from langchain.tools import ToolRuntime, tool
from langchain_core.tools import ToolException

from personal_growth_agent.common.exceptions import CustomException
from personal_growth_agent.core.goals import format_minutes, weekly_load
from personal_growth_agent.schema import PlanDraft

from .context import GoalPlannerContext


@tool(
    description=(
        "Show the full plan to the user as a card with a Confirm button. Call it once every goal "
        "is agreed and the profile (name, reminder time, review day, time zone) is complete. "
        "Call it again with the full updated plan after every change the user asks for. When "
        "changing a confirmed plan, include every goal to keep with its [gN] ref."
    )
)
async def present_plan(plan: PlanDraft, runtime: ToolRuntime[GoalPlannerContext]) -> str:
    context = runtime.context
    try:
        await context.store.present(context.user_id, plan)
    except CustomException as error:
        raise ToolException(f"{error.detail}. Fix the plan and call present_plan again.")
    load = weekly_load(plan)
    per_goal = ", ".join(f"{g.title} {format_minutes(g.minutes)}" for g in load.goals if g.minutes)
    return (
        "Plan shown to the user as a card with a Confirm button.\n"
        f"Weekly load: {per_goal}; total {format_minutes(load.total_minutes)}.\n"
        "Reply in 1-2 sentences: mention the total weekly time, then ask them to review the plan "
        "and press Confirm, or tell you what to change. Do not repeat the plan."
    )


present_plan.handle_tool_error = True
