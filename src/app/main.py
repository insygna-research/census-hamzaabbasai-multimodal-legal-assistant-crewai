from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, evaluations, health, reviews
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db import Database


def create_app(settings: Settings | None = None) -> FastAPI:
    active_settings = settings or get_settings()
    project_root = Path(__file__).resolve().parents[2]

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        active_settings.prepare_local_dirs()
        app.state.database.create_tables()
        yield

    configure_logging()
    app = FastAPI(
        title=active_settings.app_name,
        version="0.1.0",
        description="Evidence-first contract risk and compliance review",
        lifespan=lifespan,
    )
    app.state.settings = active_settings
    app.state.database = Database(active_settings.database_url)
    app.state.sample_contract = project_root / "sample-data" / "vendor-agreement.txt"
    app.state.evaluation_dataset = project_root / "sample-data" / "evaluation-set.json"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[active_settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router, prefix=active_settings.api_prefix)
    app.include_router(documents.router, prefix=active_settings.api_prefix)
    app.include_router(reviews.router, prefix=active_settings.api_prefix)
    app.include_router(evaluations.router, prefix=active_settings.api_prefix)
    return app


app = create_app()
