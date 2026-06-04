from app.utils.skill_synonyms import SKILL_SYNONYMS

def normalize_skill(skill: str) -> str:
    if not skill:
        return ""

    skill = skill.lower().strip()

    return SKILL_SYNONYMS.get(skill, skill)