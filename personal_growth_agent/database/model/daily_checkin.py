from enum import StrEnum
from typing import Optional

from bson import ObjectId
from pydantic import Field

from .base import Base
from .common import DateStr, Embedded


class EntryStatus(StrEnum):
    DONE = "done"
    PARTIAL = "partial"
    SKIPPED = "skipped"


class EntrySource(StrEnum):
    TAP = "tap"
    CHAT = "chat"


class CheckinEntry(Embedded):
    """One logged activity against a goal. A goal can have several entries in a day."""

    id: ObjectId = Field(default_factory=ObjectId)
    goal_id: ObjectId
    status: EntryStatus = EntryStatus.DONE
    # How much was done, in the goal's commitment unit. Defaults to one session.
    amount: float = Field(default=1, ge=0)
    note: Optional[str] = None
    source: EntrySource = EntrySource.TAP
    logged_at: int


class DailyCheckin(Base):
    """One document per user per day. Entries are added through the day; the evening
    check-in fills energy, mood and note and sets completed_at."""

    __collection__ = "daily_checkin"

    user_id: ObjectId
    date: DateStr
    entries: list[CheckinEntry] = Field(default_factory=list)
    energy: Optional[int] = Field(default=None, ge=1, le=5)
    mood: Optional[int] = Field(default=None, ge=1, le=5)
    note: Optional[str] = None
    completed_at: Optional[int] = None
