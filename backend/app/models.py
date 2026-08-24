from pydantic import BaseModel
from typing import List, Optional

class ResumeData(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    skills: List[str] = []
    experience: str = ""
    education: str = ""
    raw_text: str = ""
    filename: str = ""
    uploaded_at: str = ""
    match_score: Optional[int] = None
    justification: Optional[str] = None
    matched_skills: Optional[List[str]] = []
    missing_skills: Optional[List[str]] = []

class JobDescription(BaseModel):
    id: Optional[str] = None
    title: str
    description: str
    requirements: Optional[str] = None
    created_at: str = ""

class MatchRequest(BaseModel):
    resume_id: str
    job_id: str