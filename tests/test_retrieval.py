from types import SimpleNamespace
from uuid import uuid4

from qdrant_client import QdrantClient

from app.core.config import Settings
from app.services.retrieval import ContractSearch


def vector_for(text: str) -> list[float]:
    clean_text = text.lower()
    if "liability" in clean_text:
        return [1.0, 0.0, 0.0]
    if "payment" in clean_text:
        return [0.0, 1.0, 0.0]
    return [0.0, 0.0, 1.0]


class FakeEmbeddings:
    def create(self, *, model: str, inputs: list[str]):
        data = [
            SimpleNamespace(index=index, embedding=vector_for(text))
            for index, text in enumerate(inputs)
        ]
        return SimpleNamespace(data=data)


class FakeMistral:
    def __init__(self) -> None:
        self.embeddings = FakeEmbeddings()


def build_search(text: str) -> ContractSearch:
    settings = Settings(
        qdrant_url=":memory:",
        retrieval_top_k=2,
        retrieval_score_threshold=0.2,
    )
    return ContractSearch(
        settings,
        uuid4(),
        text,
        mistral_client=FakeMistral(),
        qdrant_client=QdrantClient(":memory:"),
    )


def test_contract_search_returns_the_matching_page() -> None:
    text = (
        "[Page 1]\nPayment is due within 30 days.\n\n"
        "[Page 2]\nThe supplier has unlimited liability for indirect losses."
    )
    search = build_search(text)

    hits = search.search("unlimited liability")

    assert hits
    assert hits[0].page_number == 2
    assert "unlimited liability" in hits[0].text.lower()


def test_contract_search_applies_the_score_threshold() -> None:
    search = build_search("[Page 1]\nPayment is due within 30 days.")

    assert search.search("biometric surveillance") == []
