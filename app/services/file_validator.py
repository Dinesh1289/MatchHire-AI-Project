"""
FileValidationService

Single responsibility: validate an uploaded file before any parsing occurs.
Checks magic bytes (not just extension/MIME), file size, and basic integrity.

This runs synchronously and cheaply — before we touch any parsing libraries.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.exceptions import (
    CorruptedFileError,
    EmptyFileError,
    FileTooLargeError,
    UnsupportedFileTypeError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

# Magic bytes: the only reliable way to determine file type.
_PDF_MAGIC = b"%PDF"
_DOCX_MAGIC = b"PK\x03\x04"  # ZIP-based; we validate further below


@dataclass(frozen=True)
class ValidatedFile:
    """Value object returned after successful validation."""

    filename: str
    extension: str          # ".pdf" or ".docx"
    mime_type: str
    content: bytes
    size_bytes: int


class FileValidationService:
    """
    Stateless validator. Construct once, call validate() per request.

    Dependency-injected into the route handler via FastAPI Depends().
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    async def validate(self, upload: UploadFile) -> ValidatedFile:
        """
        Full validation pipeline. Raises AppError subclasses on any failure.

        Order matters:
          1. Read content (so we can inspect magic bytes)
          2. Size check
          3. Extension check
          4. Magic-byte check
          5. Integrity check (document-level)
        """
        content = await upload.read()

        self._check_not_empty(content, upload.filename)
        self._check_size(content, upload.filename)

        extension = self._extract_extension(upload.filename)
        self._check_extension(extension, upload.filename)

        mime_type = self._detect_mime_type(content, extension, upload.filename)
        self._check_integrity(content, extension, upload.filename)

        logger.info(
                f"file_validated | "
    f"filename={upload.filename} | "
    f"size_bytes={len(content)} | "
    f"mime_type={mime_type}"
        )

        return ValidatedFile(
            filename=upload.filename or "resume",
            extension=extension,
            mime_type=mime_type,
            content=content,
            size_bytes=len(content),
        )

    # ── Private helpers ────────────────────────────────────────────────────────

    def _check_not_empty(self, content: bytes, filename: str | None) -> None:
        if not content:
            raise EmptyFileError(
                f"Uploaded file '{filename}' is empty.",
                detail="File must contain data.",
            )

    def _check_size(self, content: bytes, filename: str | None) -> None:
        max_bytes = self._settings.MAX_UPLOAD_SIZE_BYTES
        if len(content) > max_bytes:
            raise FileTooLargeError(
                f"File exceeds the {max_bytes // (1024*1024)} MB limit.",
                detail=f"Received {len(content)} bytes; max is {max_bytes} bytes.",
            )

    def _extract_extension(self, filename: str | None) -> str:
        if not filename:
            raise UnsupportedFileTypeError(
                "File has no name — cannot determine type.",
            )
        ext = Path(filename).suffix.lower()
        if not ext:
            raise UnsupportedFileTypeError(
                f"File '{filename}' has no extension.",
                detail=f"Supported: {sorted(self._settings.ALLOWED_EXTENSIONS)}",
            )
        return ext

    def _check_extension(self, extension: str, filename: str | None) -> None:
        if extension not in self._settings.ALLOWED_EXTENSIONS:
            raise UnsupportedFileTypeError(
                f"Extension '{extension}' is not supported.",
                detail=f"Supported extensions: {sorted(self._settings.ALLOWED_EXTENSIONS)}",
            )

    def _detect_mime_type(
        self, content: bytes, extension: str, filename: str | None
    ) -> str:
        """
        Detect MIME type from magic bytes — not from the Content-Type header,
        which clients can spoof trivially.
        """
        if extension == ".pdf":
            if not content.startswith(_PDF_MAGIC):
                raise UnsupportedFileTypeError(
                    f"'{filename}' does not appear to be a valid PDF.",
                    detail="PDF files must start with %PDF magic bytes.",
                )
            return "application/pdf"

        if extension == ".docx":
            if not content.startswith(_DOCX_MAGIC):
                raise UnsupportedFileTypeError(
                    f"'{filename}' does not appear to be a valid DOCX file.",
                    detail="DOCX files must be valid ZIP archives.",
                )
            return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        # Should never reach here given _check_extension passes first
        raise UnsupportedFileTypeError(f"Unrecognised extension: {extension}")

    def _check_integrity(
        self, content: bytes, extension: str, filename: str | None
    ) -> None:
        """
        Lightweight integrity probe: try to open the document without
        fully parsing it. Catches truncated/corrupted uploads early.
        """
        if extension == ".pdf":
            self._probe_pdf(content, filename)
        elif extension == ".docx":
            self._probe_docx(content, filename)

    @staticmethod
    def _probe_pdf(content: bytes, filename: str | None) -> None:
        try:
            import fitz  # PyMuPDF

            doc = fitz.open(stream=content, filetype="pdf")
            if doc.page_count == 0:
                raise CorruptedFileError(
                    f"PDF '{filename}' contains zero pages.",
                )
            doc.close()
        except CorruptedFileError:
            raise
        except Exception as exc:
            raise CorruptedFileError(
                f"PDF '{filename}' could not be opened.",
                detail=str(exc),
            ) from exc

    @staticmethod
    def _probe_docx(content: bytes, filename: str | None) -> None:
        try:
            import zipfile

            with zipfile.ZipFile(io.BytesIO(content)) as zf:
                names = zf.namelist()
            # A valid DOCX must contain word/document.xml
            if not any("word/document.xml" in n for n in names):
                raise CorruptedFileError(
                    f"'{filename}' is a ZIP archive but not a valid DOCX.",
                    detail="Missing word/document.xml.",
                )
        except CorruptedFileError:
            raise
        except Exception as exc:
            raise CorruptedFileError(
                f"DOCX '{filename}' could not be opened.",
                detail=str(exc),
            ) from exc
