from pathlib import Path

from fastapi import APIRouter, Depends, Request

from app.api.dependencies import get_app_settings
from app.core.config import Settings
from app.domain.schemas import EvaluationResponse
from app.services.evaluations import EvaluationService

router = APIRouter(prefix="/evaluations", tags=["evaluations"])


@router.post("/run", response_model=EvaluationResponse)
def run_evaluation(
    request: Request,
    settings: Settings = Depends(get_app_settings),
) -> EvaluationResponse:
    dataset_path: Path = request.app.state.evaluation_dataset
    return EvaluationService(settings, dataset_path).run()
