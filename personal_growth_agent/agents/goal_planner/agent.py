from datetime import date
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from personal_growth_agent.llm_models import LLMModel
from personal_growth_agent.prompts import GOAL_PLANNER_SYSTEM_PROMPT

from ..llm_client import LLMClient
from .context import GoalPlannerContext
from .tools import present_plan

DEFAULT_LLM = LLMClient(model=LLMModel.CLAUDE_SONNET_5_5)


@dynamic_prompt
def system_prompt(request: ModelRequest) -> str:
    today = date.today()
    return GOAL_PLANNER_SYSTEM_PROMPT.format(today=today.isoformat(), weekday=today.strftime("%A"))


class GoalPlannerAgent(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    llm: LLMClient = DEFAULT_LLM
    checkpointer: BaseCheckpointSaver[Any] = Field(default_factory=InMemorySaver)

    _graph: CompiledStateGraph[Any, Any, Any, Any] = PrivateAttr()

    def model_post_init(self, context: Any) -> None:
        self._graph = create_agent(
            model=self.llm.chat_model,
            tools=[present_plan],
            middleware=[system_prompt],
            context_schema=GoalPlannerContext,
            checkpointer=self.checkpointer,
            name="goal_planner",
        )

    async def chat(self, thread_id: str, message: str, context: GoalPlannerContext) -> AIMessage:
        result = await self._graph.ainvoke(
            {"messages": [HumanMessage(message)]}, config=self._config(thread_id), context=context
        )
        reply = result["messages"][-1]
        assert isinstance(reply, AIMessage)
        return reply

    async def history(self, thread_id: str) -> list[BaseMessage]:
        state = await self._graph.aget_state(self._config(thread_id))
        messages: list[BaseMessage] = state.values.get("messages", [])
        return messages

    @staticmethod
    def _config(thread_id: str) -> RunnableConfig:
        return {"configurable": {"thread_id": thread_id}}
