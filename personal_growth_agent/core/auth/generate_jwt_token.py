import time

import jwt

from personal_growth_agent.common import config
from personal_growth_agent.database.model import User
from personal_growth_agent.schema.session import Session


def generate_jwt_token(user: User) -> str:
    """Generate JWT token for stateless session."""
    session = Session(
        user_id=str(user.id),
        expires_at=round(time.time() + config.JWT_EXPIRY_TIME),
    )
    return jwt.encode(session.model_dump(), config.JWT_SECRET, algorithm="HS256")
