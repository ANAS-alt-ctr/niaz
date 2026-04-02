from pydantic import BaseModel
from typing import Optional

class TodayUpdate(BaseModel):
    student_id: str
    bootcamp_id: str
    yesterdayWork: str
    todayPlan: str
    blockers: str
    githubLink: str
    hoursWorked: int
    needMentor: bool
    grade: Optional[str] = None
    mentor: Optional[str] = None
    feedback: Optional[str] = None
