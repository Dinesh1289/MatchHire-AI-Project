from pydantic import BaseModel
from typing import List, Optional


class ParsedJobDescription(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    responsibilities: List[str] = []
    qualifications: List[str] = []
    min_experience_years: Optional[int] = None
    keywords: List[str] = []
    raw_text_length: int = 0