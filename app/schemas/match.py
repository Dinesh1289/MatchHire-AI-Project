"""
Match-related Pydantic schemas.

Three groups:
  1. ParsedJobDescription  — structured output of jd_parser.py
  2. MatchAnalysisRequest  — what the client sends to /matches/analyze
  3. MatchResult           — the full scored, explained output

Design note: all score fields are float 0.0–1.0 internally.
The API serialises them as 0–100 floats (via @computed_field or
a dedicated response model) so the frontend can display "87%" directly.
"""

from __future__ import annotations

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from app.schemas.resume import ParsedResume, Skill, SkillCategory


# ── Enumerations ───────────────────────────────────────────────────────────────


class SeniorityLevel(StrEnum):
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"
    UNKNOWN = "unknown"


class MatchTier(StrEnum):
    """Human-readable tier derived from match_score."""
    STRONG = "strong"        # ≥ 0.75
    GOOD = "good"            # ≥ 0.55
    PARTIAL = "partial"      # ≥ 0.35
    WEAK = "weak"            # < 0.35


class RecommendationAction(StrEnum):
    APPLY_NOW = "apply_now"
    APPLY_WITH_TAILORING = "apply_with_tailoring"
    SKILL_GAP_FIRST = "skill_gap_first"
    NOT_RECOMMENDED = "not_recommended"


# ── Parsed Job Description ─────────────────────────────────────────────────────


class RequiredSkill(BaseModel):
    """A skill extracted from a JD, tagged as required vs. nice-to-have."""
    name: str
    category: SkillCategory = SkillCategory.UNKNOWN
    is_required: bool = True          # False = "nice to have"
    years_required: float | None = None


class ParsedJobDescription(BaseModel):
    """
    Canonical structured representation of a job description.

    Produced by JDParser; consumed by MatchingEngine.
    Also returned as part of the MatchResult so the client can
    inspect what the engine saw.
    """
    model_config = ConfigDict(from_attributes=True)

    # Core fields
    title: str
    company: str | None = None
    location: str | None = None
    description_raw: str = Field(default="", exclude=True)  # Not serialised

    # Extracted structure
    required_skills: list[RequiredSkill] = Field(default_factory=list)
    preferred_skills: list[RequiredSkill] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)

    # Experience requirements
    min_years_experience: float | None = None
    max_years_experience: float | None = None
    seniority_level: SeniorityLevel = SeniorityLevel.UNKNOWN

    # Education requirements
    requires_degree: bool = False
    preferred_degree_fields: list[str] = Field(default_factory=list)

    # Responsibilities (used for keyword overlap scoring)
    responsibilities: list[str] = Field(default_factory=list)

    # Parser metadata
    parser_version: str = "1.0.0"
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @property
    def all_skills(self) -> list[RequiredSkill]:
        return self.required_skills + self.preferred_skills

    @property
    def required_skill_names(self) -> set[str]:
        return {s.name.lower() for s in self.required_skills}

    @property
    def all_skill_names(self) -> set[str]:
        return {s.name.lower() for s in self.all_skills}


# ── Score breakdown ────────────────────────────────────────────────────────────


class WeightedDimension(BaseModel):
    """One scoring dimension with its raw score, weight, and weighted contribution."""
    dimension: str
    raw_score: float = Field(ge=0.0, le=1.0)
    weight: float = Field(ge=0.0, le=1.0)
    contribution: float = Field(ge=0.0, le=1.0)
    explanation: str


class ScoreBreakdown(BaseModel):
    """
    Full weighted score breakdown.

    Weights must sum to 1.0 — validated by model_validator.
    """
    skills_match: WeightedDimension        # weight = 0.40
    experience_match: WeightedDimension    # weight = 0.30
    title_similarity: WeightedDimension    # weight = 0.15
    keyword_match: WeightedDimension       # weight = 0.10
    education_match: WeightedDimension     # weight = 0.05

    @model_validator(mode="after")
    def validate_weights_sum(self) -> "ScoreBreakdown":
        total = sum(
            d.weight for d in [
                self.skills_match,
                self.experience_match,
                self.title_similarity,
                self.keyword_match,
                self.education_match,
            ]
        )
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Dimension weights must sum to 1.0, got {total:.3f}")
        return self


# ── Skill gap analysis ─────────────────────────────────────────────────────────


class SkillGapItem(BaseModel):
    """A missing skill with actionable context."""
    name: str
    category: SkillCategory = SkillCategory.UNKNOWN
    is_required: bool = True
    priority: str  # "critical" | "important" | "nice_to_have"
    suggestion: str | None = None  # e.g. "Take Udemy Docker course"


class SkillMatchItem(BaseModel):
    """A skill the candidate has that the JD also requires."""
    name: str
    category: SkillCategory = SkillCategory.UNKNOWN
    is_required: bool = True
    candidate_years: float | None = None
    required_years: float | None = None
    years_sufficient: bool | None = None  # None = not enough info


# ── Strengths / Weaknesses ────────────────────────────────────────────────────


class StrengthItem(BaseModel):
    title: str
    detail: str


class WeaknessItem(BaseModel):
    title: str
    detail: str
    is_blocking: bool = False  # True = likely to fail screening


# ── Recommendation ────────────────────────────────────────────────────────────


class Recommendation(BaseModel):
    action: RecommendationAction
    headline: str           # One-line summary, e.g. "Strong match — apply today"
    rationale: str          # 2–3 sentence explanation
    next_steps: list[str]   # Ordered, concrete actions for the candidate


# ── Top-level Match Result ────────────────────────────────────────────────────


class MatchResult(BaseModel):
    """
    The complete output of the matching engine.

    This is what /matches/analyze returns.
    match_score is the single number (0.0–1.0) the frontend uses
    to sort/rank jobs. Everything else supports it.
    """
    model_config = ConfigDict(from_attributes=True)

    # Scores
    match_score: float = Field(ge=0.0, le=1.0, description="Weighted overall score 0–1")
    breakdown: ScoreBreakdown

    @computed_field
    @property
    def match_score_pct(self) -> float:
        """Convenience field: score as 0–100 rounded to 1 decimal place."""
        return round(self.match_score * 100, 1)

    @computed_field
    @property
    def match_tier(self) -> MatchTier:
        if self.match_score >= 0.75:
            return MatchTier.STRONG
        if self.match_score >= 0.55:
            return MatchTier.GOOD
        if self.match_score >= 0.35:
            return MatchTier.PARTIAL
        return MatchTier.WEAK

    # Skill analysis
    matched_skills: list[SkillMatchItem] = Field(default_factory=list)
    missing_skills: list[SkillGapItem] = Field(default_factory=list)
    bonus_skills: list[str] = Field(
        default_factory=list,
        description="Candidate skills not in JD but relevant — differentiators",
    )

    # Narrative analysis
    strengths: list[StrengthItem] = Field(default_factory=list)
    weaknesses: list[WeaknessItem] = Field(default_factory=list)

    # Recommendation
    recommendation: Recommendation

    # Parsed inputs (returned so client can inspect / debug)
    parsed_jd: ParsedJobDescription
    engine_version: str = "1.0.0"


# ── API request / response envelopes ─────────────────────────────────────────


class MatchAnalysisRequest(BaseModel):
    """
    POST /matches/analyze

    Client can either:
      A) Send a resume_id + jd_text   (resume already parsed in Module 1)
      B) Send a full ParsedResume + jd_text (stateless, no DB needed yet)

    Both paths work. In Module 3 (DB), we'll default to path A.
    """
    # Option A — reference a stored resume
    resume_id: UUID | None = Field(
        default=None,
        description="UUID of a previously uploaded resume. Takes precedence over parsed_resume.",
    )

    # Option B — send the parsed resume directly
    parsed_resume: ParsedResume | None = Field(
        default=None,
        description="Directly provide a ParsedResume (from /resumes/upload response).",
    )

    # Job description (always required)
    jd_text: str = Field(
        ...,
        min_length=50,
        max_length=20_000,
        description="Raw job description text. Min 50 chars.",
    )

    # Optional hints to improve parsing accuracy
    job_title_hint: str | None = Field(
        default=None,
        description="Job title if not clearly stated in jd_text.",
    )
    company_name: str | None = None

    @model_validator(mode="after")
    def require_resume_source(self) -> "MatchAnalysisRequest":
        if self.resume_id is None and self.parsed_resume is None:
            raise ValueError("Provide either resume_id or parsed_resume.")
        return self


class MatchAnalysisResponse(BaseModel):
    """Thin envelope around MatchResult for API consistency."""
    result: MatchResult
    message: str = "Analysis complete"
