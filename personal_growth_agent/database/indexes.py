from pymongo import ASCENDING, IndexModel

from personal_growth_agent.common import logger

from .model import OtpRequest, User


async def ensure_indexes() -> None:
    logger.info("Ensuring mongodb indexes")
    await User.collection().create_indexes([IndexModel([("email", ASCENDING)], unique=True)])
    await OtpRequest.collection().create_indexes(
        [
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0),
        ]
    )
