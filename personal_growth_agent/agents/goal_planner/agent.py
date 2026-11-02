from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from langchain.agents import create_agent
from langchain.agents.middleware import (
    AgentMiddleware,
    ModelCallLimitMiddleware,
    ModelRequest,
    ToolCallLimitMiddleware,
    dynamic_prompt,
)
from langchain.agents.middleware.model_call_limit import ModelCallLimitExceededError
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, RemoveMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from personal_growth_agent.common import logger
from personal_growth_agent.common.exceptions import (
    LLMUnavailableException,
    PlannerFailedException,
)
from personal_growth_agent.database.model import CommitmentPeriod
from personal_growth_agent.llm_models import LLMModel
from personal_growth_agent.prompts import GOAL_PLANNER_SYSTEM_PROMPT
from personal_growth_agent.schema import CurrentPlan, PracticeCommitment, ProposedCommitment

from ..llm_client import PROVIDER_UNAVAILABLE_ERRORS, LLMClient
from .context import GoalPlannerContext
from .tools import present_plan

DEFAULT_LLM = LLMClient(model=LLMModel.CLAUDE_SONNET_5_5)
MAX_PLAN_CALLS_PER_TURN = 3
MAX_MODEL_CALLS_PER_TURN = 6


def describe_commitment(commitment: ProposedCommitment) -> str:
    if isinstance(commitment, PracticeCommitment):
        text = (
            f"{commitment.target:g} {commitment.unit}/{commitment.period} as "
            f"{commitment.sessions} x {commitment.session}"
        )
        return f"{text}, ~{commitment.minutes} min each" if commitment.minutes else text
    if commitment.period == CommitmentPeriod.DAY:
        return f'avoid "{commitment.rule}", every day'
    return f'avoid "{commitment.rule}", {commitment.target} days/week'


def describe_current_plan(plan: CurrentPlan) -> str:
    if not plan.goals:
        return "No confirmed plan yet. This is onboarding."
    lines = []
    for current in plan.goals:
        goal = current.goal
        line = (
            f"[{current.ref}] {goal.title} ({goal.type}), priority {goal.priority}: "
            f"{describe_commitment(goal.commitment)}. Why: {goal.why}"
        )
        if goal.target_date:
            line += f". Target {goal.target_date}"
        if goal.milestones:
            line += ". Milestones: " + "; ".join(
                f"{m.title} by {m.due_date}" for m in goal.milestones
            )
        lines.append(line)
    if plan.profile:
        p = plan.profile
        lines.append(
            f"Profile: {p.name}, reminder {p.reminder_time}, review {p.review_day}, "
            f"time zone {p.timezone}"
        )
    return "\n".join(lines)


@dynamic_prompt
async def system_prompt(request: ModelRequest[GoalPlannerContext]) -> str:
    context = request.runtime.context
    plan = await context.store.current(context.user_id)
    zone = ZoneInfo(plan.profile.timezone) if plan.profile else ZoneInfo("UTC")
    today = datetime.now(zone).date()
    return GOAL_PLANNER_SYSTEM_PROMPT.format(
        today=today.isoformat(),
        weekday=today.strftime("%A"),
        current_plan=describe_current_plan(plan),
    )


class GoalPlannerAgent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    llm: LLMClient = DEFAULT_LLM
    checkpointer: BaseCheckpointSaver[Any] = Field(default_factory=InMemorySaver)

    _graph: CompiledStateGraph[Any, Any, Any, Any] = PrivateAttr()

    def model_post_init(self, context: Any) -> None:
        middleware: list[AgentMiddleware[Any, Any, Any]] = [
            system_prompt,
            ToolCallLimitMiddleware(
                tool_name=present_plan.name,
                run_limit=MAX_PLAN_CALLS_PER_TURN,
                exit_behavior="continue",
            ),
            ModelCallLimitMiddleware(run_limit=MAX_MODEL_CALLS_PER_TURN, exit_behavior="error"),
        ]
        self._graph = create_agent(
            model=self.llm.chat_model,
            tools=[present_plan],
            middleware=middleware,
            context_schema=GoalPlannerContext,
            checkpointer=self.checkpointer,
            name="goal_planner",
        )

    async def chat(self, thread_id: str, message: str, context: GoalPlannerContext) -> AIMessage:
        kept = len(await self.history(thread_id))
        try:
            result = await self._graph.ainvoke(
                {"messages": [HumanMessage(message)]},
                config=self._config(thread_id),
                context=context,
            )
        except Exception as error:
            await self._rollback(thread_id, kept)
            if isinstance(error, ModelCallLimitExceededError):
                logger.warning(f"[goal_planner] model call limit hit on {thread_id}: {error}")
                raise PlannerFailedException(
                    "Sorry, something went wrong on my side. Please send that again."
                ) from error
            if isinstance(error, PROVIDER_UNAVAILABLE_ERRORS):
                logger.exception(f"[goal_planner] LLM provider failed on {thread_id}")
                raise LLMUnavailableException(
                    "The planner is unavailable right now. Please try again in a moment."
                ) from error
            raise
        reply = result["messages"][-1]
        assert isinstance(reply, AIMessage)
        return reply

    async def history(self, thread_id: str) -> list[BaseMessage]:
        state = await self._graph.aget_state(self._config(thread_id))
        messages: list[BaseMessage] = state.values.get("messages", [])
        return messages

    async def _rollback(self, thread_id: str, kept: int) -> None:
        added = (await self.history(thread_id))[kept:]
        removals = [RemoveMessage(id=m.id) for m in added if m.id]
        if removals:
            await self._graph.aupdate_state(self._config(thread_id), {"messages": removals})

    @staticmethod
    def _config(thread_id: str) -> RunnableConfig:
        return {"configurable": {"thread_id": thread_id}}
