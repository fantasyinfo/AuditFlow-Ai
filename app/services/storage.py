import os
import shutil
import uuid
from pathlib import Path
from typing import Protocol

from app.config import get_settings

settings = get_settings()


class StorageBackend(Protocol):
    """Protocol for pluggable file storage backends (Local disk, S3, MinIO, etc.)."""

    async def save_file(self, tenant_id: uuid.UUID, filename: str, content: bytes) -> str:
        """Save file bytes and return storage path / key."""
        ...

    def get_file(self, storage_path: str) -> bytes:
        """Retrieve file bytes given a storage path / key."""
        ...

    def delete_file(self, storage_path: str) -> bool:
        """Delete file given a storage path / key."""
        ...


class LocalStorageBackend:
    """Local filesystem storage backend, saving files under UPLOAD_DIR/<tenant_id>/."""

    def __init__(self, base_dir: str = settings.UPLOAD_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_file(self, tenant_id: uuid.UUID, filename: str, content: bytes) -> str:
        tenant_dir = self.base_dir / str(tenant_id)
        tenant_dir.mkdir(parents=True, exist_ok=True)

        # Unique file name to prevent collision
        unique_prefix = uuid.uuid4().hex[:12]
        safe_filename = f"{unique_prefix}_{filename}"
        target_path = tenant_dir / safe_filename

        with open(target_path, "wb") as f:
            f.write(content)

        return str(target_path)

    def get_file(self, storage_path: str) -> bytes:
        with open(storage_path, "rb") as f:
            return f.read()

    def delete_file(self, storage_path: str) -> bool:
        path = Path(storage_path)
        if path.exists():
            path.unlink()
            return True
        return False


# Global default storage provider instance
storage_backend = LocalStorageBackend()
