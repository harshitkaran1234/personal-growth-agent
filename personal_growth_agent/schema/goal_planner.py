from datetime import date
from typing import Optional, Self

from pydantic import BaseModel, Field, model_validator

from personal_growth_agent.database.model import CommitmentPeriod, GoalType, Weekday


class ProposedCommitment(BaseModel):
    period: CommitmentPeriod = Field(description="Whether the target is per day or per week.")
    target: float = Field(
        gt=0, description="Amount the user commits to per period, measured in `unit`."
    )
    unit: str = Field(
        min_length=1,
        max_length=30,
        description='What the target counts, e.g. "sessions", "pages", "km", "problems".',
    )
    sessions: int = Field(
        ge=1,
        le=14,
        description="How many sittings per period the target is split into. "
        'Equals `target` when unit is "sessions".',
    )
    session: str = Field(
        min_length=1,
        max_length=120,
        description='What one sitting looks like, e.g. "45 min chapter + notes", "5 km easy run".',
    )
    minutes: int = Field(ge=5, le=240, description="Rough length of one sitting in minutes.")

    @model_validator(mode="after")
    def check_sessions_unit(self) -> Self:
        if self.unit.strip().lower() == "sessions" and self.sessions != self.target:
            raise ValueError('When unit is "sessions", sessions must equal target')
        return self


class ProposedMilestone(BaseModel):
    title: str = Field(
        min_length=1, max_length=120, description="A concrete checkpoint on the way to the goal."
    )
    due_date: date = Field(description="Date the checkpoint should be reached by.")


class ProposedGoal(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=120,
        description='Short, specific goal title, e.g. "Learn system design".',
    )
    why: str = Field(
        min_length=1, description="Why the goal matters to the user, in their own words."
    )
    type: GoalType = Field(
        description="habit: ongoing practice. learning: a skill or subject. "
        "project: something to finish or ship."
    )
    commitment: ProposedCommitment
    target_date: Optional[date] = Field(
        default=None, description="When the goal should be reached. None for ongoing habits."
    )
    milestones: list[ProposedMilestone] = Field(
        default_factory=list,
        max_length=5,
        description="Checkpoints in date order. Usually 2 to 5 for learning and project goals, "
        "none for habits.",
    )
    priority: int = Field(ge=1, description="Rank among the user's goals. 1 is most important.")

    @model_validator(mode="after")
    def check_dates(self) -> Self:
        if self.type == GoalType.HABIT and self.target_date is not None:
            raise ValueError("Habits are ongoing and have no target_date")
        due_dates = [milestone.due_date for milestone in self.milestones]
        if due_dates != sorted(due_dates):
            raise ValueError("Milestones must be in date order")
        if self.target_date and due_dates and due_dates[-1] > self.target_date:
            raise ValueError("Milestones must be due on or before target_date")
        return self


class ProfileDraft(BaseModel):
    name: str = Field(min_length=1, max_length=80, description="What to call the user.")
    reminder_time: str = Field(
        pattern=r"^([01]\d|2[0-3]):[0-5]\d$",
        description='Local time for the evening check-in reminder, 24-hour "HH:MM".',
    )
    review_day: Weekday = Field(description="Weekday for the weekly review.")


class PlanDraft(BaseModel):
    goals: list[ProposedGoal] = Field(
        min_length=1, max_length=3, description="The goals the user agreed to, 1 to 3."
    )
    profile: Optional[ProfileDraft] = Field(
        default=None, description="User settings, or null if they were not agreed in the chat."
    )

    @model_validator(mode="after")
    def check_priorities(self) -> Self:
        priorities = sorted(goal.priority for goal in self.goals)
        if priorities != list(range(1, len(self.goals) + 1)):
            raise ValueError("Priorities must be 1..n with no gaps or repeats")
        return self
