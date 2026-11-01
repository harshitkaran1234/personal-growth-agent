import argparse
import asyncio

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

from personal_growth_agent.agents import LLMClient, LLMParams
from personal_growth_agent.agents.goal_planner import (
    DEFAULT_LLM,
    GoalPlannerAgent,
    GoalPlannerContext,
)
from personal_growth_agent.common import config  # noqa: F401
from personal_growth_agent.common.exceptions import CustomException
from personal_growth_agent.core.goals import JsonPlanStore, format_minutes, weekly_load
from personal_growth_agent.llm_models import LLMModel
from personal_growth_agent.schema import PendingPlan

HELP = "/state  /plan  /confirm  /user <id>  /quit"


def thread_for(user_id: str) -> str:
    return f"onboarding:{user_id}"


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
    parser.add_argument("--model", type=LLMModel, choices=list(LLMModel), default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--user", default="u1")
    args = parser.parse_args()

    llm = DEFAULT_LLM
    if args.model or args.temperature is not None:
        overrides = {"temperature": args.temperature} if args.temperature is not None else {}
        llm = LLMClient(
            model=args.model or llm.model,
            params=LLMParams(**{**llm.params.model_dump(), **overrides}),
        )
    agent = GoalPlannerAgent(llm=llm)
    store = JsonPlanStore()
    user_id = args.user

    print(f"model: {agent.llm.model}  params: {agent.llm.params.model_dump(exclude_none=True)}")
    print(f"user: {user_id}  thread: {thread_for(user_id)}  store: {store.root}")
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
            print_state(await agent.history(thread_for(user_id)))
            continue
        if text == "/plan":
            print((await store.get(user_id)).model_dump_json(indent=2), "\n")
            continue
        if text == "/confirm":
            record = await store.get(user_id)
            try:
                version = record.pending.version if record.pending else 0
                confirmed = await store.confirm(user_id, version)
                print(f"confirmed plan v{confirmed.version} -> {store.root / user_id}.json\n")
            except CustomException as error:
                print(f"cannot confirm: {error.detail}\n")
            continue
        if text.startswith("/user"):
            parts = text.split(maxsplit=1)
            if len(parts) == 2:
                user_id = parts[1]
            print(f"user: {user_id}  thread: {thread_for(user_id)}\n")
            continue
        if text.startswith("/"):
            print(f"commands: {HELP}\n")
            continue

        before = (await store.get(user_id)).pending
        seen = len(await agent.history(thread_for(user_id)))
        context = GoalPlannerContext(user_id=user_id, store=store)
        reply = await agent.chat(thread_for(user_id), text, context)
        for message in (await agent.history(thread_for(user_id)))[seen:]:
            if isinstance(message, ToolMessage):
                print(f"\n[tool {message.name}: {message.status}] {message.text[:300]}")
        print(f"\nplanner> {reply.text}\n")
        after = (await store.get(user_id)).pending
        if after and (before is None or after.version != before.version):
            print_card(after)


if __name__ == "__main__":
    asyncio.run(main())
