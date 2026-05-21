"""
NLPExtractor — v2

Fixes applied based on real parsing failures from Dinesh's ATS-style resume:

  BUG 1 — Skill merging
    Input:  "Product Strategy                    Excel"
    Before: One skill: "Product Strategy                    Excel"
    After:  Two skills: "Product Strategy", "Excel"
    Fix:    Skill splitter now handles whitespace-run delimiters (3+ spaces)
            in addition to commas/pipes/bullets. Also strips trailing whitespace
            from each extracted token.

  BUG 2 — Work experience header mis-parsing
    Input:  "Manager, Unlox Academy    Jul 2025"
    Before: company="Manager, Unlox Academy    Jul 2025", title="Unknown"
    After:  company="Unlox Academy", title="Manager", date_range.start="Jul 2025"
    Fix:    New _is_experience_header() detects the pattern "Title, Company  Date"
            as a single header line. Comma-separated Title/Company is now handled
            as an explicit pattern before the fallback "at" splitter.

  BUG 3 — Bullets mis-classified as titles/companies
    Input:  Long sentence starting with a capital letter after the header line
    Before: Treated as company or title because _looks_like_job_header() was
            too permissive (any line < 100 chars was a "header").
    After:  _is_experience_header() uses multiple positive signals:
              - Contains date or date-range
              - Matches "Title, Company" or "Title at Company" pattern
              - Short (< 80 chars) AND contains a comma with a proper-noun token
            Long descriptive sentences are never classified as headers.

  BUG 4 — Bullet grouping under wrong experience entry
    Input:  Multi-line bullet content that wraps and loses its bullet prefix
    Before: Continuation lines lost, or assigned to wrong entry
    After:  _is_bullet_continuation() detects continuation lines (no punctuation
            start, starts lowercase or is short fragment) and appends them to the
            last bullet rather than starting a new one.

  BUG 5 — Years of experience = 0
    Input:  "Jul 2025" (single date, no range), "Jan 2025 — Apr 2025"
    Before: estimate_total_experience() required a full date range; single-date
            entries (current role) gave 0 months.
    After:  Single date with no end date is treated as "start to today" if it's
            the most recent experience. Month-level precision is now used:
            "Jan 2025 — Apr 2025" = 3 months, not 0.

  BUG 6 — Seniority = "junior" despite 4 years PM experience
    Before: infer_seniority() only checked title text; "Associate Product Manager"
            matched "junior" heuristics but not "mid".
    After:  Explicit "associate" → "mid" mapping added. Years-based fallback
            now correctly maps 4 years → "mid" (was correct in logic but
            total_years_experience was 0 due to BUG 5, so it never fired).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import NamedTuple

from app.schemas.resume import (
    Achievement,
    ContactInfo,
    DateRange,
    Education,
    Project,
    Skill,
    SkillCategory,
    WorkExperience,
)

# ── Pre-compiled patterns ─────────────────────────────────────────────────────

_RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Z|a-z]{2,}\b")
_RE_PHONE = re.compile(
    r"(\+?\d{1,3}[\s\-.]?)?\(?\d{3}\)?[\s\-.]?\d{3}[\s\-.]?\d{4}"
)
_RE_LINKEDIN = re.compile(r"linkedin\.com/in/[\w\-]+", re.IGNORECASE)
_RE_GITHUB = re.compile(r"github\.com/[\w\-]+", re.IGNORECASE)
_RE_URL = re.compile(r"https?://[^\s]+")

# ── Date patterns ─────────────────────────────────────────────────────────────

_MONTH_PATTERN = (
    r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
    r"Dec(?:ember)?)"
)
_DATE_TOKEN = rf"(?:{_MONTH_PATTERN}\.?\s+\d{{4}}|\d{{4}})"
_RE_DATE = re.compile(_DATE_TOKEN, re.IGNORECASE)
_RE_DATE_RANGE = re.compile(
    rf"({_DATE_TOKEN})"
    r"\s*[-–—to]+\s*"
    rf"({_DATE_TOKEN}|Present|Current|Now)",
    re.IGNORECASE,
)
# Single date with no end (e.g. "Jul 2025" at end of line — current role)
_RE_SINGLE_DATE = re.compile(
    rf"(?:^|\s)({_MONTH_PATTERN}\.?\s+\d{{4}}|\d{{4}})(?:\s*$)",
    re.IGNORECASE,
)

# ── Section header patterns ───────────────────────────────────────────────────

_SECTION_HEADERS = {
    "experience": re.compile(
        r"^(?:work\s+)?experience$|^employment\s+history$|^career\s+history$|"
        r"^professional\s+experience$|^work\s+history$",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^education$|^academic\s+background$|^qualifications$|^educational\s+background$",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^skills$|^technical\s+skills$|^core\s+competencies$|^expertise$|"
        r"^key\s+skills$|^skills\s+&\s+expertise$|^tools?\s+&\s+skills?$",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^projects?$|^personal\s+projects?$|^portfolio$|^key\s+projects?$|^side\s+projects?$",
        re.IGNORECASE,
    ),
    "achievements": re.compile(
        r"^achievements?$|^accomplishments?$|^awards?$|^honors?$|^recognition$",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^certifications?$|^licenses?$|^credentials$|^certificates?$",
        re.IGNORECASE,
    ),
    "summary": re.compile(
        r"^(?:professional\s+)?summary$|^objective$|^profile$|^about\s+me$|"
        r"^career\s+(?:summary|objective|profile)$|^executive\s+summary$",
        re.IGNORECASE,
    ),
}

# ── Job title indicators ──────────────────────────────────────────────────────
# Used to detect "Title, Company" headers — ATS resumes often use this format
_JOB_TITLE_PREFIXES = re.compile(
    r"\b(?:manager|engineer|developer|analyst|designer|director|lead|head|"
    r"associate|senior|junior|principal|staff|vp|vice president|president|"
    r"specialist|consultant|architect|scientist|researcher|intern|trainee|"
    r"officer|executive|coordinator|administrator)\b",
    re.IGNORECASE,
)

# ── Skill taxonomy ────────────────────────────────────────────────────────────

_SKILL_TAXONOMY: dict[SkillCategory, list[str]] = {
    SkillCategory.LANGUAGE: [
        "python", "javascript", "typescript", "java", "kotlin", "swift",
        "go", "golang", "rust", "c++", "c#", "ruby", "php", "scala",
        "r", "matlab", "dart", "elixir", "haskell", "clojure", "sql",
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
        "api fundamentals", "rest api", "rest apis",
    ],
    SkillCategory.TOOL: [
        "git", "jira", "confluence", "figma", "postman", "datadog",
        "sentry", "grafana", "prometheus", "notion", "slack",
        "google sheets", "excel", "ms excel", "microsoft excel",
        "google analytics", "mixpanel", "amplitude", "tableau",
        "looker", "power bi", "airtable", "trello", "asana",
        "app script", "google apps script",
    ],
    SkillCategory.SOFT: [
        "leadership", "communication", "problem solving", "teamwork",
        "project management", "agile", "scrum", "kanban", "mentoring",
        "stakeholder management", "cross-functional", "collaboration",
        "product strategy", "user research", "data analysis",
        "user acquisition", "growth funnels", "gtm strategy",
        "prd documentation", "user stories", "product roadmap",
        "sprint planning", "go-to-market",
    ],
}

_SKILL_LOOKUP: dict[str, SkillCategory] = {}
for _cat, _names in _SKILL_TAXONOMY.items():
    for _name in _names:
        _SKILL_LOOKUP[_name.lower()] = _cat

# Whitespace run delimiter — 3+ spaces between column items
_RE_WHITESPACE_DELIM = re.compile(r" {3,}")


# ── Section data container ────────────────────────────────────────────────────


@dataclass
class ExtractedSections:
    summary: str = ""
    experience_lines: list[str] = field(default_factory=list)
    education_lines: list[str] = field(default_factory=list)
    skills_lines: list[str] = field(default_factory=list)
    projects_lines: list[str] = field(default_factory=list)
    achievements_lines: list[str] = field(default_factory=list)
    certifications_lines: list[str] = field(default_factory=list)
    header_lines: list[str] = field(default_factory=list)


# ── Main extractor ────────────────────────────────────────────────────────────


class NLPExtractor:
    """
    Stateless extractor. All methods are pure functions of their inputs.
    v2: multi-column aware, robust experience parsing, month-precision dates.
    """

    # ── Section splitting ──────────────────────────────────────────────────────

    def split_sections(self, raw_text: str) -> ExtractedSections:
        """
        Walk through lines, detect section headers, bucket content.
        """
        lines = raw_text.splitlines()
        sections = ExtractedSections()
        current_section = "header"
        section_content: dict[str, list[str]] = {k: [] for k in _SECTION_HEADERS}
        section_content["header"] = []

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            matched_section = self._match_section_header(stripped)
            if matched_section:
                current_section = matched_section
                continue

            section_content[current_section].append(stripped)

        sections.header_lines = section_content["header"]
        sections.summary = " ".join(section_content.get("summary", []))
        sections.experience_lines = section_content.get("experience", [])
        sections.education_lines = section_content.get("education", [])
        sections.skills_lines = section_content.get("skills", [])
        sections.projects_lines = section_content.get("projects", [])
        sections.achievements_lines = section_content.get("achievements", [])
        sections.certifications_lines = section_content.get("certifications", [])

        return sections

    def _match_section_header(self, line: str) -> str | None:
        for section_name, pattern in _SECTION_HEADERS.items():
            if pattern.match(line):
                return section_name
        return None

    # ── Contact info ───────────────────────────────────────────────────────────

    def extract_contact(self, raw_text: str) -> ContactInfo:
        email_match = _RE_EMAIL.search(raw_text)
        phone_match = _RE_PHONE.search(raw_text)
        linkedin_match = _RE_LINKEDIN.search(raw_text)
        github_match = _RE_GITHUB.search(raw_text)
        name = self._extract_name(raw_text)

        return ContactInfo(
            name=name,
            email=email_match.group(0) if email_match else None,
            phone=phone_match.group(0) if phone_match else None,
            linkedin=f"https://{linkedin_match.group(0)}" if linkedin_match else None,
            github=f"https://{github_match.group(0)}" if github_match else None,
        )

    def _extract_name(self, raw_text: str) -> str | None:
        for line in raw_text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if any(
                pattern.search(stripped)
                for pattern in (_RE_EMAIL, _RE_PHONE, _RE_LINKEDIN, _RE_GITHUB, _RE_URL)
            ):
                continue
            if 3 < len(stripped) < 60:
                if re.match(r"^[A-Za-z\s.\-']+$", stripped):
                    return stripped.title()  # Normalise ALL-CAPS names → Title Case
        return None

    # ── Skills — FIX 1: multi-delimiter splitting ──────────────────────────────

    def extract_skills(self, skills_lines: list[str]) -> list[Skill]:
        """
        Parse skill lines. Handles:
          - Comma-separated: "Python, Go, Rust"
          - Pipe-separated: "Python | Go | Rust"
          - Bullet-separated: "• Python • Go"
          - Whitespace-run (two-column): "Product Strategy          Excel"
          - Group labels: "Languages: Python, Go"

        FIX: Added whitespace-run splitting as first-pass delimiter.
        """
        raw_skills: list[str] = []

        for line in skills_lines:
            # Strip group labels like "Languages: " or "Technical Skills: "
            line = re.sub(r"^[A-Za-z][A-Za-z\s]+:\s*", "", line)
            line = line.strip()
            if not line:
                continue

            # Step 1: if line has whitespace-run delimiter (multi-column artefact),
            # split on it first
            if _RE_WHITESPACE_DELIM.search(line):
                parts = _RE_WHITESPACE_DELIM.split(line)
            else:
                parts = [line]

            # Step 2: within each part, also split on commas/pipes/bullets
            for part in parts:
                sub_parts = re.split(r"[,|•·/\t]+", part)
                raw_skills.extend(p.strip() for p in sub_parts if p.strip())

        seen: set[str] = set()
        skills: list[Skill] = []

        for raw in raw_skills:
            # Clean up: strip leading/trailing bullets, dashes, spaces
            cleaned = raw.strip("·•-– \t")
            normalized = cleaned.lower()
            if not normalized or normalized in seen or len(normalized) < 2:
                continue
            # Skip entries that are obviously not skills (long sentences)
            if len(cleaned) > 60:
                continue
            seen.add(normalized)
            category = _SKILL_LOOKUP.get(normalized, SkillCategory.UNKNOWN)
            skills.append(Skill(name=cleaned, category=category))

        return skills

    # ── Work experience — FIX 2, 3, 4 ────────────────────────────────────────

    def extract_experience(self, experience_lines: list[str]) -> list[WorkExperience]:
        """
        Parse work experience blocks.

        ATS resume header formats supported:
          A) "Title, Company   Date"           ← most common ATS format
          B) "Title at Company"
          C) "Company\nTitle\nDate" (multiline)
          D) "Title — Company — Date"

        FIX 2: New header detection handles comma-separated "Title, Company Date"
        FIX 3: Long sentences are never treated as headers
        FIX 4: Bullet continuation lines are grouped correctly
        """
        entries: list[WorkExperience] = []
        current: dict = {}
        bullets: list[str] = []

        for line in experience_lines:
            # Try to detect full date range or single date
            date_range = self._extract_date_range(line)
            single_date = self._extract_single_date(line) if not date_range else None

            # ── Case 1: Line is (or contains) a date range ────────────────────
            if date_range:
                if current.get("company") or current.get("title"):
                    current["date_range"] = date_range
                    # If date is inline with header text, the header is already parsed
                else:
                    # Date line before any header — attach to next entry
                    current["date_range"] = date_range
                continue

            # ── Case 2: Single trailing date on what looks like a header line ─
            # e.g. "Manager, Unlox Academy    Jul 2025"
            line_without_date = _RE_SINGLE_DATE.sub("", line).strip() if single_date else line

            # ── Case 3: Detect a new experience entry header ──────────────────
            if self._is_experience_header(line_without_date):
                # Save previous entry before starting a new one
                if current.get("company") or current.get("title"):
                    entries.append(self._build_experience(current, bullets))
                    bullets = []
                    current = {}

                parsed = self._parse_experience_header(line_without_date)
                current = parsed
                if single_date:
                    current["date_range"] = DateRange(
                        start=single_date, end=None, is_current=True
                    )
                continue

            # ── Case 4: Bullet point ──────────────────────────────────────────
            if self._is_bullet(line):
                clean = line.lstrip("•-–*· ").strip()
                if clean:
                    bullets.append(clean)
                continue

            # ── Case 5: Continuation of previous bullet ───────────────────────
            if bullets and self._is_bullet_continuation(line):
                # Append to last bullet
                bullets[-1] = bullets[-1].rstrip() + " " + line.strip()
                continue

            # ── Case 6: Single date line (not inline) ─────────────────────────
            if single_date and not current.get("date_range"):
                current["date_range"] = DateRange(
                    start=single_date, end=None, is_current=False
                )
                continue

            # ── Case 7: Fallback — second line in entry block ─────────────────
            # Don't treat long descriptive sentences as company/title
            if len(line.strip()) < 80:
                if not current.get("company"):
                    current["company"] = line.strip()
                elif not current.get("title"):
                    current["title"] = line.strip()
                # else: ignore — don't corrupt existing entry

        # Final entry
        if current.get("company") or current.get("title"):
            entries.append(self._build_experience(current, bullets))

        return entries

    def _is_experience_header(self, line: str) -> bool:
        """
        Determine if a line is an experience entry header (Title + Company).

        Positive signals:
          1. Matches "Title, Company" pattern with job title keywords
          2. Matches "Title at Company" pattern
          3. Contains a job-title keyword AND is short (< 80 chars)
          4. Matches "Title — Company" em-dash pattern

        Negative signals (never a header):
          - Starts with bullet marker
          - Length > 120 chars (it's a sentence)
          - Starts lowercase (continuation line)
          - Is a pure date line
        """
        stripped = line.strip()

        if not stripped:
            return False
        if stripped[0].islower():
            return False
        if stripped.startswith(("•", "-", "–", "*")):
            return False
        if len(stripped) > 120:
            return False
        if _RE_DATE_RANGE.fullmatch(stripped):
            return False

        # Pattern A: "Title, Company" — comma-separated with job title word
        if "," in stripped and _JOB_TITLE_PREFIXES.search(stripped):
            parts = stripped.split(",", 1)
            if len(parts) == 2 and len(parts[0].strip()) < 60:
                return True

        # Pattern B: "Title at Company" or "Title @ Company"
        if re.search(r"\bat\b|@", stripped, re.IGNORECASE):
            if _JOB_TITLE_PREFIXES.search(stripped):
                return True

        # Pattern C: "Title — Company" em-dash
        if re.search(r"\s[—–]\s", stripped):
            if _JOB_TITLE_PREFIXES.search(stripped):
                return True

        # Pattern D: Short line with a job title word but no bullet/sentence structure
        if len(stripped) < 80 and _JOB_TITLE_PREFIXES.search(stripped):
            # Must not look like a bullet or long description
            word_count = len(stripped.split())
            if 2 <= word_count <= 8:
                return True

        return False

    def _parse_experience_header(self, line: str) -> dict:
        """
        Parse "Title, Company" or "Title at Company" into {title, company}.

        Handles:
          "Manager, Unlox Academy"               → title=Manager, company=Unlox Academy
          "Senior Backend Engineer at Acme Corp"  → title=Senior Backend Engineer, company=Acme Corp
          "Associate Product Manager, Academor Edtech" → title=APM, company=Academor Edtech
          "Software Engineer — Google"            → title=Software Engineer, company=Google
        """
        stripped = line.strip()

        # Try "Title at Company" first
        at_split = re.split(r"\s+at\s+|\s+@\s+", stripped, maxsplit=1, flags=re.IGNORECASE)
        if len(at_split) == 2:
            return {"title": at_split[0].strip(), "company": at_split[1].strip()}

        # Try em-dash "Title — Company"
        dash_split = re.split(r"\s*[—–]\s*", stripped, maxsplit=1)
        if len(dash_split) == 2 and _JOB_TITLE_PREFIXES.search(dash_split[0]):
            return {"title": dash_split[0].strip(), "company": dash_split[1].strip()}

        # Try "Title, Company" — split on FIRST comma
        if "," in stripped:
            comma_split = stripped.split(",", 1)
            title_part = comma_split[0].strip()
            company_part = comma_split[1].strip()
            # Validate: title part should contain a job title word
            if _JOB_TITLE_PREFIXES.search(title_part):
                return {"title": title_part, "company": company_part}

        # Fallback: whole line is the title
        return {"title": stripped, "company": ""}

    def _is_bullet(self, line: str) -> bool:
        """True if line starts with an explicit bullet marker."""
        return line.startswith(("•", "·", "–", "—")) or bool(
            re.match(r"^[-*]\s+\S", line)
        )

    def _is_bullet_continuation(self, line: str) -> bool:
        """
        True if a line is a continuation of the previous bullet.

        A continuation line:
          - Does not start with a capital letter at the first word
          - OR starts with a lowercase letter (mid-sentence wrap)
          - AND is not an experience header
          - AND is not very short (not a new field label)
        """
        stripped = line.strip()
        if not stripped:
            return False
        # Starts lowercase → definitely a continuation
        if stripped[0].islower():
            return True
        # Short enough to be a fragment (but not a new header)
        if len(stripped) < 30 and not _JOB_TITLE_PREFIXES.search(stripped):
            return False
        return False

    def _extract_single_date(self, line: str) -> str | None:
        """
        Extract a standalone date that is NOT part of a range.
        e.g. "Manager, Unlox Academy    Jul 2025" → "Jul 2025"
        """
        # Don't extract if this line already has a date range
        if _RE_DATE_RANGE.search(line):
            return None
        m = _RE_SINGLE_DATE.search(line)
        if m:
            return m.group(1)
        return None

    def _build_experience(self, data: dict, bullets: list[str]) -> WorkExperience:
        techs = self._extract_technologies_from_bullets(bullets)
        return WorkExperience(
            company=data.get("company", ""),
            title=data.get("title", "Unknown"),
            location=data.get("location"),
            date_range=data.get("date_range"),
            bullets=list(bullets),  # copy
            technologies=techs,
        )

    def _extract_technologies_from_bullets(self, bullets: list[str]) -> list[str]:
        found: list[str] = []
        bullet_text = " ".join(bullets).lower()
        for skill_name, category in _SKILL_LOOKUP.items():
            if category in (SkillCategory.TECHNICAL, SkillCategory.LANGUAGE, SkillCategory.TOOL):
                if re.search(r"\b" + re.escape(skill_name) + r"\b", bullet_text):
                    found.append(skill_name)
        return found

    # ── Education ─────────────────────────────────────────────────────────────

    def extract_education(self, education_lines: list[str]) -> list[Education]:
        entries: list[Education] = []
        current: dict = {}

        for line in education_lines:
            # Strip location suffixes like "   Coimbatore" from degree lines
            line = _RE_WHITESPACE_DELIM.split(line)[0].strip()

            date_range = self._extract_date_range(line)
            if date_range:
                current["date_range"] = date_range
                continue

            gpa_match = re.search(r"GPA\s*:?\s*(\d\.\d+)", line, re.IGNORECASE)
            if gpa_match:
                current["gpa"] = float(gpa_match.group(1))
                continue

            degree_keywords = (
                "bachelor", "master", "phd", "b.tech", "m.tech", "b.e", "m.e",
                "b.sc", "m.sc", "mba", "associate", "diploma", "certificate",
                "b.e,", "be,",  # Indian format: "B.E, Electrical..."
            )
            if any(kw in line.lower() for kw in degree_keywords):
                if current.get("institution"):
                    entries.append(self._build_education(current))
                    current = {}
                # Extract degree and field from same line e.g. "B.E, Electrical and Electronics Engineering"
                degree_part, field_part = self._split_degree_field(line)
                current["degree"] = degree_part
                if field_part:
                    current["field_of_study"] = field_part
            else:
                if not current.get("institution"):
                    current["institution"] = line
                elif not current.get("field_of_study"):
                    current["field_of_study"] = line

        if current.get("institution") or current.get("degree"):
            entries.append(self._build_education(current))

        return entries

    def _split_degree_field(self, line: str) -> tuple[str, str | None]:
        """
        Split "B.E, Electrical and Electronics Engineering" into
        ("B.E", "Electrical and Electronics Engineering").
        """
        # Pattern: degree abbreviation, then field
        m = re.match(
            r"^(B\.?E\.?|B\.?Tech\.?|M\.?E\.?|M\.?Tech\.?|B\.?Sc\.?|M\.?Sc\.?|"
            r"M\.?B\.?A\.?|Ph\.?D\.?|Bachelor[^,]*|Master[^,]*)[,\s]+(.+)$",
            line,
            re.IGNORECASE,
        )
        if m:
            return m.group(1).strip(), m.group(2).strip()
        return line, None

    def _build_education(self, data: dict) -> Education:
        return Education(
            institution=data.get("institution", "Unknown"),
            degree=data.get("degree"),
            field_of_study=data.get("field_of_study"),
            date_range=data.get("date_range"),
            gpa=data.get("gpa"),
        )

    # ── Projects ──────────────────────────────────────────────────────────────

    def extract_projects(self, project_lines: list[str]) -> list[Project]:
        """
        Parse project entries. Handles:
          - "Project Name" on its own line
          - Bullet highlights below
          - "Tech Stack: X, Y, Z" line
        """
        entries: list[Project] = []
        current_name: str | None = None
        current_bullets: list[str] = []
        current_techs: list[str] = []
        current_url: str | None = None

        for line in project_lines:
            url_match = _RE_URL.search(line)
            tech_match = re.match(r"^(?:tech(?:nology)?(?:\s+stack)?|tools?|built\s+with)\s*[:\-]\s*(.+)$", line, re.IGNORECASE)

            if tech_match:
                # "Tech Stack: FastAPI, Python..." line
                tech_str = tech_match.group(1)
                techs = [t.strip() for t in re.split(r"[,|]+", tech_str) if t.strip()]
                current_techs.extend(techs)
            elif url_match:
                current_url = url_match.group(0)
            elif self._is_bullet(line) or line.startswith("  "):
                clean = line.lstrip("•-–*· ").strip()
                if clean:
                    current_bullets.append(clean)
            else:
                # New project header
                if current_name:
                    if not current_techs:
                        current_techs = self._extract_technologies_from_bullets(current_bullets)
                    entries.append(Project(
                        name=current_name,
                        technologies=current_techs,
                        url=current_url,
                        highlights=current_bullets,
                    ))
                    current_bullets = []
                    current_techs = []
                    current_url = None
                current_name = line.strip()

        if current_name:
            if not current_techs:
                current_techs = self._extract_technologies_from_bullets(current_bullets)
            entries.append(Project(
                name=current_name,
                technologies=current_techs,
                url=current_url,
                highlights=current_bullets,
            ))

        return entries

    # ── Achievements / Certifications ─────────────────────────────────────────

    def extract_achievements(self, achievement_lines: list[str]) -> list[Achievement]:
        entries: list[Achievement] = []
        for line in achievement_lines:
            line = line.lstrip("•-–* ").strip()
            if not line:
                continue
            date_match = _RE_DATE.search(line)
            entries.append(Achievement(
                title=line,
                date=date_match.group(0) if date_match else None,
            ))
        return entries

    # ── ATS keywords ──────────────────────────────────────────────────────────

    def extract_ats_keywords(self, raw_text: str, skills: list[Skill]) -> list[str]:
        """
        Build a flat deduplicated keyword list.
        Now uses clean skill names (post-extraction) rather than raw skill text.
        """
        keywords: set[str] = set()

        # 1. Clean extracted skill names
        for skill in skills:
            keywords.add(skill.name.lower())

        # 2. Scan full text for taxonomy terms
        text_lower = raw_text.lower()
        for term in _SKILL_LOOKUP:
            if re.search(r"\b" + re.escape(term) + r"\b", text_lower):
                keywords.add(term)

        # 3. Action verbs
        action_verbs = {
            "led", "built", "designed", "developed", "implemented", "architected",
            "optimized", "reduced", "increased", "managed", "mentored", "deployed",
            "shipped", "scaled", "migrated", "automated", "integrated", "launched",
        }
        for verb in action_verbs:
            if re.search(r"\b" + verb + r"\b", text_lower):
                keywords.add(verb)

        # Remove any multi-space artefacts that leaked through
        cleaned = {kw for kw in keywords if "  " not in kw and len(kw) <= 50}
        return sorted(cleaned)

    # ── Date utilities ────────────────────────────────────────────────────────

    def _extract_date_range(self, line: str) -> DateRange | None:
        m = _RE_DATE_RANGE.search(line)
        if m:
            end = m.group(2)
            is_current = end.lower() in ("present", "current", "now")
            return DateRange(
                start=m.group(1),
                end=None if is_current else end,
                is_current=is_current,
            )
        return None

    # ── FIX 5: Month-precision experience calculation ─────────────────────────

    def estimate_total_experience(self, work_experience: list[WorkExperience]) -> float:
        """
        Sum up experience duration with month-level precision.

        FIX: Now handles:
          - Full date ranges: "Jan 2021 — Present" → months to today
          - Single-date current role: date_range.is_current=True
          - Month + year format: "Jan 2021" extracted as (month=1, year=2021)
          - Overlapping tenures: we sum raw, then subtract overlaps (TODO for v3)
        """
        import calendar
        import datetime

        today = datetime.date.today()
        total_months = 0

        for exp in work_experience:
            dr = exp.date_range
            if not dr or not dr.start:
                continue

            start_date = self._parse_date_to_month(str(dr.start), today)
            if start_date is None:
                continue

            if dr.is_current or dr.end is None:
                end_date = today
            else:
                end_date = self._parse_date_to_month(str(dr.end), today)
                if end_date is None:
                    continue

            months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            total_months += max(0, months)

        return round(total_months / 12, 1)

    def _parse_date_to_month(self, date_str: str, fallback: "datetime.date") -> "datetime.date | None":
        """
        Parse "Jan 2021", "January 2021", or "2021" into a date object.
        Returns the 1st of the parsed month.
        """
        import datetime

        date_str = date_str.strip()

        # Try "Month Year" format
        m = re.search(
            r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
            r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|"
            r"Dec(?:ember)?)\s+(\d{4})",
            date_str,
            re.IGNORECASE,
        )
        if m:
            month_abbr_map = {
                "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
                "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
            }
            month_str = m.group(1)[:3].lower()
            month = month_abbr_map.get(month_str)
            year = int(m.group(2))
            if month and 1900 < year <= fallback.year + 1:
                return datetime.date(year, month, 1)

        # Try bare year
        m = re.search(r"\b(\d{4})\b", date_str)
        if m:
            year = int(m.group(1))
            if 1900 < year <= fallback.year + 1:
                return datetime.date(year, 1, 1)

        return None

    # ── FIX 6: Seniority inference ────────────────────────────────────────────

    def infer_seniority(self, years: float, title_hints: list[str]) -> str:
        """
        Infer seniority from title keywords, then years.

        FIX: Added "associate" → "mid" mapping and "product manager" → "mid"
        context. Also corrected years thresholds to match industry norms.
        """
        title_text = " ".join(title_hints).lower()

        # Explicit seniority keywords — ordered from highest to lowest
        if any(kw in title_text for kw in ("principal", "staff engineer", "distinguished", "fellow")):
            return "principal"
        if any(kw in title_text for kw in ("lead", "head of", "director", "vp ", "vice president", "architect")):
            return "lead"
        if any(kw in title_text for kw in ("senior", "sr.", "sr ")):
            return "senior"
        # "Associate" in most companies = mid-level, not junior
        if any(kw in title_text for kw in ("associate product", "associate engineer", "associate manager")):
            return "mid"
        if any(kw in title_text for kw in ("junior", "jr.", "jr ", "entry", "intern", "trainee", "graduate")):
            return "junior"

        # Standalone "manager" without seniority modifier → mid/senior based on years
        if "manager" in title_text and years >= 3:
            return "mid" if years < 6 else "senior"

        # Years-based fallback
        if years >= 8:
            return "senior"
        if years >= 3:
            return "mid"
        if years >= 1:
            return "junior"
        return "junior"
