"""
Normalization utilities for matching engine.
"""


SKILL_SYNONYMS = {
    "pm": "product management",
    "product mgr": "product management",
    "js": "javascript",
    "py": "python",
    "postgres": "postgresql",
    "node": "nodejs",
    "ml": "machine learning",
}


def normalize_skill(skill: str) -> str:
    """
    Normalize skill names for reliable matching.
    """

    normalized = (
        skill.strip()
        .lower()
        .replace("-", " ")
        .replace(".", "")
    )

    return SKILL_SYNONYMS.get(normalized, normalized)