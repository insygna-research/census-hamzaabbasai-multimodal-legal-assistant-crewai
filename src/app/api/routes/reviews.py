from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_app_settings, get_db
from app.core.config import Settings
from app.db.repositories import ReviewRepository, to_review_response
from app.domain.schemas import (
    ReviewCreate,
    ReviewDecisionRequest,
    ReviewResponse,
)
from app.services.reports import build_markdown_report
from app.services.reviews import (
    DocumentNotFoundError,
    ReviewNotFoundError,
    ReviewService,
)

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("", response_model=list[ReviewResponse])
def list_reviews(db: Session = Depends(get_db)) -> list[ReviewResponse]:
    return [to_review_response(record) for record in ReviewRepository(db).list()]


@router.get("/{review_id}", response_model=ReviewResponse)
def get_review(review_id: UUID, db: Session = Depends(get_db)) -> ReviewResponse:
    review = ReviewRepository(db).get(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review was not found")
    return to_review_response(review)


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    payload: ReviewCreate,
    settings: Settings = Depends(get_app_settings),
    db: Session = Depends(get_db),
) -> ReviewResponse:
    try:
        review = ReviewService(settings, db).create(
            payload.document_id,
            payload.jurisdiction,
        )
    except DocumentNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(status_code=502, detail=f"Review failed: {error}") from error
    return to_review_response(review)


@router.post("/{review_id}/decision", response_model=ReviewResponse)
def decide_review(
    review_id: UUID,
    payload: ReviewDecisionRequest,
    settings: Settings = Depends(get_app_settings),
    db: Session = Depends(get_db),
) -> ReviewResponse:
    try:
        review = ReviewService(settings, db).decide(
            review_id,
            payload.decision,
            payload.notes,
        )
    except ReviewNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    return to_review_response(review)


@router.get("/{review_id}/report")
def download_report(review_id: UUID, db: Session = Depends(get_db)) -> Response:
    review = ReviewRepository(db).get(review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review was not found")
    report = build_markdown_report(review)
    return Response(
        content=report,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="contract-review-{review_id}.md"'},
    )
