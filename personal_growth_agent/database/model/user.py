from enum import StrEnum
from typing import Optional

from personal_growth_agent.common import config

from .base import Base
from .common import Embedded


class Weekday(StrEnum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


class Profile(Embedded):
    name: str
    reminder_time: str
    review_day: Weekday
    timezone: str


class User(Base):
    __collection__ = "user"

    email: str
    name: Optional[str] = None
    # Local "HH:MM" for the evening check-in reminder.
    reminder_time: str = config.DEFAULT_REMINDER_TIME
    review_day: Weekday = Weekday.SUN
    timezone: str = "UTC"
    is_onboarded: bool = False
    plan_version: int = 0
    pending_profile: Optional[Profile] = None
    last_login_at: Optional[int] = None
