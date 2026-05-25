from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.auth.google_oauth import get_google_credentials
from backend.api.deps import current_user_id, db_session
from backend.schemas.email import DraftApprovalRequest, EmailSearchRequest
from backend.tools.gmail_sender import GmailSender
from backend.tools.gmail_search import GmailSearchTool
from backend.workers.daily_digest import DailyDigestWorker
from backend.workers.email_sync import EmailSyncWorker
from backend.workers.follow_up import FollowUpWorker


router = APIRouter(prefix="/emails", tags=["emails"])


@router.post("/search")
async def search_emails(
    request: EmailSearchRequest,
    user_id: str = Depends(current_user_id),
    db: AsyncSession = Depends(db_session),
) -> dict:
    results = await GmailSearchTool(db).keyword_search(user_id=user_id, query=request.query, limit=request.limit)
    return {
        "items": [
            {
                "id": email.gmail_message_id,
                "from": email.sender,
                "subject": email.subject,
                "snippet": email.snippet,
                "classification": email.classification,
                "urgency": email.urgency_score,
                "received_at": email.received_at,
            }
            for email in results
        ]
    }


@router.post("/drafts/approve")
async def approve_draft(
    request: DraftApprovalRequest,
    user_id: str = Depends(current_user_id),
    db: AsyncSession = Depends(db_session),
) -> dict:
    credentials = await get_google_credentials(db, user_id)
    sender = GmailSender(credentials)
    result = (
        await sender.send(to=[str(address) for address in request.to], subject=request.subject, body=request.body)
        if request.send_now
        else await sender.create_draft(to=[str(address) for address in request.to], subject=request.subject, body=request.body)
    )
    return {
        "status": "sent" if request.send_now else "draft_created",
        "message": "Email sent." if request.send_now else "Gmail draft created.",
        "gmail_id": result.get("id"),
        "user_id": user_id,
    }


@router.post("/sync")
async def sync_recent_emails(user_id: str = Depends(current_user_id), db: AsyncSession = Depends(db_session)) -> dict:
    synced = await EmailSyncWorker(db).sync_recent(user_id=user_id)
    return {"synced": synced}


@router.post("/digest")
async def daily_digest(user_id: str = Depends(current_user_id), db: AsyncSession = Depends(db_session)) -> dict:
    digest = await DailyDigestWorker(db).generate(user_id=user_id)
    return {"digest": digest}


@router.post("/follow-ups")
async def draft_follow_ups(user_id: str = Depends(current_user_id), db: AsyncSession = Depends(db_session)) -> dict:
    drafted = await FollowUpWorker(db).draft_stale_followups(user_id=user_id)
    return {"drafted": drafted}
