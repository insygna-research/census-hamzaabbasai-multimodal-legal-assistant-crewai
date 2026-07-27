import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import DocumentRecord
from app.db.repositories import DocumentRepository
from app.services.document_parser import DocumentParser
from app.services.storage import FileStorage


class DocumentService:
    def __init__(self, settings: Settings, session: Session) -> None:
        self.settings = settings
        self.repository = DocumentRepository(session)
        self.parser = DocumentParser(settings)
        self.storage = FileStorage(settings)

    def ingest(self, file_name: str, content_type: str, content: bytes) -> DocumentRecord:
        digest = hashlib.sha256(content).hexdigest()
        existing = self.repository.find_by_hash(digest)
        if existing:
            return existing

        parsed = self.parser.parse(file_name, content_type, content)
        path, saved_digest = self.storage.save(file_name, content)
        record = DocumentRecord(
            file_name=Path(file_name).name,
            content_type=content_type,
            size_bytes=len(content),
            sha256=saved_digest,
            storage_path=str(path),
            extracted_text=parsed.text,
            extraction_json=parsed.model_dump_json(),
            page_count=len(parsed.pages),
            parser=parsed.parser,
            status="ready",
        )
        return self.repository.add(record)
