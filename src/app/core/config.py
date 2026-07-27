from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Multimodal Legal Assistant"
    api_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:3000"
    database_url: str = "sqlite:///./data/app.db"
    upload_dir: Path = Path("./data/uploads")
    max_upload_mb: int = Field(default=20, ge=1, le=100)

    model_name: str = "mistral-large-latest"
    mistral_api_key: str | None = None
    mistral_ocr_model: str = "mistral-ocr-latest"
    mistral_embedding_model: str = "mistral-embed"

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection_prefix: str = "legal_contract"
    retrieval_top_k: int = Field(default=6, ge=2, le=20)
    retrieval_score_threshold: float = Field(default=0.2, ge=0, le=1)

    @field_validator("api_prefix")
    @classmethod
    def clean_api_prefix(cls, value: str) -> str:
        return "/" + value.strip("/")

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    def prepare_local_dirs(self) -> None:
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        if self.database_url.startswith("sqlite:///"):
            database_path = Path(self.database_url.removeprefix("sqlite:///"))
            database_path.parent.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
