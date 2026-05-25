import re
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.db.models import EmailMessage


class GmailSearchTool:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def keyword_search(self, user_id: str, query: str, limit: int = 10) -> list[EmailMessage]:
        terms = [term.strip() for term in re.split(r"\s+OR\s+|\s*,\s*", query, flags=re.IGNORECASE) if term.strip()]
        conditions = []
        for term in terms or [query]:
            pattern = f"%{term}%"
            conditions.append(
                EmailMessage.subject.ilike(pattern)
                | EmailMessage.sender.ilike(pattern)
                | EmailMessage.body_text.ilike(pattern)
                | EmailMessage.snippet.ilike(pattern)
                | EmailMessage.classification.ilike(pattern)
            )
        stmt = (
            select(EmailMessage)
            .where(EmailMessage.user_id == user_id)
            .where(or_(*conditions))
            .order_by(EmailMessage.received_at.desc().nullslast())
            .limit(limit)
        )
        return list((await self.db.scalars(stmt)).all())
