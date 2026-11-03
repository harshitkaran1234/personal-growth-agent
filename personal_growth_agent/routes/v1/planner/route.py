from fastapi import APIRouter, Depends, Request

from personal_growth_agent.agents.goal_planner import GoalPlannerAgent
from personal_growth_agent.common.session_validator import validate_session
from personal_growth_agent.schema.session import Session

from .controller import chat_with_planner, confirm_plan, get_planner_state
from .schema import ChatRequest, ChatResponse, ConfirmRequest, ConfirmResponse, PlannerStateResponse

router = APIRouter(prefix="/planner", tags=["Planner"])


def get_goal_planner(request: Request) -> GoalPlannerAgent:
    agent: GoalPlannerAgent = request.app.state.goal_planner
    return agent


@router.get("")
async def get_state(
    session: Session = Depends(validate_session),
    agent: GoalPlannerAgent = Depends(get_goal_planner),
) -> PlannerStateResponse:
    return await get_planner_state(agent, session)


@router.post("/chat")
async def chat(
    request: ChatRequest,
    session: Session = Depends(validate_session),
    agent: GoalPlannerAgent = Depends(get_goal_planner),
) -> ChatResponse:
    return await chat_with_planner(agent, request, session)


@router.post("/confirm")
async def confirm(
    request: ConfirmRequest,
    session: Session = Depends(validate_session),
    agent: GoalPlannerAgent = Depends(get_goal_planner),
) -> ConfirmResponse:
    return await confirm_plan(agent, request, session)
