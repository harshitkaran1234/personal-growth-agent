from enum import StrEnum
from typing import Optional

from bson import ObjectId
from pydantic import Field

from .base import Base
from .common import Embedded
from .user import Weekday


class GoalType(StrEnum):
    HABIT = "habit"
    LEARNING = "learning"
    PROJECT = "project"


class GoalStatus(StrEnum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class CommitmentPeriod(StrEnum):
    DAY = "day"
    WEEK = "week"


class Commitment(Embedded):
    """How much the user commits to per period, e.g. 4 sessions a week or 1 a day."""

    period: CommitmentPeriod = CommitmentPeriod.WEEK
    target: float = Field(default=1, gt=0)
    unit: str = "sessions"


class AnchoredSlot(Embedded):
    """Optional fixed time for a session, e.g. Tuesday at 19:00."""

    weekday: Weekday
    time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


class Goal(Base):
    __collection__ = "goal"

    user_id: ObjectId
    title: str = Field(min_length=1, max_length=120)
    description: Optional[str] = None
    # What the user wants out of it. Shown back to them in reviews and nudges.
    why: Optional[str] = None
    type: GoalType = GoalType.HABIT
    status: GoalStatus = GoalStatus.ACTIVE
    # Lower number is more important. Optional ordering, not a score.
    priority: Optional[int] = Field(default=None, ge=1)
    commitment: Commitment = Field(default_factory=Commitment)
    anchored_slots: list[AnchoredSlot] = Field(default_factory=list)
    completed_at: Optional[int] = None
    archived_at: Optional[int] = None
