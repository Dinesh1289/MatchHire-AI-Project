"""
MatchingEngine — Resume ↔ Job Description Comparison

Implements weighted multi-dimensional scoring:

  Dimension              Weight   What it measures
  ─────────────────────  ──────   ─────────────────────────────────────────
  Skills Match           40%      Overlap of candidate skills vs JD skills
  Experience Match       30%      Years of experience vs JD requirement
  Title Similarity       15%      Semantic similarity of role titles
  Keyword Match          10%      ATS keyword coverage
  Education Match         5%      Degree/field match vs JD requirements
                          ──
                         100%

Design principles:
  - Deterministic: same inputs → same outputs, every time
  - Explainable: every score has a human-readable explanation
  - Extensible: add dimensions by registering a new _score_* method
  - Testable: all sub-scorers are pure functions
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import cached_property
from app.utils.normalization import normalize_skill
from app.core.logging import get_logger
from app.schemas.match import (
    MatchResult,
    ParsedJobDescription,
    Recommendation,
    RecommendationAction,
    RequiredSkill,
    ScoreBreakdown,
    SkillGapItem,
    SkillMatchItem,
    StrengthItem,
    WeaknessItem,
    WeightedDimension,
)
from app.schemas.resume import ParsedResume, Skill, SkillCategory

logger = get_logger(__name__)

# ── Weights — must sum to 1.0 ─────────────────────────────────────────────────
_W_SKILLS = 0.40
_W_EXPERIENCE = 0.30
_W_TITLE = 0.15
_W_KEYWORDS = 0.10
_W_EDUCATION = 0.05

# ── Seniority ordering (for range comparisons) ────────────────────────────────
_SENIORITY_ORDER = {
    "intern": 0,
    "junior": 1,
    "mid": 2,
    "senior": 3,
    "lead": 4,
    "principal": 5,
    "unknown": -1,
}

# Title word normalisation map — "sr" → "senior" etc.
_TITLE_NORMALISE = {
    r"\bsr\.?\b": "senior",
    r"\bjr\.?\b": "junior",
    r"\bdev\b": "developer",
    r"\bengineer\b": "engineer",
    r"\bmgr\b": "manager",
    r"\bswe\b": "software engineer",
}


# ── Internal scoring result container ────────────────────────────────────────


@dataclass(frozen=True)
class _SkillScoreResult:
    raw_score: float
    matched: list[SkillMatchItem]
    missing: list[SkillGapItem]
    bonus: list[str]
    explanation: str


# ── Engine ────────────────────────────────────────────────────────────────────


class MatchingEngine:
    """
    Stateless scoring engine. Safe to instantiate once per process.

    Usage:
        engine = MatchingEngine()
        result = engine.analyze(parsed_resume, parsed_jd)
    """

    ENGINE_VERSION = "1.0.0"

    def analyze(
        self,
        resume: ParsedResume,
        jd: ParsedJobDescription,
    ) -> MatchResult:
        """
        Run the full scoring pipeline.

        Returns a MatchResult with score, breakdown, skill gap,
        strengths/weaknesses, and a recommendation.
        """
        logger.info(
            f"match_analysis_start | "
            f"candidate={resume.contact.name or 'unknown'} | "
            f"jd_title={jd.title} | "
            f"resume_skills={len(resume.skills)} | "
            f"jd_required_skills={len(jd.required_skills)}",
        )

        # ── Score each dimension ──────────────────────────────────────────────
        skill_result = self._score_skills(resume, jd)
        exp_dim = self._score_experience(resume, jd)
        title_dim = self._score_title(resume, jd)
        keyword_dim = self._score_keywords(resume, jd)
        edu_dim = self._score_education(resume, jd)

        # ── Assemble weighted breakdown ───────────────────────────────────────
        skills_dim = WeightedDimension(
            dimension="skills_match",
            raw_score=skill_result.raw_score,
            weight=_W_SKILLS,
            contribution=round(skill_result.raw_score * _W_SKILLS, 4),
            explanation=skill_result.explanation,
        )

        breakdown = ScoreBreakdown(
            skills_match=skills_dim,
            experience_match=exp_dim,
            title_similarity=title_dim,
            keyword_match=keyword_dim,
            education_match=edu_dim,
        )

        # ── Final weighted score ──────────────────────────────────────────────
        match_score = round(
            sum(d.contribution for d in [
                skills_dim, exp_dim, title_dim, keyword_dim, edu_dim
            ]),
            4,
        )
        # Clamp to [0, 1] to absorb any floating-point drift
        match_score = max(0.0, min(1.0, match_score))

        # ── Narrative + recommendation ────────────────────────────────────────
        strengths = self._derive_strengths(resume, jd, breakdown, skill_result)
        weaknesses = self._derive_weaknesses(resume, jd, breakdown, skill_result)
        recommendation = self._build_recommendation(
            match_score, skill_result, weaknesses
        )

        result = MatchResult(
            match_score=match_score,
            breakdown=breakdown,
            matched_skills=skill_result.matched,
            missing_skills=skill_result.missing,
            bonus_skills=skill_result.bonus,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendation=recommendation,
            parsed_jd=jd,
            engine_version=self.ENGINE_VERSION,
        )

        logger.info(
            f"match_analysis_complete | "
            f"candidate={resume.contact.name or 'unknown'} | "
            f"jd_title={jd.title} | "
            f"match_score={match_score} | "
            f"match_tier={result.match_tier} | "
            f"matched_skills={len(skill_result.matched)} | "
            f"missing_skills={len(skill_result.missing)}",
        )

        return result

    # ══════════════════════════════════════════════════════════════════════════
    # Dimension 1: Skills Match (40%)
    # ══════════════════════════════════════════════════════════════════════════

    def _score_skills(
        self, resume: ParsedResume, jd: ParsedJobDescription
    ) -> _SkillScoreResult:
        """
        Scoring logic:
          - Required skills carry full weight
          - Preferred skills carry half weight
          - Missing a required skill has a larger penalty than missing a preferred one

        Formula:
          required_score  = matched_required / total_required         (if total > 0)
          preferred_score = matched_preferred / total_preferred        (if total > 0)
          raw = 0.75 * required_score + 0.25 * preferred_score
        """
        resume_skill_names = self._candidate_skill_set(resume)

        required_skills = jd.required_skills
        preferred_skills = jd.preferred_skills

        matched: list[SkillMatchItem] = []
        missing: list[SkillGapItem] = []
        bonus: list[str] = []

        # ── Required skills ───────────────────────────────────────────────────
        matched_required = 0
        for jd_skill in required_skills:
            key = normalize_skill(jd_skill.name)
            candidate_skill = self._find_candidate_skill(resume, key)
            if self._skill_matches(key, resume_skill_names):
                matched_required += 1
                years_ok = self._years_sufficient(candidate_skill, jd_skill)
                matched.append(SkillMatchItem(
                    name=jd_skill.name,
                    category=jd_skill.category,
                    is_required=True,
                    candidate_years=candidate_skill.years_of_experience if candidate_skill else None,
                    required_years=jd_skill.years_required,
                    years_sufficient=years_ok,
                ))
            else:
                priority = self._skill_priority(jd_skill, is_required=True)
                missing.append(SkillGapItem(
                    name=jd_skill.name,
                    category=jd_skill.category,
                    is_required=True,
                    priority=priority,
                    suggestion=self._skill_suggestion(jd_skill.name),
                ))

        # ── Preferred skills ──────────────────────────────────────────────────
        matched_preferred = 0
        for jd_skill in preferred_skills:
            key = normalize_skill(jd_skill.name)
            if self._skill_matches(key, resume_skill_names):
                matched_preferred += 1
                candidate_skill = self._find_candidate_skill(resume, key)
                matched.append(SkillMatchItem(
                    name=jd_skill.name,
                    category=jd_skill.category,
                    is_required=False,
                    candidate_years=candidate_skill.years_of_experience if candidate_skill else None,
                    required_years=jd_skill.years_required,
                    years_sufficient=None,
                ))
            else:
                missing.append(SkillGapItem(
                    name=jd_skill.name,
                    category=jd_skill.category,
                    is_required=False,
                    priority="nice_to_have",
                    suggestion=None,
                ))

        # ── Bonus skills (candidate has; JD doesn't mention) ─────────────────
        jd_all = jd.all_skill_names
        for skill in resume.skills:
            if normalize_skill(skill.name) not in jd_all and skill.category in (
                SkillCategory.LANGUAGE, SkillCategory.TECHNICAL
            ):
                bonus.append(skill.name)

        # ── Compute score ─────────────────────────────────────────────────────
        req_score = (matched_required / len(required_skills)) if required_skills else 1.0
        pref_score = (matched_preferred / len(preferred_skills)) if preferred_skills else 1.0

        # If no required skills in JD, rely entirely on preferred
        if not required_skills:
            raw_score = pref_score
        elif not preferred_skills:
            raw_score = req_score
        else:
            raw_score = 0.75 * req_score + 0.25 * pref_score

        raw_score = round(raw_score, 4)

        # ── Build explanation ─────────────────────────────────────────────────
        total_req = len(required_skills)
        total_pref = len(preferred_skills)
        explanation = (
            f"Matched {matched_required}/{total_req} required skills "
            f"and {matched_preferred}/{total_pref} preferred skills."
        )
        if bonus:
            explanation += f" Has {len(bonus)} bonus skills not listed in JD."

        return _SkillScoreResult(
            raw_score=raw_score,
            matched=matched,
            missing=missing,
            bonus=bonus[:10],  # Cap bonus list
            explanation=explanation,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # Dimension 2: Experience Match (30%)
    # ══════════════════════════════════════════════════════════════════════════

    def _score_experience(
        self, resume: ParsedResume, jd: ParsedJobDescription
    ) -> WeightedDimension:
        """
        Scoring logic:
          - No JD requirement → full score (we can't penalise what isn't stated)
          - Candidate meets or exceeds minimum → full score
          - Below minimum → linear decay to 0 at 0 years
          - Seniority level comparison adds a ±0.1 bonus/penalty

        Penalty cap: a candidate with 0 years gets 0.0 even if JD says 0+ required.
        """
        candidate_years = resume.total_years_experience or 0.0
        jd_min = jd.min_years_experience
        jd_max = jd.max_years_experience

        if jd_min is None:
            # No requirement stated — don't penalise
            raw_score = 0.85  # Small discount vs 1.0 because we can't verify fit
            explanation = (
                f"No minimum experience requirement stated. "
                f"Candidate has {candidate_years:.1f} years."
            )
        elif candidate_years >= jd_min:
            raw_score = 1.0
            years_over = candidate_years - jd_min
            if jd_max and candidate_years > jd_max * 1.5:
                # Possibly overqualified — slight reduction
                raw_score = 0.85
                explanation = (
                    f"Candidate has {candidate_years:.1f} years — may be overqualified "
                    f"(JD asks for {jd_min}–{jd_max} years)."
                )
            else:
                explanation = (
                    f"Meets experience requirement: {candidate_years:.1f} years "
                    f"vs {jd_min:.0f}+ required."
                )
        else:
            # Partial credit: linear from 0 to jd_min
            raw_score = round(candidate_years / jd_min, 4) if jd_min > 0 else 0.0
            gap = jd_min - candidate_years
            explanation = (
                f"Below requirement: {candidate_years:.1f} years vs "
                f"{jd_min:.0f} required. Gap: {gap:.1f} years."
            )

        # ── Seniority adjustment ──────────────────────────────────────────────
        seniority_adj, seniority_note = self._seniority_adjustment(resume, jd)
        raw_score = max(0.0, min(1.0, raw_score + seniority_adj))
        if seniority_note:
            explanation += f" {seniority_note}"

        raw_score = round(raw_score, 4)
        return WeightedDimension(
            dimension="experience_match",
            raw_score=raw_score,
            weight=_W_EXPERIENCE,
            contribution=round(raw_score * _W_EXPERIENCE, 4),
            explanation=explanation,
        )

    def _seniority_adjustment(
        self, resume: ParsedResume, jd: ParsedJobDescription
    ) -> tuple[float, str]:
        """Return (adjustment, note). Adjustment is in [-0.1, +0.1]."""
        candidate_level = (resume.seniority_level or "unknown").lower()
        jd_level = jd.seniority_level.value.lower()

        c_rank = _SENIORITY_ORDER.get(candidate_level, -1)
        j_rank = _SENIORITY_ORDER.get(jd_level, -1)

        if c_rank == -1 or j_rank == -1:
            return 0.0, ""

        diff = c_rank - j_rank
        if diff == 0:
            return 0.05, f"Seniority level matches ({jd_level})."
        if diff == 1:
            return 0.0, f"One level above JD seniority ({candidate_level} vs {jd_level})."
        if diff > 1:
            return -0.05, f"Possibly overqualified ({candidate_level} vs {jd_level} role)."
        if diff == -1:
            return -0.05, f"One level below JD seniority ({candidate_level} vs {jd_level})."
        return -0.1, f"Seniority gap: {candidate_level} applying for {jd_level} role."

    # ══════════════════════════════════════════════════════════════════════════
    # Dimension 3: Title Similarity (15%)
    # ══════════════════════════════════════════════════════════════════════════

    def _score_title(
        self, resume: ParsedResume, jd: ParsedJobDescription
    ) -> WeightedDimension:
        """
        Token-overlap similarity between most recent job title and JD title.
        Uses a bag-of-words Jaccard similarity on normalised tokens.
        No ML required — sufficient for MVP.
        """
        # Get candidate's most recent title
        candidate_title = ""
        if resume.work_experience:
            candidate_title = resume.work_experience[0].title

        jd_title = jd.title

        if not candidate_title or not jd_title:
            raw_score = 0.5  # Neutral — can't assess
            explanation = "Could not compare titles (missing data)."
        else:
            c_tokens = self._title_tokens(candidate_title)
            j_tokens = self._title_tokens(jd_title)

            if not c_tokens or not j_tokens:
                raw_score = 0.5
                explanation = "Title tokens too sparse to compare."
            else:
                intersection = c_tokens & j_tokens
                union = c_tokens | j_tokens
                jaccard = len(intersection) / len(union)

                # Boost for direct substring match (e.g. "engineer" in both)
                if c_tokens & j_tokens:
                    boost = min(0.2, len(intersection) * 0.1)
                else:
                    boost = 0.0

                raw_score = min(1.0, round(jaccard + boost, 4))
                explanation = (
                    f"Title overlap: '{candidate_title}' vs '{jd_title}'. "
                    f"Shared tokens: {sorted(intersection) or 'none'}."
                )

        return WeightedDimension(
            dimension="title_similarity",
            raw_score=raw_score,
            weight=_W_TITLE,
            contribution=round(raw_score * _W_TITLE, 4),
            explanation=explanation,
        )

    def _title_tokens(self, title: str) -> set[str]:
        """Normalise and tokenise a job title."""
        normalised = title.lower()
        for pattern, replacement in _TITLE_NORMALISE.items():
            normalised = re.sub(pattern, replacement, normalised)
        # Remove stopwords
        stopwords = {"and", "or", "the", "a", "an", "of", "for", "in", "at", "to", "with"}
        tokens = set(re.findall(r"[a-z]+", normalised)) - stopwords
        return tokens

    # ══════════════════════════════════════════════════════════════════════════
    # Dimension 4: Keyword Match (10%)
    # ══════════════════════════════════════════════════════════════════════════

    def _score_keywords(
        self, resume: ParsedResume, jd: ParsedJobDescription
    ) -> WeightedDimension:
        """
        Overlap of resume ATS keywords vs JD keywords.
        Simple set intersection — captures domain term coverage.
        """
        if not jd.keywords:
            raw_score = 0.7  # Neutral if JD has no extractable keywords
            explanation = "No JD keywords extracted — neutral score applied."
        else:
            resume_kws = {normalize_skill(k) for k in resume.ats_keywords}
            jd_kws = {normalize_skill(k) for k in jd.keywords}
            matched_kws = resume_kws & jd_kws
            raw_score = round(len(matched_kws) / len(jd_kws), 4)
            explanation = (
                f"Matched {len(matched_kws)}/{len(jd_kws)} JD keywords. "
                f"Examples: {sorted(matched_kws)[:5] or 'none'}."
            )

        return WeightedDimension(
            dimension="keyword_match",
            raw_score=raw_score,
            weight=_W_KEYWORDS,
            contribution=round(raw_score * _W_KEYWORDS, 4),
            explanation=explanation,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # Dimension 5: Education Match (5%)
    # ══════════════════════════════════════════════════════════════════════════

    def _score_education(
        self, resume: ParsedResume, jd: ParsedJobDescription
    ) -> WeightedDimension:
        """
        Binary + partial scoring:
          - JD doesn't require a degree → 1.0
          - JD requires degree AND candidate has one → 1.0
          - JD requires degree, candidate has one in a preferred field → 1.0 + implicit boost
          - JD requires degree, candidate has no education listed → 0.5 (uncertain)
        """
        if not jd.requires_degree:
            raw_score = 1.0
            explanation = "No degree requirement specified."
        elif not resume.education:
            raw_score = 0.5
            explanation = "Degree required but no education listed on resume."
        else:
            has_degree = any(
                edu.degree and any(
                    kw in edu.degree.lower()
                    for kw in ("bachelor", "master", "phd", "b.s", "m.s", "b.e", "m.e", "b.tech")
                )
                for edu in resume.education
            )

            if has_degree:
                # Check field match
                if jd.preferred_degree_fields:
                    fields_matched = any(
                        any(
                            field in (edu.field_of_study or "").lower()
                            or field in (edu.institution or "").lower()
                            for field in jd.preferred_degree_fields
                        )
                        for edu in resume.education
                    )
                    raw_score = 1.0 if fields_matched else 0.85
                    explanation = (
                        "Degree matches requirement"
                        + (f" and preferred field ({jd.preferred_degree_fields[0]})." if fields_matched else " but field not specified.")
                    )
                else:
                    raw_score = 1.0
                    explanation = "Has a degree — meets requirement."
            else:
                raw_score = 0.4
                explanation = "Degree required but no qualifying degree found on resume."

        return WeightedDimension(
            dimension="education_match",
            raw_score=raw_score,
            weight=_W_EDUCATION,
            contribution=round(raw_score * _W_EDUCATION, 4),
            explanation=explanation,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # Narrative: Strengths
    # ══════════════════════════════════════════════════════════════════════════

    def _derive_strengths(
        self,
        resume: ParsedResume,
        jd: ParsedJobDescription,
        breakdown: ScoreBreakdown,
        skill_result: _SkillScoreResult,
    ) -> list[StrengthItem]:
        strengths: list[StrengthItem] = []

        # Strong skills coverage
        if breakdown.skills_match.raw_score >= 0.75:
            matched_names = [s.name for s in skill_result.matched if s.is_required]
            strengths.append(StrengthItem(
                title="Strong Skills Coverage",
                detail=(
                    f"Covers {len(matched_names)} of the required skills including "
                    f"{', '.join(matched_names[:4])}."
                ),
            ))

        # Experience depth
        if breakdown.experience_match.raw_score >= 0.9:
            years = resume.total_years_experience or 0
            strengths.append(StrengthItem(
                title="Meets Experience Requirement",
                detail=(
                    f"{years:.0f} years of experience aligns well with this role's requirements."
                ),
            ))

        # Title alignment
        if breakdown.title_similarity.raw_score >= 0.6:
            strengths.append(StrengthItem(
                title="Relevant Role Background",
                detail=(
                    f"Previous role as '{resume.work_experience[0].title if resume.work_experience else 'N/A'}' "
                    f"is relevant to '{jd.title}'."
                ),
            ))

        # Bonus skills as differentiator
        if skill_result.bonus:
            strengths.append(StrengthItem(
                title="Additional Differentiators",
                detail=(
                    f"Has extra skills that could add value: "
                    f"{', '.join(skill_result.bonus[:4])}."
                ),
            ))

        # Keyword coverage
        if breakdown.keyword_match.raw_score >= 0.7:
            strengths.append(StrengthItem(
                title="Good ATS Keyword Coverage",
                detail="Resume covers most of the key terms recruiters and ATS systems scan for.",
            ))

        return strengths

    # ══════════════════════════════════════════════════════════════════════════
    # Narrative: Weaknesses
    # ══════════════════════════════════════════════════════════════════════════

    def _derive_weaknesses(
        self,
        resume: ParsedResume,
        jd: ParsedJobDescription,
        breakdown: ScoreBreakdown,
        skill_result: _SkillScoreResult,
    ) -> list[WeaknessItem]:
        weaknesses: list[WeaknessItem] = []

        # Critical missing skills
        critical_missing = [
            s for s in skill_result.missing
            if s.is_required and s.priority == "critical"
        ]
        if critical_missing:
            names = ", ".join(s.name for s in critical_missing[:4])
            weaknesses.append(WeaknessItem(
                title="Missing Critical Required Skills",
                detail=f"These required skills are absent: {names}.",
                is_blocking=True,
            ))

        # Experience gap
        if breakdown.experience_match.raw_score < 0.6:
            candidate_years = resume.total_years_experience or 0
            jd_min = jd.min_years_experience or 0
            weaknesses.append(WeaknessItem(
                title="Experience Gap",
                detail=(
                    f"Role requires {jd_min:.0f}+ years; "
                    f"candidate has {candidate_years:.1f} years."
                ),
                is_blocking=jd_min - candidate_years > 2,
            ))

        # Low keyword coverage
        if breakdown.keyword_match.raw_score < 0.4:
            weaknesses.append(WeaknessItem(
                title="Low ATS Keyword Coverage",
                detail=(
                    "Resume may not pass ATS screening. "
                    "Consider adding more JD-specific terms."
                ),
                is_blocking=False,
            ))

        # Education gap
        if breakdown.education_match.raw_score < 0.5:
            weaknesses.append(WeaknessItem(
                title="Education Requirement Gap",
                detail=(
                    "The role requires a degree that isn't clearly listed on your resume."
                ),
                is_blocking=False,
            ))

        # Title mismatch
        if breakdown.title_similarity.raw_score < 0.3:
            weaknesses.append(WeaknessItem(
                title="Title Mismatch",
                detail=(
                    f"Your recent title doesn't closely match '{jd.title}'. "
                    "Tailor your resume headline."
                ),
                is_blocking=False,
            ))

        return weaknesses

    # ══════════════════════════════════════════════════════════════════════════
    # Recommendation
    # ══════════════════════════════════════════════════════════════════════════

    def _build_recommendation(
        self,
        match_score: float,
        skill_result: _SkillScoreResult,
        weaknesses: list[WeaknessItem],
    ) -> Recommendation:
        blocking_weaknesses = [w for w in weaknesses if w.is_blocking]
        missing_required_count = sum(1 for s in skill_result.missing if s.is_required)
        missing_required_names = [s.name for s in skill_result.missing if s.is_required]

        if match_score >= 0.75 and not blocking_weaknesses:
            action = RecommendationAction.APPLY_NOW
            headline = "Strong match — apply with confidence"
            rationale = (
                f"Your profile aligns well with this role (score: {round(match_score*100)}%). "
                "Your skills and experience are a solid fit. "
                "Customise your cover letter to highlight your most relevant experience."
            )
            next_steps = [
                "Tailor your resume summary to mirror the job title.",
                "Write a cover letter referencing your top 3 matched skills.",
                "Apply directly and follow up in 5–7 business days.",
            ]

        elif match_score >= 0.55:
            action = RecommendationAction.APPLY_WITH_TAILORING
            headline = "Good match — apply after tailoring your resume"
            rationale = (
                f"You meet most of the requirements (score: {round(match_score*100)}%). "
                "A few gaps exist but are not disqualifying. "
                "Tailoring your resume to highlight relevant experience will improve your chances."
            )
            next_steps = [
                f"Highlight experience with: {', '.join(missing_required_names[:3])} if applicable.",
                "Update your resume summary to echo the job title and key terms.",
                "Quantify achievements in bullet points (e.g. 'reduced latency by 40%').",
                "Apply and prepare to address gaps in the interview.",
            ]

        elif match_score >= 0.35:
            action = RecommendationAction.SKILL_GAP_FIRST
            headline = "Partial match — close key skill gaps before applying"
            critical_skills = [s.name for s in skill_result.missing if s.priority == "critical"][:3]
            rationale = (
                f"You match some requirements (score: {round(match_score*100)}%), "
                f"but {missing_required_count} required skills are missing. "
                "Consider upskilling before applying to maximise your success rate."
            )
            next_steps = [
                f"Learn or demonstrate: {', '.join(critical_skills)}." if critical_skills
                else "Work on the missing required skills listed above.",
                "Add any related projects to your portfolio.",
                "Consider applying for mid-level roles to build the missing experience.",
                "Set a 30–60 day learning goal before reapplying.",
            ]

        else:
            action = RecommendationAction.NOT_RECOMMENDED
            headline = "Low match — significant gaps exist"
            rationale = (
                f"This role is a weak fit at this time (score: {round(match_score*100)}%). "
                "Multiple required skills and experience levels are not met. "
                "We recommend building experience in adjacent roles first."
            )
            next_steps = [
                "Focus on roles that better match your current skill set.",
                f"Build experience with: {', '.join(missing_required_names[:3])}." if missing_required_names else "Build broader technical experience.",
                "Revisit this type of role after 6–12 months of targeted growth.",
            ]

        return Recommendation(
            action=action,
            headline=headline,
            rationale=rationale,
            next_steps=next_steps,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # Utilities
    # ══════════════════════════════════════════════════════════════════════════

    def _candidate_skill_set(self, resume: ParsedResume) -> set[str]:
        """
        Build a flat set of normalized skill names from the resume.
        Also includes technology names found in work experience bullets.
        """

        skill_names: set[str] = set()

        # Resume skills
        for skill in resume.skills:
            skill_names.add(
                normalize_skill(skill.name)
            )

        # Work experience technologies
        for exp in resume.work_experience:
            for tech in exp.technologies:
                skill_names.add(
                    normalize_skill(tech)
                )

        # Project technologies
        for project in resume.projects:
            for tech in project.technologies:
                skill_names.add(
                    normalize_skill(tech)
                )

        return skill_names

    def _skill_matches(self, jd_skill_key: str, candidate_skills: set[str]) -> bool:
        normalized_jd_skill = normalize_skill(jd_skill_key)

        return normalized_jd_skill in {
            normalize_skill(skill)
            for skill in candidate_skills
        }

    def _find_candidate_skill(
        self, resume: ParsedResume, skill_key: str
    ) -> Skill | None:
        """Find the Skill object from the resume by normalised name."""
        normalized_key = normalize_skill(skill_key)

        for skill in resume.skills:
            if normalize_skill(skill.name) == normalized_key:
                return skill

        return None

    def _years_sufficient(
        self, candidate_skill: Skill | None, jd_skill: RequiredSkill
    ) -> bool | None:
        """
        Returns True/False if both years are known; None if we can't assess.
        """
        if jd_skill.years_required is None:
            return None
        if candidate_skill is None or candidate_skill.years_of_experience is None:
            return None
        return candidate_skill.years_of_experience >= jd_skill.years_required

    def _skill_priority(self, skill: RequiredSkill, is_required: bool) -> str:
        if not is_required:
            return "nice_to_have"
        # Technical/Language skills in required section are critical
        if skill.category in (SkillCategory.LANGUAGE, SkillCategory.TECHNICAL):
            return "critical"
        if skill.category == SkillCategory.TOOL:
            return "important"
        return "important"

    def _skill_suggestion(self, skill_name: str) -> str | None:
        """Lightweight static suggestions for common skills."""
        _SUGGESTIONS: dict[str, str] = {
            "docker": "Take Docker's official 'Getting Started' tutorial (free).",
            "kubernetes": "Complete the CKAD certification path on KodeKloud.",
            "aws": "Pursue AWS Cloud Practitioner certification.",
            "terraform": "Work through HashiCorp's official Terraform tutorials.",
            "python": "Build 2–3 Python projects and add them to GitHub.",
            "typescript": "Convert an existing JavaScript project to TypeScript.",
            "react": "Build a portfolio project using React + Tailwind.",
            "postgresql": "Complete SQLZoo or Mode Analytics SQL tutorials.",
            "redis": "Add caching to a side project using Redis.",
            "kafka": "Complete Confluent's free Kafka fundamentals course.",
            "spark": "Complete Databricks' free Spark course.",
        }
        return _SUGGESTIONS.get(skill_name.lower())
