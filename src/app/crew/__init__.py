import os
from pathlib import Path

os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
crewai_data_dir = Path(os.environ.get("CREWAI_DATA_DIR", "./data/crewai")).resolve()
crewai_data_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("XDG_DATA_HOME", str(crewai_data_dir))

from app.crew.review_flow import execute_review_flow  # noqa: E402

__all__ = ["execute_review_flow"]
