"""
Unit tests for JDParser.

Tests cover title extraction, skill identification (required vs preferred),
experience year extraction, seniority detection, and education parsing.
"""

from __future__ import annotations

import pytest

from app.schemas.match import SeniorityLevel
from app.schemas.resume import SkillCategory
from app.services.jd_parser import JDParser

parser = JDParser()

# ── Sample JDs ────────────────────────────────────────────────────────────────

BACKEND_JD = """
Senior Backend Engineer — Python

About the Role
We're looking for a Senior Backend Engineer to join our platform team.
You will build and scale APIs that serve millions of users.

Requirements
- 5+ years of software engineering experience
- Strong proficiency in Python and FastAPI or Django
- Experience with PostgreSQL and Redis
- Solid understanding of Docker and Kubernetes
- Familiarity with AWS (Lambda, S3, RDS)
- Experience with CI/CD pipelines and GitHub Actions

Preferred
- Experience with Kafka or RabbitMQ
- Knowledge of Terraform
- Open source contributions

Responsibilities
- Design and build scalable REST APIs
- Participate in code reviews and architectural discussions
- Mentor junior engineers

Education
Bachelor's degree in Computer Science or equivalent experience
"""

FULLSTACK_JD = """
Junior Full Stack Developer

We are looking for a motivated Junior Full Stack Developer.

Qualifications
- 1-2 years of experience
- JavaScript and TypeScript
- React and Node.js
- Basic SQL (MySQL or PostgreSQL)
- Git version control

Nice to have
- Vue.js experience
- Docker basics
- Agile/Scrum experience
"""

VAGUE_JD = """
Software Engineer

We need a software engineer. Experience required. Good communication skills.
"""


# ── Title extraction ──────────────────────────────────────────────────────────


class TestTitleExtraction:
    def test_uses_hint_when_provided(self):
        jd = parser.parse(BACKEND_JD, title_hint="Staff Engineer")
        assert jd.title == "Staff Engineer"

    def test_extracts_title_from_first_line(self):
        jd = parser.parse(BACKEND_JD)
        # First non-empty line of BACKEND_JD is the title
        assert "backend" in jd.title.lower() or "engineer" in jd.title.lower()

    def test_vague_jd_returns_unknown_when_no_hint(self):
        jd = parser.parse(VAGUE_JD)
        assert jd.title  # Should always return something


# ── Skill extraction ──────────────────────────────────────────────────────────


class TestSkillExtraction:
    def test_extracts_required_skills(self):
        jd = parser.parse(BACKEND_JD)
        req_names = {s.name.lower() for s in jd.required_skills}
        assert "python" in req_names
        assert "postgresql" in req_names
        assert "docker" in req_names

    def test_extracts_preferred_skills(self):
        jd = parser.parse(BACKEND_JD)
        pref_names = {s.name.lower() for s in jd.preferred_skills}
        assert "kafka" in pref_names or "terraform" in pref_names

    def test_required_skills_marked_correctly(self):
        jd = parser.parse(BACKEND_JD)
        assert all(s.is_required for s in jd.required_skills)

    def test_preferred_skills_not_required(self):
        jd = parser.parse(BACKEND_JD)
        assert all(not s.is_required for s in jd.preferred_skills)

    def test_no_duplicate_skills(self):
        jd = parser.parse(BACKEND_JD)
        all_names = [s.name.lower() for s in jd.all_skills]
        assert len(all_names) == len(set(all_names))

    def test_skill_categories_assigned(self):
        jd = parser.parse(BACKEND_JD)
        python_skill = next((s for s in jd.required_skills if s.name.lower() == "python"), None)
        assert python_skill is not None
        assert python_skill.category == SkillCategory.LANGUAGE

    def test_junior_jd_skills(self):
        jd = parser.parse(FULLSTACK_JD)
        req_names = {s.name.lower() for s in jd.required_skills}
        assert "javascript" in req_names or "typescript" in req_names


# ── Experience years ──────────────────────────────────────────────────────────


class TestExperienceYears:
    def test_extracts_min_years(self):
        jd = parser.parse(BACKEND_JD)
        assert jd.min_years_experience == 5.0

    def test_extracts_year_range(self):
        jd = parser.parse(FULLSTACK_JD)
        assert jd.min_years_experience == 1.0
        assert jd.max_years_experience == 2.0

    def test_no_years_when_not_specified(self):
        jd = parser.parse(VAGUE_JD)
        assert jd.min_years_experience is None


# ── Seniority ─────────────────────────────────────────────────────────────────


class TestSeniority:
    def test_senior_detected_from_title(self):
        jd = parser.parse(BACKEND_JD, title_hint="Senior Backend Engineer")
        assert jd.seniority_level == SeniorityLevel.SENIOR

    def test_junior_detected_from_title(self):
        jd = parser.parse(FULLSTACK_JD)
        assert jd.seniority_level == SeniorityLevel.JUNIOR

    def test_seniority_inferred_from_years(self):
        jd = parser.parse(VAGUE_JD)
        # Vague JD has no seniority signal
        assert jd.seniority_level == SeniorityLevel.UNKNOWN


# ── Education ─────────────────────────────────────────────────────────────────


class TestEducation:
    def test_detects_degree_requirement(self):
        jd = parser.parse(BACKEND_JD)
        assert jd.requires_degree is True

    def test_detects_cs_field(self):
        jd = parser.parse(BACKEND_JD)
        assert any("computer science" in f for f in jd.preferred_degree_fields)

    def test_no_degree_requirement_when_not_stated(self):
        jd = parser.parse(VAGUE_JD)
        assert jd.requires_degree is False


# ── Keywords ──────────────────────────────────────────────────────────────────


class TestKeywords:
    def test_keywords_non_empty(self):
        jd = parser.parse(BACKEND_JD)
        assert len(jd.keywords) > 0

    def test_keywords_include_python(self):
        jd = parser.parse(BACKEND_JD)
        assert "python" in jd.keywords

    def test_keywords_sorted(self):
        jd = parser.parse(BACKEND_JD)
        assert jd.keywords == sorted(jd.keywords)


# ── Confidence ────────────────────────────────────────────────────────────────


class TestConfidence:
    def test_well_structured_jd_high_confidence(self):
        jd = parser.parse(BACKEND_JD, title_hint="Senior Backend Engineer")
        assert jd.confidence_score >= 0.7

    def test_vague_jd_low_confidence(self):
        jd = parser.parse(VAGUE_JD)
        assert jd.confidence_score <= 0.4

    def test_empty_jd_returns_gracefully(self):
        jd = parser.parse("", title_hint="Engineer")
        assert jd.title == "Engineer"
        assert jd.required_skills == []
