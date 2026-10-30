from enum import StrEnum
from typing import Optional

from bson import ObjectId
from pydantic import Field

from .base import Base
from .common import DateStr, Embedded
from .goal import Commitment


class WeekResult(StrEnum):
    MET = "met"
    PARTLY_MET = "partly_met"
    MISSED = "missed"


class PlanStatus(StrEnum):
    DRAFT = "draft"
    ACTIVE = "active"
    # Not approved in time, so last week's plan carried over.
    CONTINUED = "continued"


class GoalWeekSummary(Embedded):
    """Snapshot of one goal for the week. Counts are computed in code from daily check-ins,
    and title and commitment are copied so later goal edits don't rewrite history."""

    goal_id: ObjectId
    title: str
    commitment: Commitment
    done: int = 0
    partial: int = 0
    skipped: int = 0
    amount: float = 0
    result: WeekResult = WeekResult.MISSED


class PlannedCommitment(Embedded):
    goal_id: ObjectId
    commitment: Commitment


class WeeklyCheckin(Base):
    """One document per user per week: the summary, the reflection and next week's plan."""

    __collection__ = "weekly_checkin"

    user_id: ObjectId
    week_start: DateStr
    goals: list[GoalWeekSummary] = Field(default_factory=list)
    reflection: Optional[str] = None
    next_week_plan: list[PlannedCommitment] = Field(default_factory=list)
    plan_status: PlanStatus = PlanStatus.DRAFT
    reviewed_at: Optional[int] = None
