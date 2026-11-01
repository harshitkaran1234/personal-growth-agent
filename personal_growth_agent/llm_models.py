from enum import StrEnum


class LLMModel(StrEnum):
    CLAUDE_FABLE_5_1 = "anthropic:claude-fable-5-1"
    CLAUDE_OPUS_5_5 = "anthropic:claude-opus-5-5"
    CLAUDE_SONNET_5_5 = "anthropic:claude-sonnet-5-5"
    CLAUDE_HAIKU_5_5 = "anthropic:claude-haiku-5-5"
    GPT_5 = "openai:gpt-5"
    GPT_4_1 = "openai:gpt-4.1"
