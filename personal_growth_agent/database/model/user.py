from enum import StrEnum
from typing import Optional

from personal_growth_agent.common import config

from .base import Base


class Weekday(StrEnum):
    MON = "mon"
    TUE = "tue"
    WED = "wed"
    THU = "thu"
    FRI = "fri"
    SAT = "sat"
    SUN = "sun"


class User(Base):
    __collection__ = "user"

    email: str
    name: Optional[str] = None
    # Local "HH:MM" for the evening check-in reminder.
    reminder_time: str = config.DEFAULT_REMINDER_TIME
    review_day: Weekday = Weekday.SUN
    is_onboarded: bool = False
    last_login_at: Optional[int] = None
