"""
Unit tests for MatchingEngine.

Tests verify each scoring dimension independently, then the full pipeline.
We use fixture factories to build minimal ParsedResume + ParsedJobDescription
objects rather than parsing real documents — keeping tests fast and deterministic.
"""

from __future__ import annotations

import pytest

from app.schemas.match import (
    MatchTier,
    ParsedJobDescription,
    RecommendationAction,
    RequiredSkill,
    SeniorityLevel,
)
from app.schemas.resume import (
    ContactInfo,
    Education,
    ParsedResume,
    Skill,
    SkillCategory,
    WorkExperience,
)
from app.services.matching_engine import MatchingEngine

engine = MatchingEngine()


# ── Fixture factories ─────────────────────────────────────────────────────────

def _make_resume(
    skills: list[str] | None = None,
    years: float = 5.0,
    seniority: str = "senior",
    title: str = "Senior Backend Engineer",
    has_degree: bool = True,
    ats_keywords: list[str] | None = None,
) -> ParsedResume:
    skill_objs = [
        Skill(name=s, category=SkillCategory.TECHNICAL)
        for s in (skills or [])
    ]
    edu = (
        [Education(institution="MIT", degree="Bachelor's in Computer Science")]
        if has_degree
        else []
    )
    return ParsedResume(
        contact=ContactInfo(name="Jane Smith", email="jane@example.com"),
        skills=skill_objs,
        work_experience=[
            WorkExperience(
                company="Acme Corp",
                title=title,
                technologies=skills or [],
            )
        ] if title else [],
        education=edu,
        total_years_experience=years,
        seniority_level=seniority,
        ats_keywords=ats_keywords or (skills or []),
    )


def _make_jd(
    title: str = "Senior Backend Engineer",
    required_skills: list[str] | None = None,
    preferred_skills: list[str] | None = None,
    min_years: float | None = 5.0,
    seniority: SeniorityLevel = SeniorityLevel.SENIOR,
    requires_degree: bool = False,
    keywords: list[str] | None = None,
) -> ParsedJobDescription:
    req = [
        RequiredSkill(name=s, category=SkillCategory.TECHNICAL, is_required=True)
        for s in (required_skills or [])
    ]
    pref = [
        RequiredSkill(name=s, category=SkillCategory.TECHNICAL, is_required=False)
        for s in (preferred_skills or [])
    ]
    return ParsedJobDescription(
        title=title,
        required_skills=req,
        preferred_skills=pref,
        min_years_experience=min_years,
        seniority_level=seniority,
        requires_degree=requires_degree,
        keywords=keywords or (required_skills or []),
    )


# ── Full pipeline smoke test ──────────────────────────────────────────────────


class TestFullPipeline:
    def test_returns_match_result(self):
        resume = _make_resume(skills=["python", "fastapi", "postgresql", "docker"])
        jd = _make_jd(required_skills=["python", "fastapi", "postgresql", "docker"])
        result = engine.analyze(resume, jd)
        assert result is not None
        assert 0.0 <= result.match_score <= 1.0

    def test_perfect_match_scores_high(self):
        skills = ["python", "fastapi", "postgresql", "docker", "redis"]
        resume = _make_resume(skills=skills, years=6.0, seniority="senior")
        jd = _make_jd(
            required_skills=skills,
            min_years=5.0,
            seniority=SeniorityLevel.SENIOR,
        )
        result = engine.analyze(resume, jd)
        assert result.match_score >= 0.75
        assert result.match_tier == MatchTier.STRONG

    def test_zero_skills_scores_low(self):
        resume = _make_resume(skills=[], years=0.0, seniority="junior")
        jd = _make_jd(required_skills=["python", "kubernetes", "aws", "terraform"])
        result = engine.analyze(resume, jd)
        assert result.match_score < 0.5

    def test_weights_sum_to_one(self):
        resume = _make_resume(skills=["python"])
        jd = _make_jd(required_skills=["python"])
        result = engine.analyze(resume, jd)
        b = result.breakdown
        total_weight = sum([
            b.skills_match.weight,
            b.experience_match.weight,
            b.title_similarity.weight,
            b.keyword_match.weight,
            b.education_match.weight,
        ])
        assert abs(total_weight - 1.0) < 0.001

    def test_contributions_sum_to_match_score(self):
        resume = _make_resume(skills=["python", "fastapi"])
        jd = _make_jd(required_skills=["python", "fastapi", "docker"])
        result = engine.analyze(resume, jd)
        b = result.breakdown
        total_contribution = sum([
            b.skills_match.contribution,
            b.experience_match.contribution,
            b.title_similarity.contribution,
            b.keyword_match.contribution,
            b.education_match.contribution,
        ])
        assert abs(total_contribution - result.match_score) < 0.01


# ── Skills dimension ──────────────────────────────────────────────────────────


class TestSkillsScoring:
    def test_full_required_skill_match(self):
        skills = ["python", "fastapi", "postgresql"]
        resume = _make_resume(skills=skills)
        jd = _make_jd(required_skills=skills)
        result = engine.analyze(resume, jd)
        assert result.breakdown.skills_match.raw_score == 1.0

    def test_no_skill_match(self):
        resume = _make_resume(skills=["cobol", "fortran"])
        jd = _make_jd(required_skills=["python", "kubernetes", "aws"])
        result = engine.analyze(resume, jd)
        assert result.breakdown.skills_match.raw_score == 0.0

    def test_partial_skill_match(self):
        resume = _make_resume(skills=["python", "docker"])
        jd = _make_jd(required_skills=["python", "docker", "kubernetes", "terraform"])
        result = engine.analyze(resume, jd)
        score = result.breakdown.skills_match.raw_score
        assert 0.0 < score < 1.0

    def test_matched_skills_populated(self):
        resume = _make_resume(skills=["python", "fastapi"])
        jd = _make_jd(required_skills=["python", "fastapi", "docker"])
        result = engine.analyze(resume, jd)
        matched_names = {s.name.lower() for s in result.matched_skills}
        assert "python" in matched_names
        assert "fastapi" in matched_names

    def test_missing_skills_populated(self):
        resume = _make_resume(skills=["python"])
        jd = _make_jd(required_skills=["python", "kubernetes"])
        result = engine.analyze(resume, jd)
        missing_names = {s.name.lower() for s in result.missing_skills}
        assert "kubernetes" in missing_names

    def test_missing_required_skills_are_critical(self):
        resume = _make_resume(skills=[])
        jd = _make_jd(required_skills=["python"])
        result = engine.analyze(resume, jd)
        assert result.missing_skills[0].priority == "critical"

    def test_no_jd_skills_gives_full_score(self):
        resume = _make_resume(skills=["python"])
        jd = _make_jd(required_skills=[])
        result = engine.analyze(resume, jd)
        # No skills in JD → can't penalise
        assert result.breakdown.skills_match.raw_score == 1.0

    def test_alias_matching_nodejs(self):
        """node.js in JD should match nodejs in resume."""
        resume = _make_resume(skills=["nodejs"])
        jd = _make_jd(required_skills=["node.js"])
        result = engine.analyze(resume, jd)
        assert result.breakdown.skills_match.raw_score > 0.0


# ── Experience dimension ──────────────────────────────────────────────────────


class TestExperienceScoring:
    def test_meets_requirement(self):
        resume = _make_resume(years=6.0)
        jd = _make_jd(min_years=5.0)
        result = engine.analyze(resume, jd)
        assert result.breakdown.experience_match.raw_score >= 0.9

    def test_below_requirement_partial_credit(self):
        resume = _make_resume(years=2.0)
        jd = _make_jd(min_years=5.0)
        result = engine.analyze(resume, jd)
        score = result.breakdown.experience_match.raw_score
        assert 0.0 < score < 0.9

    def test_zero_years_against_five_year_requirement(self):
        resume = _make_resume(years=0.0)
        jd = _make_jd(min_years=5.0)
        result = engine.analyze(resume, jd)
        assert result.breakdown.experience_match.raw_score == 0.0

    def test_no_jd_requirement_gives_reasonable_score(self):
        resume = _make_resume(years=3.0)
        jd = _make_jd(min_years=None)
        result = engine.analyze(resume, jd)
        assert result.breakdown.experience_match.raw_score >= 0.8


# ── Title dimension ───────────────────────────────────────────────────────────


class TestTitleScoring:
    def test_identical_titles_score_high(self):
        resume = _make_resume(title="Senior Backend Engineer")
        jd = _make_jd(title="Senior Backend Engineer")
        result = engine.analyze(resume, jd)
        assert result.breakdown.title_similarity.raw_score >= 0.7

    def test_completely_different_titles_score_low(self):
        resume = _make_resume(title="Graphic Designer")
        jd = _make_jd(title="Senior Backend Engineer")
        result = engine.analyze(resume, jd)
        assert result.breakdown.title_similarity.raw_score < 0.5

    def test_partial_title_overlap(self):
        resume = _make_resume(title="Backend Engineer")
        jd = _make_jd(title="Senior Backend Engineer")
        result = engine.analyze(resume, jd)
        score = result.breakdown.title_similarity.raw_score
        assert score > 0.4


# ── Recommendation ────────────────────────────────────────────────────────────


class TestRecommendation:
    def test_strong_match_apply_now(self):
        skills = ["python", "fastapi", "postgresql", "docker", "redis"]
        resume = _make_resume(skills=skills, years=6.0, seniority="senior")
        jd = _make_jd(required_skills=skills, min_years=5.0)
        result = engine.analyze(resume, jd)
        if result.match_score >= 0.75:
            assert result.recommendation.action == RecommendationAction.APPLY_NOW

    def test_weak_match_not_recommended(self):
        resume = _make_resume(skills=[], years=0.0)
        jd = _make_jd(required_skills=["python", "kubernetes", "aws", "terraform", "kafka"])
        result = engine.analyze(resume, jd)
        if result.match_score < 0.35:
            assert result.recommendation.action == RecommendationAction.NOT_RECOMMENDED

    def test_recommendation_has_next_steps(self):
        resume = _make_resume(skills=["python"])
        jd = _make_jd(required_skills=["python", "kubernetes"])
        result = engine.analyze(resume, jd)
        assert len(result.recommendation.next_steps) >= 1

    def test_recommendation_headline_not_empty(self):
        resume = _make_resume(skills=["python", "fastapi"])
        jd = _make_jd(required_skills=["python", "fastapi"])
        result = engine.analyze(resume, jd)
        assert result.recommendation.headline


# ── Match tiers ───────────────────────────────────────────────────────────────


class TestMatchTiers:
    def test_strong_tier(self):
        skills = ["python", "fastapi", "postgresql", "docker"]
        resume = _make_resume(skills=skills, years=6.0)
        jd = _make_jd(required_skills=skills, min_years=4.0)
        result = engine.analyze(resume, jd)
        assert result.match_tier in (MatchTier.STRONG, MatchTier.GOOD)

    def test_weak_tier(self):
        resume = _make_resume(skills=[], years=0.0)
        jd = _make_jd(required_skills=["python", "golang", "kubernetes"])
        result = engine.analyze(resume, jd)
        assert result.match_tier in (MatchTier.WEAK, MatchTier.PARTIAL)

    def test_match_score_pct_is_0_to_100(self):
        resume = _make_resume(skills=["python"])
        jd = _make_jd(required_skills=["python"])
        result = engine.analyze(resume, jd)
        assert 0.0 <= result.match_score_pct <= 100.0
