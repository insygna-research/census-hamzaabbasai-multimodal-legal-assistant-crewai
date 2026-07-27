import pytest

from app.core.config import Settings
from app.services.document_parser import (
    DocumentParser,
    UnsupportedDocumentError,
)


def test_plain_text_parser_adds_page_marker() -> None:
    parser = DocumentParser(Settings())
    result = parser.parse("agreement.txt", "text/plain", b"Payment is due in 30 days.")

    assert result.parser == "plain-text"
    assert result.text.startswith("[Page 1]")
    assert "Payment is due" in result.text


def test_image_parser_requires_a_mistral_key() -> None:
    parser = DocumentParser(Settings())

    with pytest.raises(UnsupportedDocumentError, match="Mistral API key"):
        parser.parse("scan.png", "image/png", b"not-a-real-image")
