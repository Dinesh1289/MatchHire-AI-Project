"""
ResumeParsingService

Orchestrates the full resume ingestion pipeline:
  1. Receive validated file bytes
  2. Select the correct parser (PDF or DOCX)
  3. Run the parser
  4. Post-process and enrich the result
  5. Return ParsedResume

This is the only class callers (route handlers, Celery tasks) should touch.
The parser implementations are an internal detail.

Future extension points (without changing this interface):
  - Add AI-based extraction fallback when confidence_score < threshold
  - Add Affinda API as a parallel enrichment pass
  - Add caching so the same file hash doesn't get re-parsed
"""

from __future__ import annotations

import hashlib
from functools import cached_property

from app.core.config import get_settings
from app.core.exceptions import ParseError
from app.core.logging import get_logger
from app.schemas.resume import ParsedResume
from app.services.file_validator import ValidatedFile
from app.parsers.base import BaseResumeParser
from app.parsers.docx_parser import DOCXResumeParser
from app.parsers.pdf_parser import PDFResumeParser

logger = get_logger(__name__)

_LOW_CONFIDENCE_THRESHOLD = 0.4


class ResumeParsingService:
    """
    Stateless service. Safe to use as a FastAPI dependency (singleton).
    All state lives in the ValidatedFile passed to parse().
    """

    @cached_property
    def _parsers(self) -> dict[str, BaseResumeParser]:
        """Lazy-instantiate parsers once per process lifetime."""
        return {
            ".pdf": PDFResumeParser(),
            ".docx": DOCXResumeParser(),
        }

    def parse(self, validated_file: ValidatedFile) -> ParsedResume:
        """
        Main entry point.

        Args:
            validated_file: Output of FileValidationService.validate().

        Returns:
            ParsedResume: Fully populated structured resume.

        Raises:
            ParseError: If no parser is available or parsing fails.
        """
        parser = self._select_parser(validated_file.extension)
        file_hash = self._compute_hash(validated_file.content)

        logger.info(
                f"resume_parse_start | "
    f"filename={validated_file.filename} | "
    f"extension={validated_file.extension} | "
    f"size_bytes={validated_file.size_bytes} | "
    f"file_hash={file_hash}"
        )

        try:
            result = parser.parse(validated_file.content)
        except ParseError:
            raise
        except Exception as exc:
            logger.error(
                    f"resume_parse_unexpected_error | "
    f"filename={validated_file.filename} | "
    f"error={str(exc)}",
    exc_info=True,
            )
            raise ParseError(
                f"Parsing failed for '{validated_file.filename}'.",
                detail=str(exc),
            ) from exc

        self._log_result_quality(result, validated_file.filename)
        self._warn_low_confidence(result, validated_file.filename)

        logger.info(
            f"resume_parse_complete | "
    f"filename={validated_file.filename} | "
    f"confidence={result.confidence_score} | "
    f"skills_count={len(result.skills)} | "
    f"experience_count={len(result.work_experience)} | "
    f"education_count={len(result.education)} | "
    f"keywords_count={len(result.ats_keywords)}"
        )

        return result

    # ── Internal ──────────────────────────────────────────────────────────────

    def _select_parser(self, extension: str) -> BaseResumeParser:
        parser = self._parsers.get(extension)
        if not parser:
            raise ParseError(
                f"No parser registered for extension '{extension}'.",
                detail=f"Supported: {list(self._parsers.keys())}",
            )
        return parser

    @staticmethod
    def _compute_hash(content: bytes) -> str:
        """SHA-256 of raw file bytes. Used for dedup in future caching layer."""
        return hashlib.sha256(content).hexdigest()

    def _warn_low_confidence(self, result: ParsedResume, filename: str) -> None:
        if result.confidence_score < _LOW_CONFIDENCE_THRESHOLD:
            logger.warning(
                f"resume_low_confidence | "
                f"filename={filename} | "
                f"confidence={result.confidence_score} | "
                f"hint=Consider triggering AI-based extraction fallback.",
            )

    def _log_result_quality(self, result: ParsedResume, filename: str) -> None:
        missing: list[str] = []
        if not result.contact.email:
            missing.append("email")
        if not result.contact.name:
            missing.append("name")
        if not result.skills:
            missing.append("skills")
        if not result.work_experience:
            missing.append("work_experience")
        if not result.education:
            missing.append("education")

        if missing:
            logger.warning(
                f"resume_missing_sections | "
                f"filename={filename} | "
                f"missing={missing}",
            )
