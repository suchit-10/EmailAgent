from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models import OutboundDraft, RecruiterLead
from backend.services.llm.model_router import ModelRouter, ModelTask


class FollowUpWorker:
    def __init__(self, db: AsyncSession, router: ModelRouter | None = None) -> None:
        self.db = db
        self.router = router or ModelRouter()

    async def draft_stale_followups(self, user_id: str, days: int = 5) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        leads = (
            await self.db.scalars(
                select(RecruiterLead)
                .where(RecruiterLead.user_id == user_id)
                .where(RecruiterLead.updated_at < cutoff)
                .where(RecruiterLead.status.in_(["applied", "interview", "follow-up"]))
            )
        ).all()
        for lead in leads:
            body = await self.router.provider.complete(
                model=self.router.model_for(ModelTask.FINAL_RESPONSE),
                messages=[
                    {"role": "system", "content": "Write a concise, professional recruiting follow-up email."},
                    {"role": "user", "content": f"Company: {lead.company}; Role: {lead.role}; Notes: {lead.notes}"},
                ],
            )
            self.db.add(
                OutboundDraft(
                    user_id=user_id,
                    to=[lead.recruiter_email] if lead.recruiter_email else [],
                    subject=f"Following up on {lead.role or 'my application'}",
                    body=body,
                    draft_metadata={"lead_id": str(lead.id), "autonomous_follow_up": True},
                )
            )
        await self.db.commit()
        return len(leads)
