from pathlib import Path
from pypdf import PdfReader


class AttachmentParser:
    def parse_pdf(self, path: str | Path) -> str:
        reader = PdfReader(str(path))
        return "\n".join(page.extract_text() or "" for page in reader.pages).strip()

    def detect_type(self, filename: str, text: str) -> str:
        lower = f"{filename} {text[:1000]}".lower()
        if "resume" in lower or "curriculum vitae" in lower:
            return "resume"
        if "invoice" in lower or "amount due" in lower:
            return "invoice"
        return "document"
