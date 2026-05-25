from collections.abc import AsyncIterator
import json
from openai import AsyncOpenAI
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential
from backend.core.config import get_settings
from backend.services.llm.base_provider import LLMProvider


class GroqProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.groq_api_key, base_url=settings.groq_base_url)

    @retry(wait=wait_exponential(multiplier=0.5, max=8), stop=stop_after_attempt(3))
    async def complete(self, *, model: str, messages: list[dict], temperature: float = 0.2) -> str:
        response = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    async def stream(self, *, model: str, messages: list[dict], temperature: float = 0.2) -> AsyncIterator[str]:
        stream = await self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            token = chunk.choices[0].delta.content
            if token:
                yield token

    async def structured(
        self,
        *,
        model: str,
        messages: list[dict],
        schema: type[BaseModel],
        temperature: float = 0,
    ) -> BaseModel:
        schema_json = json.dumps(schema.model_json_schema(), indent=2)
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                *messages,
                {
                    "role": "system",
                    "content": (
                        "Return only a valid JSON object that matches this JSON Schema. "
                        f"Do not wrap it in markdown.\n{schema_json}"
                    ),
                },
            ],
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Model did not return structured output")
        return schema.model_validate_json(content)
