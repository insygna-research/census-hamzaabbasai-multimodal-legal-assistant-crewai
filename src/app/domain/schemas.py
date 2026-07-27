from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import ReviewDecision, ReviewStatus, RiskLevel


class ParsedPage(BaseModel):
    page_number: int
    markdown: str
    confidence: float | None = None
    blocks: list[dict] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    pages: list[ParsedPage]
    parser: str

    @property
    def text(self) -> str:
        return "\n\n".join(
            f"[Page {page.page_number}]\n{page.markdown.strip()}" for page in self.pages
        )


class ContractFinding(BaseModel):
    clause_type: str = Field(min_length=2, max_length=80)
    risk_level: RiskLevel
    title: str = Field(min_length=3, max_length=140)
    explanation: str = Field(min_length=10)
    evidence: str = Field(min_length=3)
    recommendation: str = Field(min_length=5)
    page_number: int | None = Field(default=None, ge=1)
    confidence: float = Field(ge=0, le=1)


class ReviewResult(BaseModel):
    summary: str
    overall_risk: RiskLevel
    findings: list[ContractFinding] = Field(default_factory=list)
    missing_clauses: list[str] = Field(default_factory=list)
    review_notes: list[str] = Field(default_factory=list)
    review_engine: str


class DocumentResponse(BaseModel):
    id: UUID
    file_name: str
    content_type: str
    size_bytes: int
    page_count: int
    parser: str
    status: str
    created_at: datetime


class ReviewCreate(BaseModel):
    document_id: UUID
    jurisdiction: str = Field(default="EU", min_length=2, max_length=50)


class FindingResponse(ContractFinding):
    id: UUID


class ReviewResponse(BaseModel):
    id: UUID
    document_id: UUID
    document_name: str
    jurisdiction: str
    engine: str
    status: ReviewStatus
    summary: str | None
    overall_risk: RiskLevel | None
    missing_clauses: list[str] = Field(default_factory=list)
    review_notes: list[str] = Field(default_factory=list)
    findings: list[FindingResponse] = Field(default_factory=list)
    decision_notes: str | None = None
    created_at: datetime
    completed_at: datetime | None = None


class ReviewDecisionRequest(BaseModel):
    decision: ReviewDecision
    notes: str = Field(default="", max_length=1000)


class EvaluationScore(BaseModel):
    runner: str
    precision: float
    recall: float
    citation_rate: float
    average_latency_ms: float
    cases: int
    errors: list[str] = Field(default_factory=list)


class EvaluationResponse(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    score: EvaluationScore
