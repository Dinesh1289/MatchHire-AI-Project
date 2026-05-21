"""
JDParser — Job Description Parser

Converts raw JD text into a ParsedJobDescription.

Design mirrors Module 1's NLPExtractor: rule-based, stateless, no ML
dependencies at MVP. The interface is stable so you can later slot in
an LLM-based extractor without touching any callers.

Extraction pipeline:
  1. Normalise text (whitespace, encoding artefacts)
  2. Split into labelled sections (Requirements, Responsibilities, etc.)
  3. Extract skills from requirements section + full text scan
  4. Extract experience requirements (years, seniority)
  5. Extract education requirements
  6. Extract ATS keywords
  7. Compute parser confidence
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from app.core.logging import get_logger
from app.schemas.match import ParsedJobDescription, RequiredSkill, SeniorityLevel
from app.schemas.resume import SkillCategory

logger = get_logger(__name__)

# ── Skill taxonomy (reuse the same source of truth as Module 1) ───────────────
# Imported lazily to avoid circular import; both modules share the same dict.

_SKILL_TAXONOMY: dict[SkillCategory, list[str]] = {
    SkillCategory.LANGUAGE: [
        "python", "javascript", "typescript", "java", "kotlin", "swift",
        "go", "golang", "rust", "c++", "c#", "ruby", "php", "scala",
        "r", "matlab", "dart", "elixir", "haskell",
    ],
    SkillCategory.TECHNICAL: [
        "react", "next.js", "nextjs", "vue", "angular", "svelte",
        "node.js", "nodejs", "express", "fastapi", "django", "flask",
        "spring", "rails", "graphql", "rest", "grpc", "websockets",
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
        "kafka", "rabbitmq", "celery", "docker", "kubernetes", "k8s",
        "terraform", "aws", "gcp", "azure", "ci/cd", "github actions",
        "jenkins", "linux", "nginx", "pandas", "numpy", "scikit-learn",
        "tensorflow", "pytorch", "spark", "airflow", "dbt",
        "machine learning", "deep learning", "nlp", "llm", "langchain",
        "microservices", "serverless", "lambda", "dynamodb", "s3",
        "bigquery", "snowflake", "dbt", "looker", "tableau",
    ],
    SkillCategory.TOOL: [
        "git", "jira", "confluence", "figma", "postman", "datadog",
        "sentry", "grafana", "prometheus", "notion", "slack",
        "github", "gitlab", "bitbucket", "vs code",
    ],
    SkillCategory.SOFT: [
        "communication", "leadership", "problem solving", "teamwork",
        "project management", "agile", "scrum", "kanban", "mentoring",
        "stakeholder management", "cross-functional", "collaboration",
    ],
}

_SKILL_LOOKUP: dict[str, SkillCategory] = {}
for _cat, _names in _SKILL_TAXONOMY.items():
    for _name in _names:
        _SKILL_LOOKUP[_name.lower()] = _cat

# ── Pre-compiled patterns ──────────────────────────────────────────────────────

# Years of experience: "3+ years", "2-5 years", "minimum 4 years"
_RE_YEARS_EXP = re.compile(
    r"(\d+)\+?\s*(?:to|-|–)\s*(\d+)\s+years?|"   # range: 2-5 years
    r"(\d+)\+\s*years?|"                           # minimum: 3+ years
    r"(?:minimum|at\s+least|min\.?)\s+(\d+)\s+years?|"  # "minimum 4 years"
    r"(\d+)\s+years?\s+(?:of\s+)?(?:experience|exp\.?)",  # "5 years of experience"
    re.IGNORECASE,
)

# Seniority signals in title or requirements
_SENIORITY_PATTERNS: dict[SeniorityLevel, re.Pattern] = {
    SeniorityLevel.INTERN: re.compile(r"\bintern\b|\btrainee\b|\bapprenticeship\b", re.IGNORECASE),
    SeniorityLevel.JUNIOR: re.compile(r"\bjunior\b|\bjr\.?\b|\bentry.level\b|\bgraduate\b|\bnew\s+grad\b", re.IGNORECASE),
    SeniorityLevel.MID: re.compile(r"\bmid.level\b|\bintermediate\b|\bassociate\b", re.IGNORECASE),
    SeniorityLevel.SENIOR: re.compile(r"\bsenior\b|\bsr\.?\b", re.IGNORECASE),
    SeniorityLevel.LEAD: re.compile(r"\blead\b|\bstaff\b|\bprincipal\b|\bhead\s+of\b|\bdirector\b", re.IGNORECASE),
    SeniorityLevel.PRINCIPAL: re.compile(r"\bprincipal\b|\bstaff\b|\bdistinguished\b|\bfellow\b", re.IGNORECASE),
}

# Section header patterns — maps to a canonical section key
_JD_SECTION_HEADERS: dict[str, re.Pattern] = {
    "requirements": re.compile(
        r"^(?:(?:minimum\s+)?qualifications?|requirements?|"
        r"what\s+you(?:'ll)?\s+(?:need|bring)|"
        r"skills?\s+(?:required|needed|we(?:'re)?\s+looking\s+for)|"
        r"must.have|required\s+skills?)",
        re.IGNORECASE,
    ),
    "preferred": re.compile(
        r"^(?:preferred|nice.to.have|bonus|"
        r"what\s+would\s+be\s+(?:nice|great)|"
        r"additional\s+qualifications?|"
        r"preferred\s+qualifications?)",
        re.IGNORECASE,
    ),
    "responsibilities": re.compile(
        r"^(?:responsibilities|what\s+you(?:'ll)?\s+do|"
        r"role\s+(?:overview|description)|duties|"
        r"key\s+responsibilities|about\s+the\s+role|"
        r"the\s+role|your\s+(?:role|responsibilities|impact))",
        re.IGNORECASE,
    ),
    "about": re.compile(
        r"^(?:about\s+(?:us|the\s+(?:company|role|team|position))|"
        r"company\s+overview|overview|summary|job\s+summary|position\s+summary)",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:education(?:al\s+requirements?)?|degree\s+requirements?)",
        re.IGNORECASE,
    ),
    "benefits": re.compile(
        r"^(?:benefits?|perks?|compensation|what\s+we\s+offer|we\s+offer|package)",
        re.IGNORECASE,
    ),
}

_DEGREE_KEYWORDS = re.compile(
    r"\b(?:bachelor(?:'s)?|b\.?s\.?|b\.?e\.?|b\.?tech\.?|"
    r"master(?:'s)?|m\.?s\.?|m\.?e\.?|m\.?tech\.?|mba|"
    r"ph\.?d\.?|doctorate|associate(?:'s)?|degree)\b",
    re.IGNORECASE,
)

_DEGREE_FIELD_KEYWORDS = [
    "computer science", "software engineering", "information technology",
    "electrical engineering", "mathematics", "statistics", "data science",
    "information systems", "computer engineering", "it",
]

_REQUIRED_SIGNAL = re.compile(
    r"\bmust\b|\brequired?\b|\bnecessary\b|\bmandatory\b|\bessential\b",
    re.IGNORECASE,
)
_PREFERRED_SIGNAL = re.compile(
    r"\bpreferred\b|\bbonus\b|\bnice.to.have\b|\bdesirable\b|\badvantage\b|\bplus\b",
    re.IGNORECASE,
)

# ── Section container ─────────────────────────────────────────────────────────


@dataclass
class JDSections:
    requirements_lines: list[str] = field(default_factory=list)
    preferred_lines: list[str] = field(default_factory=list)
    responsibilities_lines: list[str] = field(default_factory=list)
    education_lines: list[str] = field(default_factory=list)
    about_lines: list[str] = field(default_factory=list)
    full_lines: list[str] = field(default_factory=list)  # Unclassified lines


# ── Parser ────────────────────────────────────────────────────────────────────


class JDParser:
    """
    Stateless JD parser. One instance per application lifetime.
    All methods are pure functions of their inputs.

    Usage:
        parser = JDParser()
        parsed_jd = parser.parse(raw_jd_text, title_hint="Backend Engineer")
    """

    PARSER_VERSION = "1.0.0"

    def parse(
        self,
        raw_text: str,
        title_hint: str | None = None,
        company_name: str | None = None,
    ) -> ParsedJobDescription:
        """
        Full JD parsing pipeline. Returns a ParsedJobDescription.

        Args:
            raw_text: The raw job description text.
            title_hint: Optional job title override if not in text.
            company_name: Optional company name.
        """
        if not raw_text or not raw_text.strip():
            logger.warning("jd_parser_empty_input")
            return ParsedJobDescription(
                title=title_hint or "Unknown Position",
                company=company_name,
            )

        text = self._normalise(raw_text)
        sections = self._split_sections(text)

        title = self._extract_title(text, title_hint)
        required_skills, preferred_skills = self._extract_skills(sections)
        min_years, max_years = self._extract_experience_years(text)
        seniority = self._extract_seniority(title, text, min_years)
        requires_degree, degree_fields = self._extract_education_requirements(
            text, sections.education_lines
        )
        keywords = self._extract_keywords(text, required_skills + preferred_skills)
        responsibilities = self._extract_responsibilities(sections.responsibilities_lines)
        confidence = self._compute_confidence(
            title, required_skills, min_years, seniority
        )

        logger.info(
            f"jd_parse_complete | "
            f"title={title} | "
            f"required_skills_count={len(required_skills)} | "
            f"preferred_skills_count={len(preferred_skills)} | "
            f"min_years={min_years} | "
            f"seniority={seniority}",
            confidence=confidence,
        )

        return ParsedJobDescription(
            title=title,
            company=company_name,
            description_raw=raw_text,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            keywords=keywords,
            min_years_experience=min_years,
            max_years_experience=max_years,
            seniority_level=seniority,
            requires_degree=requires_degree,
            preferred_degree_fields=degree_fields,
            responsibilities=responsibilities,
            parser_version=self.PARSER_VERSION,
            confidence_score=confidence,
        )

    # ── Text normalisation ────────────────────────────────────────────────────

    def _normalise(self, text: str) -> str:
        """Strip encoding artefacts and normalise whitespace."""
        # Replace smart quotes, em-dashes, non-breaking spaces
        text = text.replace("\u2019", "'").replace("\u2018", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\u2013", "-").replace("\u2014", "-")
        text = text.replace("\u00a0", " ")
        # Collapse multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    # ── Section splitting ─────────────────────────────────────────────────────

    def _split_sections(self, text: str) -> JDSections:
        """
        Walk lines and bucket them into labelled sections.
        Unrecognised lines go into full_lines as a fallback pool.
        """
        sections = JDSections()
        current_section = "full"

        _section_map = {
            "requirements": sections.requirements_lines,
            "preferred": sections.preferred_lines,
            "responsibilities": sections.responsibilities_lines,
            "education": sections.education_lines,
            "about": sections.about_lines,
            "full": sections.full_lines,
        }

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue

            matched = self._match_jd_section(stripped)
            if matched:
                current_section = matched
                continue

            target_list = _section_map.get(current_section, sections.full_lines)
            target_list.append(stripped)
            # Always add to full_lines too — it's our keyword scanning pool
            if current_section != "full":
                sections.full_lines.append(stripped)

        return sections

    def _match_jd_section(self, line: str) -> str | None:
        for section_name, pattern in _JD_SECTION_HEADERS.items():
            if pattern.match(line):
                return section_name
        return None

    # ── Title extraction ──────────────────────────────────────────────────────

    def _extract_title(self, text: str, hint: str | None) -> str:
        if hint:
            return hint.strip()

        # Heuristic: first short, non-bullet line that looks like a title
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith(("•", "-", "*")):
                continue
            if 3 < len(stripped) < 80:
                # Avoid lines that are obviously sentences (contain a verb pattern)
                if not re.search(r"\b(?:we are|we're|our team|join us)\b", stripped, re.IGNORECASE):
                    return stripped

        return "Unknown Position"

    # ── Skill extraction ──────────────────────────────────────────────────────

    def _extract_skills(
        self, sections: JDSections
    ) -> tuple[list[RequiredSkill], list[RequiredSkill]]:
        """
        Two-pass skill extraction:
          Pass 1: Scan requirements section → mark as required
          Pass 2: Scan preferred section → mark as preferred
          Pass 3: Scan full text for any missed skills → classify by context
        """
        required: dict[str, RequiredSkill] = {}
        preferred: dict[str, RequiredSkill] = {}

        # Pass 1: requirements section
        for line in sections.requirements_lines:
            skills = self._skills_in_line(line)
            line_is_preferred = bool(_PREFERRED_SIGNAL.search(line))
            target = preferred if line_is_preferred else required
            for skill in skills:
                key = skill.name.lower()
                if key not in required and key not in preferred:
                    target[key] = skill

        # Pass 2: preferred section
        for line in sections.preferred_lines:
            skills = self._skills_in_line(line)
            for skill in skills:
                key = skill.name.lower()
                if key not in required and key not in preferred:
                    skill.is_required = False
                    preferred[key] = skill

        # Pass 3: full text scan for anything missed
        all_found = set(required.keys()) | set(preferred.keys())
        for line in sections.full_lines:
            skills = self._skills_in_line(line)
            for skill in skills:
                key = skill.name.lower()
                if key not in all_found:
                    # Classify by signals in the surrounding line
                    if _REQUIRED_SIGNAL.search(line):
                        required[key] = skill
                    else:
                        skill.is_required = False
                        preferred[key] = skill
                    all_found.add(key)

        return list(required.values()), list(preferred.values())

    def _skills_in_line(self, line: str) -> list[RequiredSkill]:
        """Scan a single line for skill taxonomy matches."""
        found: list[RequiredSkill] = []
        line_lower = line.lower()

        for skill_name, category in _SKILL_LOOKUP.items():
            # Word-boundary match to avoid "go" matching "good"
            if re.search(r"\b" + re.escape(skill_name) + r"\b", line_lower):
                years = self._extract_years_for_skill(line, skill_name)
                found.append(
                    RequiredSkill(
                        name=skill_name,
                        category=category,
                        is_required=True,
                        years_required=years,
                    )
                )

        return found

    def _extract_years_for_skill(self, line: str, skill_name: str) -> float | None:
        """
        Try to extract years requirement next to a skill mention.
        e.g. "3+ years Python" or "Python (2 years)"
        """
        # Look for a number within 30 chars of the skill name
        pattern = re.compile(
            r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?" + re.escape(skill_name) + r"|"
            r"\b" + re.escape(skill_name) + r"\b[^.]{0,30}?(\d+)\+?\s*(?:years?|yrs?)",
            re.IGNORECASE,
        )
        m = pattern.search(line)
        if m:
            value = m.group(1) or m.group(2)
            if value:
                return float(value)
        return None

    # ── Experience years ──────────────────────────────────────────────────────

    def _extract_experience_years(self, text: str) -> tuple[float | None, float | None]:
        """
        Return (min_years, max_years).
        If only one number found, it's the minimum.
        """
        min_years: float | None = None
        max_years: float | None = None

        for m in _RE_YEARS_EXP.finditer(text):
            groups = m.groups()
            # Group 1+2: range (e.g., 2-5)
            if groups[0] and groups[1]:
                candidate_min = float(groups[0])
                candidate_max = float(groups[1])
                if min_years is None or candidate_min < min_years:
                    min_years = candidate_min
                if max_years is None or candidate_max > max_years:
                    max_years = candidate_max
            else:
                # Single value from groups 3, 4, or 5
                value = next((float(g) for g in groups[2:] if g), None)
                if value is not None:
                    if min_years is None or value < min_years:
                        min_years = value

        return min_years, max_years

    # ── Seniority ─────────────────────────────────────────────────────────────

    def _extract_seniority(
        self,
        title: str,
        full_text: str,
        min_years: float | None,
    ) -> SeniorityLevel:
        """
        Priority: explicit title keyword > years heuristic > UNKNOWN.
        Check title first (highest signal), then full text.
        """
        for level, pattern in _SENIORITY_PATTERNS.items():
            if pattern.search(title):
                return level

        for level, pattern in _SENIORITY_PATTERNS.items():
            if pattern.search(full_text):
                return level

        # Fallback: infer from minimum years
        if min_years is not None:
            if min_years <= 1:
                return SeniorityLevel.JUNIOR
            if min_years <= 3:
                return SeniorityLevel.MID
            if min_years <= 6:
                return SeniorityLevel.SENIOR
            return SeniorityLevel.LEAD

        return SeniorityLevel.UNKNOWN

    # ── Education ─────────────────────────────────────────────────────────────

    def _extract_education_requirements(
        self, full_text: str, education_lines: list[str]
    ) -> tuple[bool, list[str]]:
        """Return (requires_degree, preferred_fields)."""
        search_text = " ".join(education_lines) or full_text
        requires_degree = bool(_DEGREE_KEYWORDS.search(search_text))

        preferred_fields: list[str] = []
        text_lower = search_text.lower()
        for field in _DEGREE_FIELD_KEYWORDS:
            if field in text_lower:
                preferred_fields.append(field)

        return requires_degree, preferred_fields

    # ── Keywords ──────────────────────────────────────────────────────────────

    def _extract_keywords(
        self, text: str, extracted_skills: list[RequiredSkill]
    ) -> list[str]:
        """
        Build an ATS keyword list by combining:
          1. All extracted skill names
          2. Domain terms found in the text
          3. Action verbs from responsibilities
        """
        keywords: set[str] = set()

        # From skills
        for skill in extracted_skills:
            keywords.add(skill.name.lower())

        # Scan full text for taxonomy terms
        text_lower = text.lower()
        for term in _SKILL_LOOKUP:
            if re.search(r"\b" + re.escape(term) + r"\b", text_lower):
                keywords.add(term)

        # Domain keywords (non-skill but important for matching)
        domain_terms = {
            "api", "rest", "backend", "frontend", "full.stack", "full stack",
            "cloud", "devops", "data pipeline", "data engineering", "analytics",
            "security", "performance", "scalability", "distributed systems",
            "system design", "oop", "functional programming", "tdd", "bdd",
            "code review", "technical leadership", "architecture",
        }
        for term in domain_terms:
            if re.search(r"\b" + re.escape(term) + r"\b", text_lower):
                keywords.add(term)

        return sorted(keywords)

    # ── Responsibilities ──────────────────────────────────────────────────────

    def _extract_responsibilities(self, lines: list[str]) -> list[str]:
        """Clean and return responsibility bullet points."""
        result: list[str] = []
        for line in lines:
            clean = line.lstrip("•-–*· ").strip()
            if clean and len(clean) > 10:
                result.append(clean)
        return result[:20]  # Cap at 20 to keep the schema lean

    # ── Confidence ────────────────────────────────────────────────────────────

    def _compute_confidence(
        self,
        title: str,
        required_skills: list[RequiredSkill],
        min_years: float | None,
        seniority: SeniorityLevel,
    ) -> float:
        score = 0.0
        if title and title != "Unknown Position":
            score += 0.2
        if required_skills:
            score += min(0.4, len(required_skills) * 0.04)
        if min_years is not None:
            score += 0.2
        if seniority != SeniorityLevel.UNKNOWN:
            score += 0.2
        return round(min(score, 1.0), 3)
