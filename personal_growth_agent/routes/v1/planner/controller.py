import asyncio
from collections import defaultdict
from typing import Optional

from bson import ObjectId
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from personal_growth_agent.agents.goal_planner import (
    APP_EVENT,
    CONFIRMED_MESSAGE,
    GoalPlannerAgent,
    GoalPlannerContext,
    planner_thread_id,
)
from personal_growth_agent.common.exceptions import UnauthorizedException
from personal_growth_agent.core.goals import (
    MongoPlanStore,
    active_profile,
    is_goal_changed,
    weekly_load,
)
from personal_growth_agent.database.model import User
from personal_growth_agent.schema.session import Session

from .schema import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ConfirmRequest,
    ConfirmResponse,
    GoalChange,
    GoalResponse,
    PendingGoalResponse,
    PendingPlanResponse,
    PlannerStateResponse,
    PlanResponse,
    ProfileResponse,
)

store = MongoPlanStore()
thread_locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


async def get_planner_state(agent: GoalPlannerAgent, session: Session) -> PlannerStateResponse:
    user = await load_user(session.user_id)
    history = await agent.history(planner_thread_id(session.user_id))
    return PlannerStateResponse(
        messages=to_chat_messages(history),
        current_plan=await build_current_plan(user),
        pending_plan=await build_pending_plan(user),
        is_onboarded=user.is_onboarded,
    )


async def chat_with_planner(
    agent: GoalPlannerAgent, request: ChatRequest, session: Session
) -> ChatResponse:
    thread_id = planner_thread_id(session.user_id)
    context = GoalPlannerContext(user_id=session.user_id, store=store)
    async with thread_locks[thread_id]:
        version_before = (await load_user(session.user_id)).plan_version
        reply = await agent.chat(thread_id, request.message, context)
        user = await load_user(session.user_id)
        return ChatResponse(
            reply=reply.text,
            pending_plan=await build_pending_plan(user),
            plan_presented=user.plan_version != version_before,
        )


async def confirm_plan(
    agent: GoalPlannerAgent, request: ConfirmRequest, session: Session
) -> ConfirmResponse:
    thread_id = planner_thread_id(session.user_id)
    async with thread_locks[thread_id]:
        await store.confirm(session.user_id, request.version)
        await agent.record_confirmed(thread_id)
        user = await load_user(session.user_id)
        current_plan = await build_current_plan(user)
    assert current_plan is not None
    return ConfirmResponse(
        current_plan=current_plan, is_onboarded=user.is_onboarded, message=CONFIRMED_MESSAGE
    )


async def load_user(user_id: str) -> User:
    user = await User.find_by_id(user_id)
    if user is None or user.id is None:
        raise UnauthorizedException("User no longer exists")
    return user


def to_chat_messages(history: list[BaseMessage]) -> list[ChatMessage]:
    messages = []
    for message in history:
        if isinstance(message, HumanMessage) and message.name != APP_EVENT:
            messages.append(ChatMessage(role="user", content=message.text))
        elif isinstance(message, AIMessage) and not message.tool_calls and message.text:
            messages.append(ChatMessage(role="assistant", content=message.text))
    return messages


async def build_current_plan(user: User) -> Optional[PlanResponse]:
    profile = active_profile(user)
    if profile is None:
        return None
    active = await store.active_goals(ObjectId(user.id))
    return PlanResponse(
        goals=[GoalResponse.from_goal(goal, ref) for ref, goal in active.items()],
        profile=ProfileResponse.from_profile(profile),
        weekly_load=weekly_load(list(active.values())),
    )


async def build_pending_plan(user: User) -> Optional[PendingPlanResponse]:
    oid = ObjectId(user.id)
    drafts = await store.draft_goals(oid)
    if not drafts or user.pending_profile is None:
        return None
    active = await store.active_goals(oid)
    source_of = {goal.id: (ref, goal) for ref, goal in active.items()}
    goals = []
    for draft in drafts:
        if draft.source_goal_id not in source_of:
            goals.append(PendingGoalResponse.from_goal(draft, None, change=GoalChange.NEW))
            continue
        ref, source = source_of[draft.source_goal_id]
        change = GoalChange.CHANGED if is_goal_changed(draft, source) else GoalChange.UNCHANGED
        goals.append(PendingGoalResponse.from_goal(draft, ref, change=change))
    kept = {draft.source_goal_id for draft in drafts}
    return PendingPlanResponse(
        version=user.plan_version,
        goals=goals,
        removed=[GoalResponse.from_goal(g, ref) for ref, g in active.items() if g.id not in kept],
        profile=ProfileResponse.from_profile(user.pending_profile),
        profile_changed=user.pending_profile != active_profile(user),
        weekly_load=weekly_load(drafts),
    )
