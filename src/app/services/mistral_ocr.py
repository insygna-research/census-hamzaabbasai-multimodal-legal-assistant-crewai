import base64
import inspect

from mistralai import Mistral

from app.core.config import Settings
from app.domain.schemas import ParsedDocument, ParsedPage


class MistralOCR:
    def __init__(self, settings: Settings) -> None:
        if not settings.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY is required for scanned documents")
        self.client = Mistral(api_key=settings.mistral_api_key)
        self.model = settings.mistral_ocr_model

    def parse(self, content: bytes, content_type: str) -> ParsedDocument:
        encoded = base64.b64encode(content).decode("ascii")
        source_type = "image_url" if content_type.startswith("image/") else "document_url"
        source_key = "image_url" if source_type == "image_url" else "document_url"
        data_url = f"data:{content_type};base64,{encoded}"

        request = {
            "model": self.model,
            "document": {"type": source_type, source_key: data_url},
            "table_format": "markdown",
            "include_image_base64": False,
        }
        supported_parameters = inspect.signature(self.client.ocr.process).parameters
        if "include_blocks" in supported_parameters:
            request["include_blocks"] = True
        if "confidence_scores_granularity" in supported_parameters:
            request["confidence_scores_granularity"] = "page"

        response = self.client.ocr.process(
            **request,
        )

        pages = []
        for page in response.pages:
            confidence = None
            confidence_scores = getattr(page, "confidence_scores", None)
            if confidence_scores:
                confidence = confidence_scores.average_page_confidence_score
            blocks = [
                block.model_dump() if hasattr(block, "model_dump") else dict(block)
                for block in (getattr(page, "blocks", None) or [])
            ]
            pages.append(
                ParsedPage(
                    page_number=page.index + 1,
                    markdown=page.markdown,
                    confidence=confidence,
                    blocks=blocks,
                )
            )
        return ParsedDocument(pages=pages, parser=self.model)
