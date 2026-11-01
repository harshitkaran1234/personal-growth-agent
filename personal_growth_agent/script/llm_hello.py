import argparse
import asyncio
import time
from langchain_core.messages import AIMessage, AIMessageChunk

from personal_growth_agent.agents import LLMClient, LLMParams
from personal_growth_agent.common import config  # noqa: F401
from personal_growth_agent.llm_models import LLMModel

SYSTEM_PROMPT = (
    "You are a friendly goal-planning coach. The user tells you a goal. "
    "Reply in at most 3 sentences: reflect the goal back and ask ONE question "
    "that helps make it concrete."
)
DEFAULT_MESSAGE = "I want to master system design in 3 months."


def print_response(response: AIMessage, seconds: float) -> None:
    print(f"\n--- reply ({seconds:.1f}s) ---")
    print(response.text)
    print("\n--- usage_metadata ---")
    print(response.usage_metadata)
    print("\n--- response_metadata ---")
    for key in ("model_name", "model", "stop_reason", "finish_reason"):
        if key in response.response_metadata:
            print(f"{key}: {response.response_metadata[key]}")


async def run_invoke(client: LLMClient, prompt: str) -> None:
    start = time.perf_counter()
    response = await client.ainvoke(prompt, system=SYSTEM_PROMPT)
    print_response(response, time.perf_counter() - start)


async def run_stream(client: LLMClient, prompt: str) -> None:
    start = time.perf_counter()
    print("\n--- streaming ---")
    full: AIMessageChunk | None = None
    async for chunk in client.astream(prompt, system=SYSTEM_PROMPT):
        print(chunk.text, end="", flush=True)
        full = chunk if full is None else full + chunk
    print(f"\n\n(first to last chunk: {time.perf_counter() - start:.1f}s)")
    if full is not None:
        print(f"usage_metadata: {full.usage_metadata}")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Send one message to any LLM.")
    parser.add_argument("message", nargs="?", default=DEFAULT_MESSAGE)
    parser.add_argument(
        "--model", type=LLMModel, choices=list(LLMModel), default=LLMModel.CLAUDE_SONNET_5_5
    )
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--stream", action="store_true")
    parser.add_argument("--repeat", type=int, default=1, help="send the same message N times")
    args = parser.parse_args()

    params = LLMParams(temperature=args.temperature, max_tokens=args.max_tokens)
    client = LLMClient(model=args.model, params=params)
    print(f"model: {client.model}  params: {params.model_dump(exclude_none=True)}")

    for i in range(args.repeat):
        if args.repeat > 1:
            print(f"\n===== run {i + 1}/{args.repeat} =====")
        if args.stream:
            await run_stream(client, args.message)
        else:
            await run_invoke(client, args.message)


if __name__ == "__main__":
    asyncio.run(main())
