from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.api.deps import current_user_id, db_session
from backend.db.models import EmailMessage, RecruiterLead


router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/overview")
async def overview(user_id: str = Depends(current_user_id), db: AsyncSession = Depends(db_session)) -> dict:
    unread = await db.scalar(select(func.count()).select_from(EmailMessage).where(EmailMessage.user_id == user_id, EmailMessage.is_unread.is_(True)))
    urgent = await db.scalar(select(func.count()).select_from(EmailMessage).where(EmailMessage.user_id == user_id, EmailMessage.urgency_score >= 75))
    recruiters = await db.scalar(select(func.count()).select_from(RecruiterLead).where(RecruiterLead.user_id == user_id))
    leads = (await db.scalars(select(RecruiterLead).where(RecruiterLead.user_id == user_id).order_by(RecruiterLead.updated_at.desc()).limit(8))).all()
    return {
        "unread": unread or 0,
        "urgent": urgent or 0,
        "recruiters": recruiters or 0,
        "leads": [
            {"company": lead.company, "role": lead.role, "status": lead.status, "interview_at": lead.interview_at}
            for lead in leads
        ],
    }
