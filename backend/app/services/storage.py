import os
from abc import ABC, abstractmethod
from pathlib import Path
from app.core.config import settings


class StorageService(ABC):
    @abstractmethod
    def save(self, relative_path: str, content: bytes) -> str:
        """Saves content to the given relative path. Returns absolute or resolved path string."""
        pass

    @abstractmethod
    def read(self, relative_path: str) -> bytes:
        """Reads content from the given relative path."""
        pass

    @abstractmethod
    def delete(self, relative_path: str) -> bool:
        """Deletes file at relative path. Returns True if deleted, False if not found."""
        pass

    @abstractmethod
    def exists(self, relative_path: str) -> bool:
        """Checks if file exists at relative path."""
        pass


class LocalStorage(StorageService):
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or settings.STORAGE_DIR).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, relative_path: str) -> Path:
        clean_rel = relative_path.lstrip("/\\")
        target = (self.base_dir / clean_rel).resolve()
        # Security check against path traversal
        if not str(target).startswith(str(self.base_dir)):
            raise ValueError(f"Path traversal detected: {relative_path}")
        return target

    def save(self, relative_path: str, content: bytes) -> str:
        target_path = self._resolve_path(relative_path)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with open(target_path, "wb") as f:
            f.write(content)
        return str(target_path)

    def read(self, relative_path: str) -> bytes:
        target_path = self._resolve_path(relative_path)
        if not target_path.exists():
            raise FileNotFoundError(f"File not found: {relative_path}")
        with open(target_path, "rb") as f:
            return f.read()

    def delete(self, relative_path: str) -> bool:
        target_path = self._resolve_path(relative_path)
        if target_path.exists():
            os.remove(target_path)
            return True
        return False

    def exists(self, relative_path: str) -> bool:
        target_path = self._resolve_path(relative_path)
        return target_path.exists()
