from fastapi import APIRouter, Depends

from app.api.dependencies import get_app_settings
from app.core.config import Settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health(settings: Settings = Depends(get_app_settings)) -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "orchestrator": "crewai",
        "model": settings.model_name,
        "vector_store": "qdrant",
    }
