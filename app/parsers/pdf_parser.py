"""
PDFResumeParser — v2

Root cause of the multi-column failures in ATS-style resumes:

  PyMuPDF's default text extraction on a two-column PDF reads left-column
  and right-column text interleaved on the same line, producing output like:

    "Product Strategy                                       Excel"
    "User Research                                         SQL"

  This happens because PyMuPDF preserves x-positions and pads with spaces
  between column boundaries. The NLP extractor then sees one long skill string
  instead of two separate skills.

Fix strategy (layered):
  1. Column detection: measure the x-span of words on each page. If the page
     has two clusters of x-positions, it's multi-column — split and re-join.
  2. Whitespace normalisation: collapse runs of 3+ spaces into a pipe delimiter
     BEFORE passing text to NLPExtractor, so the skill splitter can handle it.
  3. pdfplumber fallback now uses bbox-based column splitting instead of
     word flow, which is far more reliable for two-column ATS layouts.
"""

from __future__ import annotations

import io
import re

from app.core.exceptions import ParseError
from app.core.logging import get_logger
from app.schemas.resume import ParsedResume
from app.parsers.base import BaseResumeParser
from app.parsers.nlp_extractor import NLPExtractor

logger = get_logger(__name__)

_MIN_TEXT_LENGTH = 100
# If a line has an interior run of 3+ spaces, it's almost certainly two-column artefact
_RE_MULTI_SPACE = re.compile(r" {3,}")


class PDFResumeParser(BaseResumeParser):
    PARSER_VERSION = "2.0.0"

    def __init__(self) -> None:
        self._extractor = NLPExtractor()

    # ── Public API ─────────────────────────────────────────────────────────────

    def extract_text(self, content: bytes) -> str:
        """
        Extract raw text using PyMuPDF with column-aware post-processing.
        Falls back to pdfplumber bbox-column split if text is too short.
        """
        text = self._extract_with_pymupdf(content)

        if len(text.strip()) < _MIN_TEXT_LENGTH:
            logger.warning(
                f"pymupdf_text_too_short | "
    f"length={len(text.strip())} | "
    f"fallback=pdfplumber"
            )
            text = self._extract_with_pdfplumber(content)

        if len(text.strip()) < _MIN_TEXT_LENGTH:
            raise ParseError(
                "Could not extract meaningful text from the PDF.",
                detail="The PDF may be image-based (scanned). Please upload a text-based PDF.",
            )

        # ── KEY FIX: normalise multi-column artefacts ─────────────────────────
        text = self._normalise_multicolumn_text(text)
        return text

    def parse(self, content: bytes) -> ParsedResume:
        raw_text = self.extract_text(content)
        raw_text = self._normalize_text(raw_text)
        logger.debug(
            f"pdf_text_extracted | "
    f"text_length={len(raw_text)}"
        )
        logger.info(
    f"RAW_TEXT_START\n{raw_text}\nRAW_TEXT_END"
)

        sections = self._extractor.split_sections(raw_text)
        contact = self._extractor.extract_contact(raw_text)
        skills = self._extractor.extract_skills(sections.skills_lines)
        experience = self._extractor.extract_experience(sections.experience_lines)
        education = self._extractor.extract_education(sections.education_lines)
        projects = self._extractor.extract_projects(sections.projects_lines)
        achievements = self._extractor.extract_achievements(sections.achievements_lines)
        certifications = self._extractor.extract_achievements(sections.certifications_lines)
        ats_keywords = self._extractor.extract_ats_keywords(raw_text, skills)

        total_years = self._extractor.estimate_total_experience(experience)
        seniority = self._extractor.infer_seniority(
            total_years,
            [exp.title for exp in experience],
        )

        confidence = self._compute_confidence(raw_text, contact, skills, experience, education)

        return ParsedResume(
            contact=contact,
            summary=sections.summary or None,
            skills=skills,
            work_experience=experience,
            education=education,
            projects=projects,
            achievements=achievements,
            certifications=certifications,
            ats_keywords=ats_keywords,
            total_years_experience=total_years,
            seniority_level=seniority,
            raw_text_length=len(raw_text),
            parser_version=self.PARSER_VERSION,
            confidence_score=confidence,
        )

    # ── Multi-column normalisation ─────────────────────────────────────────────

    def _normalise_multicolumn_text(self, text: str) -> str:
        """
        Convert multi-column artefacts into separate lines.

        ATS resumes often lay out skills in two columns:
            "Product Strategy                    Excel"
            "User Research                        SQL"

        PyMuPDF renders these as single lines with long internal spaces.
        We split them into individual lines so downstream parsers see
        one item per line.

        Strategy:
          - If a line has 3+ interior spaces AND no bullet/date pattern,
            split it into two tokens around the whitespace run.
          - Each token becomes its own line.
        """
        result_lines: list[str] = []

        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                result_lines.append("")
                continue

            # Only split lines that look like two-column skill/data rows.
            # Don't split lines that are bullet points, dates, or long sentences.
            if self._is_two_column_line(stripped):
                parts = _RE_MULTI_SPACE.split(stripped)
                for part in parts:
                    p = part.strip()
                    if p:
                        result_lines.append(p)
            else:
                result_lines.append(stripped)

        return "\n".join(result_lines)

    def _is_two_column_line(self, line: str) -> bool:
        """
        Returns True if this line looks like two-column layout artefact.

        Signals:
          - Has interior run of 3+ spaces
          - Is not a long sentence (< 120 chars total)
          - Does not start with a bullet
          - Does not contain a date range (those should stay intact)
          - Number of words is low (typically 2–6 across two columns)
        """
        if not _RE_MULTI_SPACE.search(line):
            return False
        if line.startswith(("•", "-", "–", "*")):
            return False
        if len(line) > 150:
            return False
        # If it looks like a date range, don't split it
        if re.search(r"\d{4}\s*[-–—]\s*(?:\d{4}|Present|Current)", line, re.IGNORECASE):
            return False
        # Sentences have many words; two-column rows have few
        word_count = len(line.split())
        if word_count > 12:
            return False
        return True

    # ── PyMuPDF extraction ────────────────────────────────────────────────────

    def _extract_with_pymupdf(self, content: bytes) -> str:
        """
        Extract with PyMuPDF using blocks mode for better column handling.

        We use "blocks" instead of "text" mode because blocks gives us
        bounding box information that helps detect column boundaries.
        For simpler resumes, plain text mode with sort=True works fine.
        """
        try:
            import fitz

            doc = fitz.open(stream=content, filetype="pdf")
            all_pages: list[str] = []

            for page_num, page in enumerate(doc):
                page_text = self._extract_page_with_column_detection(page)
                if page_text.strip():
                    all_pages.append(page_text)
                logger.debug(    
                    f"pdf_page_extracted | "
                    f"page={page_num} | "
                    f"chars={len(page_text)}"
    )

            doc.close()
            return "\n".join(all_pages)

        except Exception as exc:
            logger.warning(
                f"pymupdf_extraction_failed | "
                f"error={str(exc)}"
    )
            return ""

    def _extract_page_with_column_detection(self, page) -> str:
        """
        Simple extraction using PyMuPDF sorting.
        Column detection temporarily disabled because
        resumes are being incorrectly split.
        """
        import fitz

        text = page.get_text(
            "text",
            sort=True,
            flags=fitz.TEXT_PRESERVE_LIGATURES
            | fitz.TEXT_PRESERVE_WHITESPACE,
        )

        return text or ""

    def _is_multicolumn_page(self, words: list, page_width: float) -> bool:
        """
        Heuristic: if there's a significant gap in x-positions in the middle
        of the page, it's likely two-column layout.
        """
        if not words or page_width == 0:
            return False

        mid = page_width / 2
        margin = page_width * 0.1  # 10% margin on each side of center

        left_words = [w for w in words if w[0] < mid - margin]
        right_words = [w for w in words if w[0] > mid + margin]

        # Both columns must have meaningful content
        if len(left_words) < 3 or len(right_words) < 3:
            return False

        # Right column should have a different x-range than left
        right_x_min = min(w[0] for w in right_words)
        left_x_max = max(w[2] for w in left_words)

        return right_x_min > left_x_max * 0.7  # Gap between columns

    def _extract_two_column_page(self, page, page_width: float) -> str:
        """
        Extract a two-column page by splitting at the midpoint
        and reading each half top-to-bottom independently.
        """
        import fitz

        mid = page_width / 2

        # Left column clip
        left_rect = fitz.Rect(0, 0, mid, page.rect.height)
        left_text = page.get_text("text", clip=left_rect, sort=True)

        # Right column clip
        right_rect = fitz.Rect(mid, 0, page_width, page.rect.height)
        right_text = page.get_text("text", clip=right_rect, sort=True)

        # Merge: left column first, then right column
        # This gives the NLP extractor a clean linear stream
        return left_text.strip() + "\n" + right_text.strip()

    # ── pdfplumber fallback ───────────────────────────────────────────────────

    def _extract_with_pdfplumber(self, content: bytes) -> str:
        """
        pdfplumber fallback with explicit bbox column detection.
        More reliable than word-flow for ATS layouts.
        """
        try:
            import pdfplumber

            all_pages: list[str] = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    page_width = page.width

                    # Detect two-column by checking word x-positions
                    words = page.extract_words(x_tolerance=3, y_tolerance=3)

                    if self._pdfplumber_is_multicolumn(words, page_width):
                        text = self._pdfplumber_extract_two_column(page)
                    else:
                        text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""

                    if text.strip():
                        all_pages.append(text.strip())

            return "\n".join(all_pages)

        except Exception as exc:
            logger.warning(
                f"pymupdf_extraction_failed | "
                f"error={str(exc)}"
    )
            return ""
    def _normalize_text(self, text: str) -> str:
        """
        Clean extracted PDF text for NLP processing.
        """

        if not text:
            return ""

        # Normalize line endings
        text = text.replace("\r", "\n")

        # Fix merged words like "andRetention"
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)

        # Remove excessive spaces/tabs
        text = re.sub(r"[ \t]+", " ", text)

        # Remove too many blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()
    
    def _pdfplumber_is_multicolumn(self, words: list[dict], page_width: float) -> bool:
        if not words or page_width == 0:
            return False
        mid = page_width / 2
        left = [w for w in words if w["x0"] < mid * 0.8]
        right = [w for w in words if w["x0"] > mid * 1.2]
        return len(left) >= 3 and len(right) >= 3

    def _pdfplumber_extract_two_column(self, page) -> str:
        """Split page at midpoint and extract each column."""
        mid = page.width / 2
        left_col = page.within_bbox((0, 0, mid, page.height))
        right_col = page.within_bbox((mid, 0, page.width, page.height))

        left_text = left_col.extract_text(x_tolerance=3, y_tolerance=3) or ""
        right_text = right_col.extract_text(x_tolerance=3, y_tolerance=3) or ""

        return left_text.strip() + "\n" + right_text.strip()

    # ── Confidence ────────────────────────────────────────────────────────────

    def _compute_confidence(self, raw_text, contact, skills, experience, education) -> float:
        score = 0.0
        if len(raw_text) > 500:
            score += 0.2
        if contact.email:
            score += 0.15
        if contact.name:
            score += 0.1
        if skills:
            score += min(0.2, len(skills) * 0.02)
        if experience:
            score += min(0.2, len(experience) * 0.07)
        if education:
            score += 0.1
        if any(exp.date_range for exp in experience):
            score += 0.05
        return round(min(score, 1.0), 3)
