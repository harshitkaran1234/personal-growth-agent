import argparse
import asyncio
import uuid

from langchain_core.messages import AIMessage, BaseMessage

from personal_growth_agent.agents import LLMClient, LLMParams
from personal_growth_agent.agents.goal_planner import DEFAULT_LLM, GoalPlannerAgent
from personal_growth_agent.common import config  # noqa: F401
from personal_growth_agent.llm_models import LLMModel

HELP = "/state  /new  /thread <id>  /quit"


def new_thread_id() -> str:
    return f"onboarding:{uuid.uuid4().hex[:8]}"


def print_state(messages: list[BaseMessage]) -> None:
    print(f"\n--- {len(messages)} messages in this thread ---")
    for i, message in enumerate(messages):
        print(f"[{i}] {message.type}: {message.text[:200]!r}")
        if isinstance(message, AIMessage) and message.usage_metadata:
            usage = message.usage_metadata
            print(f"     tokens in={usage['input_tokens']} out={usage['output_tokens']}")
    print()


async def main() -> None:
    parser = argparse.ArgumentParser(description="Chat with the goal planner in the terminal.")
    parser.add_argument("--model", type=LLMModel, choices=list(LLMModel), default=None)
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--thread", default=None)
    args = parser.parse_args()

    llm = DEFAULT_LLM
    if args.model or args.temperature is not None:
        overrides = {"temperature": args.temperature} if args.temperature is not None else {}
        llm = LLMClient(
            model=args.model or llm.model,
            params=LLMParams(**{**llm.params.model_dump(), **overrides}),
        )
    agent = GoalPlannerAgent(llm=llm)

    thread_id = args.thread or new_thread_id()
    print(f"model: {agent.llm.model}  params: {agent.llm.params.model_dump(exclude_none=True)}")
    print(f"thread: {thread_id}\ncommands: {HELP}\n")

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
        if text == "/new":
            thread_id = new_thread_id()
            print(f"thread: {thread_id}\n")
            continue
        if text.startswith("/thread"):
            parts = text.split(maxsplit=1)
            if len(parts) == 2:
                thread_id = parts[1]
            print(f"thread: {thread_id}\n")
            continue
        if text.startswith("/"):
            print(f"commands: {HELP}\n")
            continue

        reply = await agent.chat(thread_id, text)
        print(f"\nplanner> {reply.text}\n")


if __name__ == "__main__":
    asyncio.run(main())
