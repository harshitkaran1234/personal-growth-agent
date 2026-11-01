from langchain.tools import ToolRuntime, tool

from personal_growth_agent.core.goals import format_minutes, weekly_load
from personal_growth_agent.schema import PlanDraft

from .context import GoalPlannerContext


@tool(
    description=(
        "Show the full plan to the user as a card with a Confirm button. Call it once every goal "
        "is agreed and you have the user's name, reminder time and review day. Call it again "
        "with the full updated plan after every change the user asks for."
    )
)
async def present_plan(plan: PlanDraft, runtime: ToolRuntime[GoalPlannerContext]) -> str:
    context = runtime.context
    await context.store.present(context.user_id, plan)
    load = weekly_load(plan)
    per_goal = ", ".join(f"{g.title} {format_minutes(g.minutes)}" for g in load.goals)
    return (
        "Plan shown to the user as a card with a Confirm button.\n"
        f"Weekly load: {per_goal}; total {format_minutes(load.total_minutes)}.\n"
        "Reply in 1-2 sentences: mention the total weekly time, then ask them to review the plan "
        "and press Confirm, or tell you what to change. Do not repeat the plan."
    )
