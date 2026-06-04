"""
Resume-related Pydantic schemas.

Separate input validation from output serialisation.
All schemas use model_config = ConfigDict(from_attributes=True)
so they can be constructed from ORM objects directly.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


# ── Sub-schemas (building blocks) ─────────────────────────────────────────────


class DateRange(BaseModel):
    start: date | str | None = None
    end: date | str | None = None  # None means "present"
    is_current: bool = False


class WorkExperience(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    company: str
    title: str
    location: str | None = None
    date_range: DateRange | None = None
    description: str | None = None
    bullets: list[str] = Field(default_factory=list)
    technologies: list[str] = Field(default_factory=list)

    @field_validator("bullets", "technologies", mode="before")
    @classmethod
    def coerce_none_to_list(cls, v):
        return v or []


class Education(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    date_range: DateRange | None = None
    gpa: float | None = None
    honors: list[str] = Field(default_factory=list)


class Project(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    url: str | None = None
    highlights: list[str] = Field(default_factory=list)


class Achievement(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    description: str | None = None
    date: date | str | None = None
    issuer: str | None = None


class ContactInfo(BaseModel):
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    linkedin: str | None = None
    github: str | None = None
    portfolio: str | None = None
    location: str | None = None


# ── Skill classification ───────────────────────────────────────────────────────


class SkillCategory(StrEnum):
    TECHNICAL = "technical"
    SOFT = "soft"
    DOMAIN = "domain"
    TOOL = "tool"
    LANGUAGE = "language"
    CERTIFICATION = "certification"
    UNKNOWN = "unknown"


class Skill(BaseModel):
    name: str
    category: SkillCategory = SkillCategory.UNKNOWN
    years_of_experience: float | None = None
    proficiency: str | None = None  # beginner | intermediate | advanced | expert


# ── Top-level parsed resume ────────────────────────────────────────────────────


class ParsedResume(BaseModel):
    """
    The canonical representation of a parsed resume.

    This schema is the contract between the parsing layer and everything
    downstream (AI scoring, storage, API responses).
    """

    model_config = ConfigDict(from_attributes=True)

    # Identity
    contact: ContactInfo = Field(default_factory=ContactInfo)

    # Core sections
    summary: str | None = None
    skills: list[Skill] = Field(default_factory=list)
    work_experience: list[WorkExperience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    achievements: list[Achievement] = Field(default_factory=list)
    certifications: list[Achievement] = Field(default_factory=list)

    # ATS / search metadata
    ats_keywords: list[str] = Field(
        default_factory=list,
        description="Flat keyword list optimised for ATS matching",
    )
    total_years_experience: float | None = None
    seniority_level: str | None = None  # junior | mid | senior | lead | principal

    # Parsing provenance
    raw_text_length: int = 0
    parser_version: str = "1.0.0"
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Parser confidence 0–1; used to decide if re-parse is worthwhile",
    )


# ── API request / response envelopes ──────────────────────────────────────────


class ResumeUploadResponse(BaseModel):
    """Returned immediately after a successful upload + parse."""

    resume_id: UUID
    file_name: str
    file_size_bytes: int
    mime_type: str
    parsed: ParsedResume
    message: str = "Resume parsed successfully"


class ResumeStatusEnum(StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
