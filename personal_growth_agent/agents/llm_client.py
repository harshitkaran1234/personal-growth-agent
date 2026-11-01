from collections.abc import AsyncIterator
from typing import Optional, TypeVar

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from pydantic import BaseModel, ConfigDict, Field, PrivateAttr

from personal_growth_agent.llm_models import LLMModel

Prompt = str | list[BaseMessage]
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMParams(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    temperature: Optional[float] = Field(default=None, ge=0, le=2)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    top_p: Optional[float] = Field(default=None, gt=0, le=1)
    timeout: float = Field(default=60, gt=0)
    max_retries: int = Field(default=2, ge=0)


class LLMClient(BaseModel):
    model_config = ConfigDict(frozen=True)

    model: LLMModel
    params: LLMParams = Field(default_factory=LLMParams)

    _chat_model: Optional[BaseChatModel] = PrivateAttr(default=None)

    @property
    def chat_model(self) -> BaseChatModel:
        if self._chat_model is None:
            chat_model = init_chat_model(self.model, **self.params.model_dump(exclude_none=True))
            assert isinstance(chat_model, BaseChatModel)
            self._chat_model = chat_model
        return self._chat_model

    async def ainvoke(self, prompt: Prompt, system: Optional[str] = None) -> AIMessage:
        response = await self.chat_model.ainvoke(self._messages(prompt, system))
        assert isinstance(response, AIMessage)
        return response

    async def astructured(
        self, prompt: Prompt, schema: type[SchemaT], system: Optional[str] = None
    ) -> SchemaT:
        result = await self.chat_model.with_structured_output(schema).ainvoke(
            self._messages(prompt, system)
        )
        return schema.model_validate(result)

    async def astream(
        self, prompt: Prompt, system: Optional[str] = None
    ) -> AsyncIterator[AIMessageChunk]:
        async for chunk in self.chat_model.astream(self._messages(prompt, system)):
            assert isinstance(chunk, AIMessageChunk)
            yield chunk

    @staticmethod
    def _messages(prompt: Prompt, system: Optional[str]) -> list[BaseMessage]:
        messages: list[BaseMessage] = [SystemMessage(system)] if system else []
        if isinstance(prompt, str):
            messages.append(HumanMessage(prompt))
        else:
            messages.extend(prompt)
        return messages
