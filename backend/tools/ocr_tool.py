from pathlib import Path
from PIL import Image
import pytesseract


class OCRTool:
    def extract_text(self, path: str | Path) -> str:
        return pytesseract.image_to_string(Image.open(path)).strip()
