from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class EmailSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    limit: int = Field(default=10, ge=1, le=50)


class EmailSummary(BaseModel):
    id: str
    sender: str
    subject: str
    snippet: str
    labels: list[str] = []
    received_at: datetime | None = None
    urgency_score: int = 0
    classification: str = "general"
    summary: str = ""


class DraftApprovalRequest(BaseModel):
    to: list[EmailStr]
    subject: str
    body: str
    send_now: bool = False


class AgentRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None


class AgentEvent(BaseModel):
    type: str
    content: str
    data: dict = {}
