import hashlib
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings


class FileStorage:
    def __init__(self, settings: Settings) -> None:
        self.root = settings.upload_dir
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, file_name: str, content: bytes) -> tuple[Path, str]:
        safe_name = Path(file_name).name.replace(" ", "_")
        target = self.root / f"{uuid4().hex}_{safe_name}"
        target.write_bytes(content)
        return target, hashlib.sha256(content).hexdigest()
