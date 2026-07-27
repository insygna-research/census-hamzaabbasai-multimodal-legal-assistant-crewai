from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class DocumentRecord(Base):
    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    file_name: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(Integer)
    sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    storage_path: Mapped[str] = mapped_column(String(500))
    extracted_text: Mapped[str] = mapped_column(Text)
    extraction_json: Mapped[str] = mapped_column(Text, default="{}")
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    parser: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="ready")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    reviews: Mapped[list["ReviewRecord"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class ReviewRecord(Base):
    __tablename__ = "reviews"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        index=True,
    )
    jurisdiction: Mapped[str] = mapped_column(String(50))
    engine: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30), default="pending")
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_risk: Mapped[str | None] = mapped_column(String(20), nullable=True)
    missing_clauses_json: Mapped[str] = mapped_column(Text, default="[]")
    review_notes_json: Mapped[str] = mapped_column(Text, default="[]")
    decision_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    document: Mapped[DocumentRecord] = relationship(back_populates="reviews")
    findings: Mapped[list["FindingRecord"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
        order_by="FindingRecord.created_at",
    )
    events: Mapped[list["ReviewEventRecord"]] = relationship(
        back_populates="review",
        cascade="all, delete-orphan",
        order_by="ReviewEventRecord.created_at",
    )


class FindingRecord(Base):
    __tablename__ = "review_findings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    review_id: Mapped[UUID] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"),
        index=True,
    )
    clause_type: Mapped[str] = mapped_column(String(80))
    risk_level: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(140))
    explanation: Mapped[str] = mapped_column(Text)
    evidence: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text)
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    review: Mapped[ReviewRecord] = relationship(back_populates="findings")


class ReviewEventRecord(Base):
    __tablename__ = "review_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    review_id: Mapped[UUID] = mapped_column(
        ForeignKey("reviews.id", ondelete="CASCADE"),
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(50))
    message: Mapped[str] = mapped_column(String(300))
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    review: Mapped[ReviewRecord] = relationship(back_populates="events")
