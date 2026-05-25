from uuid import UUID
from typing import Literal, TypedDict
from pydantic import BaseModel, Field


class AgentPlan(BaseModel):
    intent: Literal["search", "summarize", "draft_reply", "send_email", "calendar", "digest", "dashboard", "general"]
    steps: list[str] = Field(default_factory=list)
    requires_approval: bool = False
    search_query: str | None = None
    tone: str = "professional"


class EmailClassification(BaseModel):
    category: Literal["recruiter", "interview", "internship", "rejection", "oa", "urgent", "spam", "general"]
    urgency_score: int = Field(ge=0, le=100)
    company: str | None = None
    role: str | None = None
    deadlines: list[str] = Field(default_factory=list)
    summary: str


class AgentState(TypedDict, total=False):
    user_id: str | UUID
    message: str
    conversation_id: str | None
    plan: AgentPlan
    memories: list[dict]
    emails: list[dict]
    classifications: list[dict]
    draft: dict | None
    calendar_events: list[dict]
    attachments: list[dict]
    final_response: str
    errors: list[str]
