from fastapi import APIRouter

from app.api.v1 import resumes
from app.api.v1 import matches
from app.api.v1 import job_descriptions

router = APIRouter()

router.include_router(
    resumes.router,
    prefix="/resumes",
    tags=["Resumes"]
)

router.include_router(
    matches.router,
    prefix="/matches",
    tags=["Matches"]
)

router.include_router(
    job_descriptions.router,
    prefix="/job-descriptions",
    tags=["Job Descriptions"]
)