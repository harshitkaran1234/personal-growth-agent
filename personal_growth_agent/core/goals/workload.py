from collections.abc import Sequence

from personal_growth_agent.database import model as db
from personal_growth_agent.database.model import CommitmentPeriod, Goal
from personal_growth_agent.schema import GoalLoad, PracticeCommitment, ProposedGoal, WeeklyLoad


def goal_weekly_minutes(goal: ProposedGoal | Goal) -> int:
    commitment = goal.commitment
    if not isinstance(commitment, (PracticeCommitment, db.PracticeCommitment)):
        return 0
    if commitment.minutes is None:
        return 0
    per_week = 7 if commitment.period == CommitmentPeriod.DAY else 1
    return commitment.sessions * commitment.minutes * per_week


def weekly_load(goals: Sequence[ProposedGoal | Goal]) -> WeeklyLoad:
    loads = [GoalLoad(title=g.title, minutes=goal_weekly_minutes(g)) for g in goals]
    return WeeklyLoad(goals=loads, total_minutes=sum(g.minutes for g in loads))


def format_minutes(minutes: int) -> str:
    hours, rest = divmod(minutes, 60)
    if not hours:
        return f"{rest}m"
    return f"{hours}h {rest}m" if rest else f"{hours}h"
