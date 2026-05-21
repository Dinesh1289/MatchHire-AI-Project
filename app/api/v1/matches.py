"""
Match API routes — /api/v1/matches
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.exceptions import NotFoundError, ParseError
from app.core.logging import get_logger
from app.schemas.match import MatchAnalysisRequest, MatchAnalysisResponse
from app.services.jd_parser import JDParser
from app.services.matching_engine import MatchingEngine

logger = get_logger(__name__)
router = APIRouter(prefix="/matches", tags=["matches"])


# ── Dependency providers ──────────────────────────────────────────────────────

def get_jd_parser() -> JDParser:
    return JDParser()


def get_matching_engine() -> MatchingEngine:
    return MatchingEngine()


# ── Routes ────────────────────────────────────────────────────────────────────


@router.post(
    "/analyze",
    response_model=MatchAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze resume–job match",
    description=(
        "Parses a raw job description, compares it against a parsed resume, "
        "and returns a weighted fit score with full breakdown, skill gap analysis, "
        "and an actionable recommendation.\n\n"
        "Provide **either** `resume_id` (for a stored resume) "
        "**or** `parsed_resume` (from the `/resumes/upload` response). "
        "In this MVP, `parsed_resume` is the primary path — "
        "`resume_id` will be wired to the DB in Module 3."
    ),
    responses={
        200: {"description": "Analysis complete"},
        400: {"description": "Invalid request (bad resume_id or missing resume)"},
        422: {"description": "JD text could not be parsed"},
    },
)
async def analyze_match(
    request: MatchAnalysisRequest,
    jd_parser: JDParser = Depends(get_jd_parser),
    engine: MatchingEngine = Depends(get_matching_engine),
    # TODO: current_user: User = Depends(get_current_user),
) -> MatchAnalysisResponse:
    """
    Resume ↔ Job Description match analysis pipeline:

      1. Resolve the resume (from request body for now; DB lookup in Module 3)
      2. Parse the raw JD text into structured ParsedJobDescription
      3. Run MatchingEngine.analyze()
      4. Return MatchResult
    """

    # ── Step 1: Resolve resume ────────────────────────────────────────────────
    if request.resume_id is not None:
        # TODO (Module 3): look up resume from DB
        # resume = await resume_repo.get(request.resume_id, user_id=current_user.id)
        # For now, raise a clear not-implemented error
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "error": "DB_LOOKUP_NOT_IMPLEMENTED",
                "message": (
                    "resume_id lookup is not yet wired to the database (Module 3). "
                    "Please send parsed_resume directly from the /resumes/upload response."
                ),
            },
        )

    resume = request.parsed_resume  # Guaranteed non-None by schema validator

    logger.info(
        f"match_analyze_request | "
        f"candidate={resume.contact.name or 'unknown'} | "
        f"jd_text_length={len(request.jd_text)} | "
        f"title_hint={request.job_title_hint}",
    )

    # ── Step 2: Parse JD ──────────────────────────────────────────────────────
    try:
        parsed_jd = jd_parser.parse(
            raw_text=request.jd_text,
            title_hint=request.job_title_hint,
            company_name=request.company_name,
        )
    except Exception as exc:
        logger.error("jd_parse_failed", error=str(exc), exc_info=True)
        raise ParseError(
            "Failed to parse the job description.",
            detail=str(exc),
        ) from exc

    # ── Step 3: Run engine ────────────────────────────────────────────────────
    result = engine.analyze(resume, parsed_jd)

    logger.info(
        f"match_analyze_complete | "
        f"candidate={resume.contact.name or 'unknown'} | "
        f"jd_title={parsed_jd.title} | "
        f"match_score={result.match_score} | "
        f"match_tier={result.match_tier}",
    )

    return MatchAnalysisResponse(result=result)
