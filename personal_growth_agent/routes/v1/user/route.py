from fastapi import APIRouter, Depends

from personal_growth_agent.common.session_validator import validate_session
from personal_growth_agent.schema.session import Session

from .controller import get_current_user, update_current_user
from .schema import UpdateUserRequest, UserResponse

router = APIRouter(prefix="/user", tags=["User"])


@router.get("/me")
async def get_me(session: Session = Depends(validate_session)) -> UserResponse:
    return await get_current_user(session)


@router.patch("/me")
async def update_me(
    request: UpdateUserRequest, session: Session = Depends(validate_session)
) -> UserResponse:
    return await update_current_user(request, session)
