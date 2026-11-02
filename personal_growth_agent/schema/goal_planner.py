from datetime import date
from typing import Annotated, Literal, Optional, Self

from pydantic import BaseModel, Field, field_validator, model_validator

from personal_growth_agent.database.model import CommitmentPeriod, GoalType, Weekday

from .validators import validate_timezone


class PracticeCommitment(BaseModel):
    kind: Literal["practice"] = Field(
        description="Something the user actively does: study, run, read, build."
    )
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
    minutes: Optional[int] = Field(
        default=None,
        ge=5,
        le=240,
        description="Rough length of one sitting in minutes. Null when time is not what "
        'matters, e.g. "make 3 reels a week".',
    )

    @model_validator(mode="after")
    def check_sessions_unit(self) -> Self:
        if self.unit.strip().lower() == "sessions" and self.sessions != self.target:
            raise ValueError('When unit is "sessions", sessions must equal target')
        return self


class AvoidCommitment(BaseModel):
    kind: Literal["avoid"] = Field(
        description="Something the user stops or limits doing: smoking, sugar, late-night phone."
    )
    period: CommitmentPeriod = Field(
        description="day if the rule holds every day, week if it holds on some days of the week."
    )
    rule: str = Field(
        min_length=1,
        max_length=120,
        description='The rule to keep, e.g. "no cigarettes", "no sugar", "no phone after 22:00".',
    )
    target: int = Field(
        ge=1,
        le=7,
        description="Days per period the rule should hold: 1 for a daily rule, "
        "1 to 7 for a weekly one (e.g. 5 for weekdays only).",
    )

    @model_validator(mode="after")
    def check_target(self) -> Self:
        if self.period == CommitmentPeriod.DAY and self.target != 1:
            raise ValueError("A daily rule has target 1")
        return self


ProposedCommitment = Annotated[
    PracticeCommitment | AvoidCommitment,
    Field(description="practice for things to do, avoid for things to stop or limit."),
    Field(discriminator="kind"),
]


class ProposedMilestone(BaseModel):
    title: str = Field(
        min_length=1, max_length=120, description="A concrete checkpoint on the way to the goal."
    )
    due_date: date = Field(description="Date the checkpoint should be reached by.")


class ProposedGoal(BaseModel):
    ref: Optional[str] = Field(
        default=None,
        pattern=r"^g\d+$",
        description="The [gN] ref of the current goal this changes or keeps. Null for a new goal.",
    )
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
    timezone: str = Field(
        description='The user\'s IANA time zone, e.g. "Asia/Kolkata", "Europe/London".'
    )

    @field_validator("timezone")
    @classmethod
    def check_timezone(cls, value: str) -> str:
        return validate_timezone(value)


class PlanDraft(BaseModel):
    goals: list[ProposedGoal] = Field(
        min_length=1, max_length=10, description="The goals the user agreed to, 1 to 10."
    )
    profile: ProfileDraft = Field(description="The user's name, reminder time and review day.")

    @model_validator(mode="after")
    def check_priorities(self) -> Self:
        priorities = sorted(goal.priority for goal in self.goals)
        if priorities != list(range(1, len(self.goals) + 1)):
            raise ValueError("Priorities must be 1..n with no gaps or repeats")
        refs = [goal.ref for goal in self.goals if goal.ref]
        if len(refs) != len(set(refs)):
            raise ValueError("Each current goal ref can appear only once")
        return self


class PendingPlan(BaseModel):
    version: int = Field(ge=1)
    plan: PlanDraft


class CurrentGoal(BaseModel):
    ref: str
    goal: ProposedGoal


class CurrentPlan(BaseModel):
    goals: list[CurrentGoal]
    profile: Optional[ProfileDraft] = None
