from fastapi import APIRouter

from personal_growth_agent.schema.api_response import SuccessResponse

router = APIRouter(tags=["Health"])


@router.get("/health")
async def healthcheck() -> SuccessResponse:
    return SuccessResponse(message="healthy")
