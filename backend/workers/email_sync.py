from datetime import datetime, timezone
import re
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from backend.auth.google_oauth import get_google_credentials
from backend.db.models import EmailMessage, RecruiterLead
from backend.tools.gmail_reader import GmailReader
from backend.vectorstore.chroma_store import EmailVectorStore


class EmailSyncWorker:
    def __init__(self, db: AsyncSession, vectorstore: EmailVectorStore | None = None) -> None:
        self.db = db
        self.vectorstore = vectorstore or EmailVectorStore()

    async def sync_recent(self, user_id: str, query: str = "newer_than:30d", limit: int = 50) -> int:
        credentials = await get_google_credentials(self.db, user_id)
        reader = GmailReader(credentials)
        messages = await reader.search(query, limit=limit)
        for item in messages:
            received_at = (
                datetime.fromtimestamp(item.received_at_ms / 1000, tz=timezone.utc)
                if item.received_at_ms
                else None
            )
            values = {
                "user_id": user_id,
                "gmail_message_id": item.gmail_message_id,
                "thread_id": item.thread_id,
                "sender": item.sender,
                "recipients": item.recipients,
                "subject": item.subject,
                "snippet": item.snippet,
                "body_text": item.body_text,
                "labels": item.labels,
                "received_at": received_at,
                "is_unread": "UNREAD" in item.labels,
                "classification": classification_for(item.subject, item.snippet, item.body_text),
                "urgency_score": urgency_for(item.subject, item.snippet, item.body_text),
            }
            statement = insert(EmailMessage).values(**values)
            await self.db.execute(
                statement.on_conflict_do_update(
                    index_elements=["user_id", "gmail_message_id"],
                    set_={key: statement.excluded[key] for key in values if key not in {"user_id", "gmail_message_id"}},
                )
            )
            await self.vectorstore.upsert_email(
                user_id=str(user_id),
                message_id=item.gmail_message_id,
                document=f"{item.subject}\n{item.snippet}\n{item.body_text[:4000]}",
                metadata={"sender": item.sender, "subject": item.subject},
            )
            if values["classification"] in {"recruiter", "interview", "oa", "urgent"}:
                lead_values = {
                    "user_id": user_id,
                    "company": company_for(item.sender),
                    "role": role_for(item.subject, item.snippet, item.body_text),
                    "status": status_for(values["classification"]),
                    "recruiter_email": email_address_for(item.sender),
                    "notes": item.snippet,
                    "source_message_id": item.gmail_message_id,
                    "updated_at": datetime.now(timezone.utc),
                }
                lead_statement = insert(RecruiterLead).values(**lead_values)
                await self.db.execute(
                    lead_statement.on_conflict_do_update(
                        index_elements=["user_id", "source_message_id"],
                        set_={key: lead_statement.excluded[key] for key in lead_values if key not in {"user_id", "source_message_id"}},
                    )
                )
        await self.db.commit()
        return len(messages)


def classification_for(subject: str, snippet: str, body: str) -> str:
    text = f"{subject} {snippet} {body}".lower()
    if any(term in text for term in ["interview", "availability", "schedule a call", "technical screen"]):
        return "interview"
    if any(term in text for term in ["online assessment", "coding assessment", "oa", "hackerrank", "codesignal"]):
        return "oa"
    if any(term in text for term in ["recruiter", "talent", "application", "new grad", "intern"]):
        return "recruiter"
    if any(term in text for term in ["urgent", "deadline", "expires", "due today", "final reminder"]):
        return "urgent"
    return "general"


def urgency_for(subject: str, snippet: str, body: str) -> int:
    text = f"{subject} {snippet} {body}".lower()
    score = 25
    if any(term in text for term in ["urgent", "deadline", "expires", "due today", "final reminder"]):
        score += 45
    if any(term in text for term in ["interview", "availability", "online assessment", "coding assessment"]):
        score += 35
    if any(term in text for term in ["tomorrow", "24 hours", "48 hours", "within 5 days"]):
        score += 20
    return min(score, 100)


def company_for(sender: str) -> str:
    match = re.search(r"@([A-Za-z0-9.-]+)", sender)
    if not match:
        return sender.split("<", 1)[0].strip() or "Unknown"
    domain = match.group(1).split(".")
    company = domain[-2] if len(domain) > 1 else domain[0]
    return company.replace("-", " ").title()


def email_address_for(sender: str) -> str:
    match = re.search(r"[\w.+-]+@[\w.-]+", sender)
    return match.group(0) if match else ""


def role_for(subject: str, snippet: str, body: str) -> str:
    text = f"{subject} {snippet} {body}"
    patterns = [
        r"((?:software|backend|frontend|full.?stack|machine learning|data|ai|sde)[\w\s-]{0,40}(?:engineer|intern|developer|role|position))",
        r"((?:new grad|internship|intern)[\w\s-]{0,40})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return " ".join(match.group(1).split()).title()
    return ""


def status_for(classification: str) -> str:
    return {"interview": "interview", "oa": "oa_pending", "urgent": "follow-up"}.get(classification, "new")
