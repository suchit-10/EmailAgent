from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from backend.tools.gmail_reader import build_raw_email


class GmailSender:
    def __init__(self, credentials: Credentials):
        self.service = build("gmail", "v1", credentials=credentials, cache_discovery=False)

    async def create_draft(self, to: list[str], subject: str, body: str) -> dict:
        raw = build_raw_email(to, subject, body)
        return self.service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()

    async def send(self, to: list[str], subject: str, body: str) -> dict:
        raw = build_raw_email(to, subject, body)
        return self.service.users().messages().send(userId="me", body={"raw": raw}).execute()
