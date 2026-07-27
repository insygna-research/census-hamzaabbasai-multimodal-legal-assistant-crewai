from uuid import UUID

from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models import ReviewRecord
from app.db.repositories import DocumentRepository, ReviewRepository
from app.domain.enums import ReviewDecision, ReviewStatus
from app.domain.schemas import ReviewResult


def execute_contract_review(
    settings: Settings,
    document_id: UUID,
    document_text: str,
    jurisdiction: str,
) -> ReviewResult:
    from app.crew import execute_review_flow

    return execute_review_flow(
        settings,
        document_id=document_id,
        document_text=document_text,
        jurisdiction=jurisdiction,
    )


class ReviewNotFoundError(LookupError):
    pass


class DocumentNotFoundError(LookupError):
    pass


class ReviewService:
    def __init__(self, settings: Settings, session: Session) -> None:
        self.settings = settings
        self.documents = DocumentRepository(session)
        self.reviews = ReviewRepository(session)

    def create(
        self,
        document_id: UUID,
        jurisdiction: str,
    ) -> ReviewRecord:
        document = self.documents.get(document_id)
        if not document:
            raise DocumentNotFoundError("Document was not found")

        review = self.reviews.add(
            ReviewRecord(
                document_id=document.id,
                jurisdiction=jurisdiction,
                engine="crewai-mistral-qdrant",
                status=ReviewStatus.PENDING,
            )
        )
        self.reviews.add_event(review, "created", "Review was created")
        self.reviews.set_status(review, ReviewStatus.RUNNING)

        try:
            result = execute_contract_review(
                self.settings,
                document.id,
                document.extracted_text,
                jurisdiction,
            )
            review = self.reviews.save_result(
                review,
                summary=result.summary,
                overall_risk=result.overall_risk,
                missing_clauses=result.missing_clauses,
                review_notes=result.review_notes,
                findings=result.findings,
            )
            self.reviews.add_event(
                review,
                "analysis_completed",
                "Analysis completed and needs human review",
                {"finding_count": len(result.findings)},
            )
            return self.reviews.get(review.id)
        except Exception as error:
            self.reviews.set_status(review, ReviewStatus.FAILED, notes=str(error))
            self.reviews.add_event(review, "failed", "Review failed", {"error": str(error)})
            raise

    def decide(
        self,
        review_id: UUID,
        decision: ReviewDecision,
        notes: str,
    ) -> ReviewRecord:
        review = self.reviews.get(review_id)
        if not review:
            raise ReviewNotFoundError("Review was not found")
        if review.status not in {ReviewStatus.NEEDS_REVIEW, ReviewStatus.REJECTED}:
            raise ValueError("Only a completed review can receive a decision")

        status = (
            ReviewStatus.APPROVED if decision == ReviewDecision.APPROVE else ReviewStatus.REJECTED
        )
        review = self.reviews.set_status(review, status, notes=notes)
        self.reviews.add_event(
            review,
            f"human_{decision}",
            f"Human reviewer marked the review as {status}",
            {"notes": notes},
        )
        return self.reviews.get(review.id)
