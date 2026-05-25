from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models import EmailMessage
from backend.services.llm.model_router import ModelRouter, ModelTask


class DailyDigestWorker:
    def __init__(self, db: AsyncSession, router: ModelRouter | None = None) -> None:
        self.db = db
        self.router = router or ModelRouter()

    async def generate(self, user_id: str) -> str:
        emails = (
            await self.db.scalars(
                select(EmailMessage)
                .where(EmailMessage.user_id == user_id)
                .order_by(EmailMessage.urgency_score.desc(), EmailMessage.received_at.desc().nullslast())
                .limit(20)
            )
        ).all()
        digest_input = "\n\n".join(f"{email.sender}\n{email.subject}\n{email.snippet}" for email in emails)
        return await self.router.provider.complete(
            model=self.router.model_for(ModelTask.SUMMARY),
            messages=[
                {"role": "system", "content": "Create a daily AI email digest with urgent tasks and interview reminders."},
                {"role": "user", "content": digest_input or "No emails synced yet."},
            ],
        )
