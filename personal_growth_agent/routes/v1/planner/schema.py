from enum import StrEnum
from typing import Any, Literal, Optional, Self

from pydantic import BaseModel, Field

from personal_growth_agent.database.model import (
    Commitment,
    Goal,
    GoalType,
    Milestone,
    Profile,
    Weekday,
)
from personal_growth_agent.schema import WeeklyLoad


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)


class ConfirmRequest(BaseModel):
    version: int = Field(ge=1)


class MilestoneResponse(BaseModel):
    id: str
    title: str
    due_date: Optional[str]
    completed_at: Optional[int]

    @classmethod
    def from_milestone(cls, milestone: Milestone) -> "MilestoneResponse":
        return cls(id=str(milestone.id), **milestone.model_dump(exclude={"id"}))


class GoalResponse(BaseModel):
    id: str
    ref: Optional[str]
    title: str
    why: Optional[str]
    type: GoalType
    priority: Optional[int]
    commitment: Commitment
    target_date: Optional[str]
    milestones: list[MilestoneResponse]

    @classmethod
    def from_goal(cls, goal: Goal, ref: Optional[str], **extra: Any) -> Self:
        return cls(
            id=str(goal.id),
            ref=ref,
            title=goal.title,
            why=goal.why,
            type=goal.type,
            priority=goal.priority,
            commitment=goal.commitment,
            target_date=goal.target_date,
            milestones=[MilestoneResponse.from_milestone(m) for m in goal.milestones],
            **extra,
        )


class GoalChange(StrEnum):
    NEW = "new"
    CHANGED = "changed"
    UNCHANGED = "unchanged"


class PendingGoalResponse(GoalResponse):
    change: GoalChange


class ProfileResponse(BaseModel):
    name: str
    reminder_time: str
    review_day: Weekday
    timezone: str

    @classmethod
    def from_profile(cls, profile: Profile) -> "ProfileResponse":
        return cls(**profile.model_dump())


class PlanResponse(BaseModel):
    goals: list[GoalResponse]
    profile: ProfileResponse
    weekly_load: WeeklyLoad


class PendingPlanResponse(BaseModel):
    version: int
    goals: list[PendingGoalResponse]
    removed: list[GoalResponse]
    profile: ProfileResponse
    profile_changed: bool
    weekly_load: WeeklyLoad


class ChatResponse(BaseModel):
    reply: str
    pending_plan: Optional[PendingPlanResponse]
    plan_presented: bool


class ConfirmResponse(BaseModel):
    current_plan: PlanResponse
    is_onboarded: bool
    message: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class PlannerStateResponse(BaseModel):
    messages: list[ChatMessage]
    current_plan: Optional[PlanResponse]
    pending_plan: Optional[PendingPlanResponse]
    is_onboarded: bool
