from fastapi import APIRouter
from app.services.jd_parser import JDParser

router = APIRouter()

parser = JDParser()


@router.post("/parse")
async def parse_job_description(payload: dict):

    text = payload.get("text", "")

    result = parser.parse(text)

    return {
        "success": True,
        "parsed": result.model_dump()
    }