from fastapi import APIRouter
from app.api.v1.resumes import router as resumes_router
from app.api.v1.matches import router as matches_router

router = APIRouter()

router.include_router(resumes_router)
router.include_router(matches_router)