import argparse
import asyncio
import time

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langgraph.checkpoint.mongodb import MongoDBSaver

from personal_growth_agent.agents import LLMClient, LLMParams
from personal_growth_agent.agents.goal_planner import (
    DEFAULT_LLM,
    describe_current_plan,
    GoalPlannerAgent,
    GoalPlannerContext,
)
from personal_growth_agent.common.exceptions import CustomException
from personal_growth_agent.core.goals import MongoPlanStore, format_minutes, weekly_load
from personal_growth_agent.database import build_checkpointer, db_client, ensure_indexes
from personal_growth_agent.database.model import Goal, User
from personal_growth_agent.llm_models import LLMModel
from personal_growth_agent.routes.v1.auth.email.controller.send_email_otp import normalize_email
from personal_growth_agent.schema import PendingPlan

HELP = "/state  /plan  /confirm  /quit"


def thread_for(user_id: str) -> str:
    return f"planner:{user_id}"


async def find_or_create_user(email: str) -> User:
    email = normalize_email(email)
    user = await User.find_one_by_filter({"email": email})
    if user is not None:
        return user
    now = int(time.time())
    new_user = User(email=email, created_at=now, last_login_at=now)
    user = await User.find_one_and_update(
        {"email": email},
        {"$setOnInsert": new_user.model_dump(exclude={"updated_at"})},
        upsert=True,
    )
    assert user is not None
    return user


async def reset_user(user: User, checkpointer: MongoDBSaver) -> None:
    await Goal.delete_many({"user_id": user.id})
    await user.update(
        {"$set": {"is_onboarded": False, "plan_version": 0}, "$unset": {"pending_profile": ""}}
    )
    await checkpointer.adelete_thread(thread_for(str(user.id)))
    await checkpointer.adelete_thread(f"onboarding:{user.id}")


def print_state(messages: list[BaseMessage]) -> None:
    print(f"\n--- {len(messages)} messages in this thread ---")
    for i, message in enumerate(messages):
        print(f"[{i}] {message.type}: {message.text[:200]!r}")
        if isinstance(message, AIMessage):
            for call in message.tool_calls:
                print(f"     tool call: {call['name']}")
            if message.usage_metadata:
                usage = message.usage_metadata
                print(f"     tokens in={usage['input_tokens']} out={usage['output_tokens']}")
    print()


def print_card(pending: PendingPlan) -> None:
    load = weekly_load(pending.plan)
    print(f"\n=== plan card v{pending.version} [Confirm with /confirm] ===")
    print(pending.plan.model_dump_json(indent=2))
    print(f"weekly load: {format_minutes(load.total_minutes)}\n")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Chat with the goal planner in the terminal.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--reset", action="store_true", help="delete goals and chat, start over")
    parser.add_argument("--model", type=LLMModel, choices=list(LLMModel), default=None)
    parser.add_argument("--temperature", type=float, default=None)
    args = parser.parse_args()

    db_client.init()
    await ensure_indexes()
    checkpointer = build_checkpointer()
    try:
        await run(args, checkpointer)
    finally:
        checkpointer.client.close()
        await db_client.close()


async def run(args: argparse.Namespace, checkpointer: MongoDBSaver) -> None:
    user = await find_or_create_user(args.email)
    user_id = str(user.id)
    thread_id = thread_for(user_id)
    if args.reset:
        await reset_user(user, checkpointer)
        print(f"reset {user.email}: goals, chat and onboarding cleared\n")

    llm = DEFAULT_LLM
    if args.model or args.temperature is not None:
        overrides = {"temperature": args.temperature} if args.temperature is not None else {}
        llm = LLMClient(
            model=args.model or llm.model,
            params=LLMParams(**{**llm.params.model_dump(), **overrides}),
        )
    agent = GoalPlannerAgent(llm=llm, checkpointer=checkpointer)
    store = MongoPlanStore()
    context = GoalPlannerContext(user_id=user_id, store=store)

    print(f"model: {agent.llm.model}  params: {agent.llm.params.model_dump(exclude_none=True)}")
    print(f"user: {user.email} ({user_id})  thread: {thread_id}")
    current = await store.current(user_id)
    if current.goals:
        print(f"current plan:\n{describe_current_plan(current)}")
    history = await agent.history(thread_id)
    if history:
        print(f"resuming conversation ({len(history)} messages). Last planner message:")
        last = next((m for m in reversed(history) if isinstance(m, AIMessage) and m.text), None)
        if last:
            print(f"planner> {last.text}")
    print(f"commands: {HELP}\n")

    while True:
        try:
            text = (await asyncio.to_thread(input, "you> ")).strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not text:
            continue
        if text == "/quit":
            break
        if text == "/state":
            print_state(await agent.history(thread_id))
            continue
        if text == "/plan":
            pending = await store.pending(user_id)
            print_card(pending) if pending else print("no pending plan\n")
            continue
        if text == "/confirm":
            pending = await store.pending(user_id)
            try:
                activated = await store.confirm(user_id, pending.version if pending else 0)
                print(f"confirmed: {activated} goals in the plan\n")
            except CustomException as error:
                print(f"cannot confirm: {error.detail}\n")
            continue
        if text.startswith("/"):
            print(f"commands: {HELP}\n")
            continue

        before = await store.pending(user_id)
        seen = len(await agent.history(thread_id))
        try:
            reply = await agent.chat(thread_id, text, context)
        except CustomException as error:
            print(f"\n[error {error.status_code}] {error.detail}\n")
            continue
        for message in (await agent.history(thread_id))[seen:]:
            if isinstance(message, ToolMessage):
                print(f"\n[tool {message.name}: {message.status}] {message.text[:300]}")
        print(f"\nplanner> {reply.text}\n")
        after = await store.pending(user_id)
        if after and (before is None or after.version != before.version):
            print_card(after)


if __name__ == "__main__":
    asyncio.run(main())
