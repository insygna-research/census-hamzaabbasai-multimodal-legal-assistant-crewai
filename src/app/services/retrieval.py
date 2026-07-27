import hashlib
import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID, uuid5

from mistralai import Mistral
from qdrant_client import QdrantClient, models

from app.core.config import Settings

PAGE_PATTERN = re.compile(r"(?im)^\[page (\d+)\]\s*$")


@dataclass(frozen=True)
class SearchHit:
    text: str
    page_number: int
    score: float


@dataclass(frozen=True)
class ContractChunk:
    text: str
    page_number: int


class MistralEmbedder:
    def __init__(
        self,
        settings: Settings,
        client: Any | None = None,
        batch_size: int = 32,
    ) -> None:
        if not settings.mistral_api_key and client is None:
            raise ValueError("MISTRAL_API_KEY is required for contract search")
        self.client = client or Mistral(api_key=settings.mistral_api_key)
        self.model = settings.mistral_embedding_model
        self.batch_size = batch_size

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for start in range(0, len(texts), self.batch_size):
            batch = texts[start : start + self.batch_size]
            response = self.client.embeddings.create(model=self.model, inputs=batch)
            data = sorted(response.data, key=lambda item: item.index or 0)
            batch_vectors = [item.embedding for item in data if item.embedding is not None]
            if len(batch_vectors) != len(batch):
                raise ValueError("Mistral returned an incomplete embedding response")
            vectors.extend(batch_vectors)
        return vectors


class ContractSearch:
    def __init__(
        self,
        settings: Settings,
        document_id: UUID,
        text: str,
        *,
        mistral_client: Any | None = None,
        qdrant_client: QdrantClient | None = None,
    ) -> None:
        self.settings = settings
        self.document_id = document_id
        self.chunks = _build_chunks(text)
        self.embedder = MistralEmbedder(settings, mistral_client)
        self.qdrant = qdrant_client or QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
            timeout=10,
            check_compatibility=False,
        )
        self.collection_name = _collection_name(settings, document_id)
        self._index_contract()

    def search(self, query: str) -> list[SearchHit]:
        clean_query = query.strip()
        if not clean_query:
            return []

        query_vector = self.embedder.embed([clean_query])[0]
        response = self.qdrant.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=self.settings.retrieval_top_k,
            score_threshold=self.settings.retrieval_score_threshold,
            with_payload=True,
        )
        hits = []
        for point in response.points:
            payload = point.payload or {}
            text = payload.get("text")
            page_number = payload.get("page_number")
            if not isinstance(text, str) or not isinstance(page_number, int):
                continue
            hits.append(
                SearchHit(
                    text=text,
                    page_number=page_number,
                    score=float(point.score),
                )
            )
        return hits

    def search_text(self, query: str) -> str:
        hits = self.search(query)
        if not hits:
            return "No relevant evidence was found."
        return "\n\n".join(
            f"Source {number} · Page {hit.page_number}\n{hit.text}\nSimilarity: {hit.score:.3f}"
            for number, hit in enumerate(hits, start=1)
        )

    def _index_contract(self) -> None:
        vectors = self.embedder.embed([chunk.text for chunk in self.chunks])
        if not vectors:
            raise ValueError("The contract did not produce searchable chunks")

        if not self.qdrant.collection_exists(self.collection_name):
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=len(vectors[0]),
                    distance=models.Distance.COSINE,
                ),
            )

        points = [
            models.PointStruct(
                id=str(uuid5(self.document_id, f"chunk:{index}")),
                vector=vector,
                payload={
                    "document_id": str(self.document_id),
                    "page_number": chunk.page_number,
                    "chunk_index": index,
                    "text": chunk.text,
                },
            )
            for index, (chunk, vector) in enumerate(zip(self.chunks, vectors, strict=True))
        ]
        self.qdrant.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )


def _collection_name(settings: Settings, document_id: UUID) -> str:
    prefix = re.sub(r"[^a-zA-Z0-9_-]", "_", settings.qdrant_collection_prefix)[:40]
    model_hash = hashlib.sha1(
        settings.mistral_embedding_model.encode("utf-8"),
        usedforsecurity=False,
    ).hexdigest()[:8]
    return f"{prefix}_{document_id.hex[:12]}_{model_hash}"


def _build_chunks(text: str, max_chars: int = 1400, overlap: int = 160) -> list[ContractChunk]:
    page_matches = list(PAGE_PATTERN.finditer(text))
    pages: list[tuple[int, str]] = []

    if not page_matches:
        pages.append((1, text))
    else:
        for index, match in enumerate(page_matches):
            start = match.end()
            end = page_matches[index + 1].start() if index + 1 < len(page_matches) else len(text)
            pages.append((int(match.group(1)), text[start:end]))

    chunks = []
    for page_number, page_text in pages:
        for part in _split_text(page_text, max_chars, overlap):
            chunks.append(ContractChunk(text=part, page_number=page_number))
    return chunks


def _split_text(text: str, max_chars: int, overlap: int) -> list[str]:
    clean_text = text.strip()
    if not clean_text:
        return []

    parts = []
    start = 0
    while start < len(clean_text):
        end = min(start + max_chars, len(clean_text))
        if end < len(clean_text):
            boundary = clean_text.rfind("\n", start, end)
            if boundary <= start:
                boundary = clean_text.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        part = clean_text[start:end].strip()
        if part:
            parts.append(part)
        if end >= len(clean_text):
            break
        start = max(end - overlap, start + 1)
    return parts
