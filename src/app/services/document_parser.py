from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.core.config import Settings
from app.domain.schemas import ParsedDocument, ParsedPage
from app.services.mistral_ocr import MistralOCR


class UnsupportedDocumentError(ValueError):
    pass


class DocumentParser:
    text_types = {"text/plain", "text/markdown"}
    supported_suffixes = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".txt", ".md"}

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def parse(self, file_name: str, content_type: str, content: bytes) -> ParsedDocument:
        suffix = Path(file_name).suffix.lower()
        if suffix not in self.supported_suffixes:
            raise UnsupportedDocumentError(f"{suffix or 'This file type'} is not supported")

        if content_type in self.text_types or suffix in {".txt", ".md"}:
            text = content.decode("utf-8", errors="replace").strip()
            if not text:
                raise UnsupportedDocumentError("The document does not contain readable text")
            return ParsedDocument(
                pages=[ParsedPage(page_number=1, markdown=text, confidence=1.0)],
                parser="plain-text",
            )

        if suffix == ".pdf":
            parsed = self._read_pdf_text(content)
            if parsed:
                return parsed

        if not self.settings.mistral_api_key:
            raise UnsupportedDocumentError(
                "A Mistral API key is required for scanned PDFs and images"
            )

        return MistralOCR(self.settings).parse(content, content_type)

    @staticmethod
    def _read_pdf_text(content: bytes) -> ParsedDocument | None:
        reader = PdfReader(BytesIO(content))
        pages = []
        readable_characters = 0
        for page_number, page in enumerate(reader.pages, start=1):
            text = (page.extract_text() or "").strip()
            readable_characters += len(text)
            pages.append(ParsedPage(page_number=page_number, markdown=text, confidence=1.0))

        if readable_characters < max(80, len(pages) * 40):
            return None
        return ParsedDocument(pages=pages, parser="pypdf")
