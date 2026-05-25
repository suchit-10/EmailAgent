from dataclasses import dataclass
from email.mime.text import MIMEText
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


@dataclass
class GmailMessage:
    gmail_message_id: str
    thread_id: str
    sender: str
    recipients: list[str]
    subject: str
    snippet: str
    body_text: str
    labels: list[str]
    received_at_ms: int | None


def _header(payload: dict, name: str) -> str:
    for item in payload.get("headers", []):
        if item.get("name", "").lower() == name.lower():
            return item.get("value", "")
    return ""


def _decode_body(payload: dict) -> str:
    data = payload.get("body", {}).get("data")
    if data:
        return base64.urlsafe_b64decode(data + "===" ).decode(errors="ignore")
    for part in payload.get("parts", []) or []:
        if part.get("mimeType") == "text/plain":
            pdata = part.get("body", {}).get("data", "")
            if pdata:
                return base64.urlsafe_b64decode(pdata + "===" ).decode(errors="ignore")
    return ""


class GmailReader:
    def __init__(self, credentials: Credentials):
        self.service = build("gmail", "v1", credentials=credentials, cache_discovery=False)

    async def search(self, query: str, limit: int = 10) -> list[GmailMessage]:
        result = self.service.users().messages().list(userId="me", q=query, maxResults=limit).execute()
        messages = result.get("messages", [])
        return [self.get_message(item["id"]) for item in messages]

    def get_message(self, message_id: str) -> GmailMessage:
        raw = self.service.users().messages().get(userId="me", id=message_id, format="full").execute()
        payload = raw.get("payload", {})
        recipients = [value.strip() for value in _header(payload, "To").split(",") if value.strip()]
        return GmailMessage(
            gmail_message_id=raw["id"],
            thread_id=raw.get("threadId", ""),
            sender=_header(payload, "From"),
            recipients=recipients,
            subject=_header(payload, "Subject"),
            snippet=raw.get("snippet", ""),
            body_text=_decode_body(payload),
            labels=raw.get("labelIds", []),
            received_at_ms=int(raw["internalDate"]) if raw.get("internalDate") else None,
        )


def build_raw_email(to: list[str], subject: str, body: str) -> str:
    message = MIMEText(body)
    message["to"] = ", ".join(to)
    message["subject"] = subject
    return base64.urlsafe_b64encode(message.as_bytes()).decode()
