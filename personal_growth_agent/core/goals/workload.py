from personal_growth_agent.database.model import CommitmentPeriod
from personal_growth_agent.schema import (
    GoalLoad,
    PlanDraft,
    PracticeCommitment,
    ProposedGoal,
    WeeklyLoad,
)


def goal_weekly_minutes(goal: ProposedGoal) -> int:
    commitment = goal.commitment
    if not isinstance(commitment, PracticeCommitment) or commitment.minutes is None:
        return 0
    per_week = 7 if commitment.period == CommitmentPeriod.DAY else 1
    return commitment.sessions * commitment.minutes * per_week


def weekly_load(plan: PlanDraft) -> WeeklyLoad:
    goals = [GoalLoad(title=g.title, minutes=goal_weekly_minutes(g)) for g in plan.goals]
    return WeeklyLoad(goals=goals, total_minutes=sum(g.minutes for g in goals))


def format_minutes(minutes: int) -> str:
    hours, rest = divmod(minutes, 60)
    return f"{hours}h {rest}m" if hours else f"{rest}m"
