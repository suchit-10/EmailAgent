from enum import StrEnum
from backend.services.llm.base_provider import LLMProvider
from backend.services.llm.groq_provider import GroqProvider


class ModelTask(StrEnum):
    SUMMARY = "summary"
    PLANNING = "planning"
    FINAL_RESPONSE = "final_response"
    CLASSIFICATION = "classification"
    EXTRACTION = "extraction"


class ModelRouter:
    model_map = {
        ModelTask.SUMMARY: "llama-3.3-70b-versatile",
        ModelTask.PLANNING: "llama-3.3-70b-versatile",
        ModelTask.FINAL_RESPONSE: "llama-3.3-70b-versatile",
        ModelTask.CLASSIFICATION: "llama-3.3-70b-versatile",
        ModelTask.EXTRACTION: "llama-3.3-70b-versatile",
    }

    def __init__(self, provider: LLMProvider | None = None) -> None:
        self.provider = provider or GroqProvider()

    def model_for(self, task: ModelTask) -> str:
        return self.model_map[task]
