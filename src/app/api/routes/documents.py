from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_app_settings, get_db
from app.core.config import Settings
from app.db.repositories import DocumentRepository, to_document_response
from app.domain.schemas import DocumentResponse
from app.services.document_parser import UnsupportedDocumentError
from app.services.documents import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentResponse]:
    records = DocumentRepository(db).list()
    return [to_document_response(record) for record in records]


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    settings: Settings = Depends(get_app_settings),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    content = await file.read(settings.max_upload_bytes + 1)
    if not content:
        raise HTTPException(status_code=400, detail="The uploaded file is empty")
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"The file is larger than {settings.max_upload_mb} MB",
        )

    try:
        record = DocumentService(settings, db).ingest(
            file.filename or "contract",
            file.content_type or "application/octet-stream",
            content,
        )
    except UnsupportedDocumentError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    return to_document_response(record)


@router.post("/sample", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def load_sample_document(
    request: Request,
    settings: Settings = Depends(get_app_settings),
    db: Session = Depends(get_db),
) -> DocumentResponse:
    sample_path: Path = request.app.state.sample_contract
    content = sample_path.read_bytes()
    record = DocumentService(settings, db).ingest(
        sample_path.name,
        "text/plain",
        content,
    )
    return to_document_response(record)
