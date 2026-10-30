from bson import ObjectId

from personal_growth_agent.common.exceptions import InvalidRequestException, UnauthorizedException
from personal_growth_agent.database.model import User
from personal_growth_agent.schema.session import Session

from .schema import UpdateUserRequest, UserResponse


async def get_current_user(session: Session) -> UserResponse:
    user = await User.find_by_id(session.user_id)
    if not user:
        raise UnauthorizedException("User no longer exists")
    return UserResponse.from_user(user)


async def update_current_user(request: UpdateUserRequest, session: Session) -> UserResponse:
    patch = request.model_dump(exclude_none=True)
    if not patch:
        raise InvalidRequestException("Nothing to update")
    user = await User.find_one_and_update({"_id": ObjectId(session.user_id)}, {"$set": patch})
    if not user:
        raise UnauthorizedException("User no longer exists")
    return UserResponse.from_user(user)
