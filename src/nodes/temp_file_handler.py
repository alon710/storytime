import tempfile
import atexit
from pathlib import Path
from typing import Optional, Literal
from contextlib import contextmanager
import threading


class TempFileHandler:
    """Centralized handler for temporary file management"""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(tempfile.gettempdir()) / "storytime"
        self.base_dir.mkdir(exist_ok=True, parents=True)
        self._temp_files: set[Path] = set()
        self._lock = threading.Lock()
        atexit.register(self.cleanup_all)

    def create_temp_file(
        self,
        suffix: str = ".png",
        prefix: str = "storytime_",
        file_type: Literal["image", "pdf", "text"] = "image"
    ) -> Path:
        """Create a temporary file and track it for cleanup"""
        with self._lock:
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=suffix,
                prefix=f"{prefix}{file_type}_",
                dir=self.base_dir
            )
            temp_path = Path(temp_file.name)
            temp_file.close()
            self._temp_files.add(temp_path)
            return temp_path

    def write_bytes(self, data: bytes, suffix: str = ".png", prefix: str = "storytime_") -> Path:
        """Create temp file and write bytes to it"""
        path = self.create_temp_file(suffix=suffix, prefix=prefix)
        path.write_bytes(data)
        return path

    def write_text(self, data: str, suffix: str = ".txt", prefix: str = "storytime_") -> Path:
        """Create temp file and write text to it"""
        path = self.create_temp_file(suffix=suffix, prefix=prefix)
        path.write_text(data)
        return path

    @contextmanager
    def temp_file_context(self, suffix: str = ".png", prefix: str = "storytime_"):
        """Context manager for temp file that auto-cleans on exit"""
        path = self.create_temp_file(suffix=suffix, prefix=prefix)
        try:
            yield path
        finally:
            self.cleanup_file(path)

    def cleanup_file(self, path: Path) -> bool:
        """Remove a specific temp file"""
        with self._lock:
            try:
                if path.exists():
                    path.unlink()
                self._temp_files.discard(path)
                return True
            except Exception:
                return False

    def cleanup_all(self):
        """Clean up all tracked temp files"""
        with self._lock:
            for path in list(self._temp_files):
                try:
                    if path.exists():
                        path.unlink()
                except Exception:
                    pass
            self._temp_files.clear()

    def get_temp_files(self) -> list[Path]:
        """Get list of all tracked temp files"""
        with self._lock:
            return list(self._temp_files)


_temp_handler: Optional[TempFileHandler] = None


def get_temp_handler() -> TempFileHandler:
    """Get or create global temp file handler"""
    global _temp_handler
    if _temp_handler is None:
        _temp_handler = TempFileHandler()
    return _temp_handler
