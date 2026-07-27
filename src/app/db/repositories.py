from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models import (
    DocumentRecord,
    FindingRecord,
    ReviewEventRecord,
    ReviewRecord,
)
from app.domain.enums import ReviewStatus
from app.domain.schemas import ContractFinding, DocumentResponse, ReviewResponse


class DocumentRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def find_by_hash(self, sha256: str) -> DocumentRecord | None:
        return self.session.scalar(select(DocumentRecord).where(DocumentRecord.sha256 == sha256))

    def get(self, document_id: UUID) -> DocumentRecord | None:
        return self.session.get(DocumentRecord, document_id)

    def list(self, limit: int = 50) -> list[DocumentRecord]:
        statement = select(DocumentRecord).order_by(DocumentRecord.created_at.desc()).limit(limit)
        return list(self.session.scalars(statement))

    def add(self, record: DocumentRecord) -> DocumentRecord:
        self.session.add(record)
        self.session.commit()
        self.session.refresh(record)
        return record


class ReviewRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add(self, record: ReviewRecord) -> ReviewRecord:
        self.session.add(record)
        self.session.commit()
        return self.get(record.id)

    def get(self, review_id: UUID) -> ReviewRecord | None:
        statement = (
            select(ReviewRecord)
            .options(
                selectinload(ReviewRecord.document),
                selectinload(ReviewRecord.findings),
                selectinload(ReviewRecord.events),
            )
            .where(ReviewRecord.id == review_id)
        )
        return self.session.scalar(statement)

    def list(self, limit: int = 50) -> list[ReviewRecord]:
        statement = (
            select(ReviewRecord)
            .options(
                selectinload(ReviewRecord.document),
                selectinload(ReviewRecord.findings),
            )
            .order_by(ReviewRecord.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(statement))

    def add_event(
        self,
        review: ReviewRecord,
        event_type: str,
        message: str,
        payload: dict | None = None,
    ) -> None:
        review.events.append(
            ReviewEventRecord(
                event_type=event_type,
                message=message,
                payload_json=json.dumps(payload or {}),
            )
        )
        self.session.commit()

    def save_result(
        self,
        review: ReviewRecord,
        *,
        summary: str,
        overall_risk: str,
        missing_clauses: list[str],
        review_notes: list[str],
        findings: list[ContractFinding],
    ) -> ReviewRecord:
        review.summary = summary
        review.overall_risk = overall_risk
        review.missing_clauses_json = json.dumps(missing_clauses)
        review.review_notes_json = json.dumps(review_notes)
        review.status = ReviewStatus.NEEDS_REVIEW
        review.completed_at = datetime.now(UTC)

        review.findings.clear()
        review.findings.extend(
            FindingRecord(
                clause_type=item.clause_type,
                risk_level=item.risk_level,
                title=item.title,
                explanation=item.explanation,
                evidence=item.evidence,
                recommendation=item.recommendation,
                page_number=item.page_number,
                confidence=item.confidence,
            )
            for item in findings
        )
        self.session.commit()
        return self.get(review.id)

    def set_status(
        self,
        review: ReviewRecord,
        status: ReviewStatus,
        *,
        notes: str | None = None,
    ) -> ReviewRecord:
        review.status = status
        if notes is not None:
            review.decision_notes = notes
        self.session.commit()
        return self.get(review.id)


def to_document_response(record: DocumentRecord) -> DocumentResponse:
    return DocumentResponse(
        id=record.id,
        file_name=record.file_name,
        content_type=record.content_type,
        size_bytes=record.size_bytes,
        page_count=record.page_count,
        parser=record.parser,
        status=record.status,
        created_at=record.created_at,
    )


def to_review_response(record: ReviewRecord) -> ReviewResponse:
    return ReviewResponse(
        id=record.id,
        document_id=record.document_id,
        document_name=record.document.file_name,
        jurisdiction=record.jurisdiction,
        engine=record.engine,
        status=record.status,
        summary=record.summary,
        overall_risk=record.overall_risk,
        missing_clauses=json.loads(record.missing_clauses_json),
        review_notes=json.loads(record.review_notes_json),
        findings=[
            {
                "id": finding.id,
                "clause_type": finding.clause_type,
                "risk_level": finding.risk_level,
                "title": finding.title,
                "explanation": finding.explanation,
                "evidence": finding.evidence,
                "recommendation": finding.recommendation,
                "page_number": finding.page_number,
                "confidence": finding.confidence,
            }
            for finding in record.findings
        ],
        decision_notes=record.decision_notes,
        created_at=record.created_at,
        completed_at=record.completed_at,
    )
