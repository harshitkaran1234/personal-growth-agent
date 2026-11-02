from enum import StrEnum
from typing import Annotated, Literal, Optional, Self

from bson import ObjectId
from pydantic import Field, model_validator

from .base import Base
from .common import DateStr, Embedded
from .user import Weekday


class GoalType(StrEnum):
    HABIT = "habit"
    LEARNING = "learning"
    PROJECT = "project"


class GoalStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class CommitmentPeriod(StrEnum):
    DAY = "day"
    WEEK = "week"


class PracticeCommitment(Embedded):
    """How much the user commits to per period, e.g. 4 sessions a week or 1 a day."""

    kind: Literal["practice"]
    period: CommitmentPeriod
    target: float = Field(gt=0)
    unit: str = Field(min_length=1, max_length=30)
    sessions: int = Field(ge=1, le=14)
    session: str = Field(min_length=1, max_length=120)
    minutes: Optional[int] = Field(default=None, ge=5, le=240)


class AvoidCommitment(Embedded):
    kind: Literal["avoid"]
    period: CommitmentPeriod
    rule: str = Field(min_length=1, max_length=120)
    target: int = Field(ge=1, le=7)

    @model_validator(mode="after")
    def check_target(self) -> Self:
        if self.period == CommitmentPeriod.DAY and self.target != 1:
            raise ValueError("A daily rule has target 1")
        return self


Commitment = Annotated[PracticeCommitment | AvoidCommitment, Field(discriminator="kind")]


class AnchoredSlot(Embedded):
    """Optional fixed time for a session, e.g. Tuesday at 19:00."""

    weekday: Weekday
    time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


class Milestone(Embedded):
    id: ObjectId = Field(default_factory=ObjectId)
    title: str = Field(min_length=1, max_length=120)
    due_date: Optional[DateStr] = None
    completed_at: Optional[int] = None


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
    commitment: Commitment
    anchored_slots: list[AnchoredSlot] = Field(default_factory=list)
    milestones: list[Milestone] = Field(default_factory=list)
    target_date: Optional[DateStr] = None
    source_goal_id: Optional[ObjectId] = None
    completed_at: Optional[int] = None
    archived_at: Optional[int] = None
