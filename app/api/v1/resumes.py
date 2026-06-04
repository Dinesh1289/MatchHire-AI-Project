"""
Resume API routes — /api/v1/resumes
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.core.logging import get_logger
from app.schemas.resume import ResumeUploadResponse
from app.services.file_validator import FileValidationService, ValidatedFile
from app.services.resume_parsing_service import ResumeParsingService

logger = get_logger(__name__)
router = APIRouter()

# ── Dependency providers ──────────────────────────────────────────────────────


def get_file_validator() -> FileValidationService:
    return FileValidationService()


def get_parsing_service() -> ResumeParsingService:
    return ResumeParsingService()


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post(
    "/upload",
    response_model=ResumeUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload and parse a resume",
    description=(
        "Accepts a PDF or DOCX resume file. "
        "Validates the file, extracts structured data, and returns a parsed resume object. "
        "Max file size: 5 MB."
    ),
    responses={
        201: {"description": "Resume parsed successfully"},
        413: {"description": "File too large"},
        415: {"description": "Unsupported file type"},
        422: {"description": "File is corrupted or unparseable"},
    },
)
async def upload_resume(
    file: UploadFile = File(
        ...,
        description="Resume file. Supported formats: PDF, DOCX. Max size: 5 MB.",
    ),
    validator: FileValidationService = Depends(get_file_validator),
    parser: ResumeParsingService = Depends(get_parsing_service),
    # TODO: uncomment when auth middleware is wired up
    # current_user: User = Depends(get_current_user),
) -> ResumeUploadResponse:
    """
    Resume upload + parse pipeline.

    Steps:
      1. Validate file (type, size, integrity)
      2. Parse to structured JSON
      3. Return parsed result

    Note: Persistence to DB is handled by the next module (Resume CRUD).
    This endpoint focuses on parsing only, keeping responsibilities clean.
    """
    # Step 1: Validate
    validated: ValidatedFile = await validator.validate(file)

    logger.info(
            f"resume_upload_received | "
    f"filename={validated.filename} | "
    f"size_bytes={validated.size_bytes} | "
    f"mime_type={validated.mime_type}"
        # user_id=str(current_user.id),  # re-enable with auth
    )

    # Step 2: Parse
    parsed_resume = parser.parse(validated)

    # Step 3: Respond
    # In Module 2 (DB + storage), we'll persist here and return a resume_id
    # from the database record. For now, generate a transient ID.
    resume_id = uuid4()

    logger.info(
        f"resume_upload_complete | "
    f"resume_id={resume_id} | "
    f"confidence={parsed_resume.confidence_score} | "
    f"skills_count={len(parsed_resume.skills)}"
    )

    return ResumeUploadResponse(
        resume_id=resume_id,
        file_name=validated.filename,
        file_size_bytes=validated.size_bytes,
        mime_type=validated.mime_type,
        parsed=parsed_resume,
    )
