import time

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import ValidationError

from personal_growth_agent.common import config
from personal_growth_agent.common.exceptions import UnauthorizedException
from personal_growth_agent.schema.session import Session

auth_scheme = HTTPBearer(auto_error=False)


async def validate_session(
    auth_creds: HTTPAuthorizationCredentials | None = Depends(auth_scheme),
) -> Session:
    """Validate the JWT bearer token and return the caller's session."""
    if not auth_creds:
        raise UnauthorizedException("Could not validate credentials")
    try:
        session = Session.model_validate(
            jwt.decode(auth_creds.credentials, config.JWT_SECRET, algorithms=["HS256"])
        )
    except (jwt.InvalidTokenError, ValidationError):
        raise UnauthorizedException("Could not validate credentials")
    if session.expires_at < time.time():
        raise UnauthorizedException("Session has expired")
    return session
