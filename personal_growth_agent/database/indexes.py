from pymongo import ASCENDING, DESCENDING, IndexModel

from personal_growth_agent.common import logger

from .model import DailyCheckin, Goal, OtpRequest, User, WeeklyCheckin


async def ensure_indexes() -> None:
    logger.info("Ensuring mongodb indexes")
    await User.collection().create_indexes([IndexModel([("email", ASCENDING)], unique=True)])
    await OtpRequest.collection().create_indexes(
        [
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0),
        ]
    )
    await Goal.collection().create_indexes(
        [IndexModel([("user_id", ASCENDING), ("status", ASCENDING), ("priority", ASCENDING)])]
    )
    await DailyCheckin.collection().create_indexes(
        [
            IndexModel([("user_id", ASCENDING), ("date", DESCENDING)], unique=True),
            IndexModel(
                [("user_id", ASCENDING), ("entries.goal_id", ASCENDING), ("date", DESCENDING)]
            ),
        ]
    )
    await WeeklyCheckin.collection().create_indexes(
        [IndexModel([("user_id", ASCENDING), ("week_start", DESCENDING)], unique=True)]
    )
