from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from pydantic import BaseModel


class LLMProvider(ABC):
    @abstractmethod
    async def complete(self, *, model: str, messages: list[dict], temperature: float = 0.2) -> str:
        raise NotImplementedError

    @abstractmethod
    async def stream(self, *, model: str, messages: list[dict], temperature: float = 0.2) -> AsyncIterator[str]:
        raise NotImplementedError

    @abstractmethod
    async def structured(
        self,
        *,
        model: str,
        messages: list[dict],
        schema: type[BaseModel],
        temperature: float = 0,
    ) -> BaseModel:
        raise NotImplementedError
