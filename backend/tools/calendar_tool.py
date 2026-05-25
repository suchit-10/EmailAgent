from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class CalendarTool:
    def __init__(self, credentials: Credentials):
        self.service = build("calendar", "v3", credentials=credentials, cache_discovery=False)

    async def create_event(
        self,
        *,
        summary: str,
        start_at: datetime,
        end_at: datetime,
        attendees: list[str],
        description: str = "",
    ) -> dict:
        event = {
            "summary": summary,
            "description": description,
            "start": {"dateTime": start_at.isoformat()},
            "end": {"dateTime": end_at.isoformat()},
            "attendees": [{"email": email} for email in attendees],
        }
        return self.service.events().insert(calendarId="primary", body=event).execute()
