"""
Simplified File Store Module - Temporary file management

This module provides a minimal interface for managing temporary files.
File metadata is stored in the State, not in a separate store.
"""

import base64
import tempfile
import uuid
from pathlib import Path


class TempFileManager:
    """Simplified manager for temporary file creation"""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path(tempfile.gettempdir()) / "storytime"
        self.base_dir.mkdir(exist_ok=True, parents=True)

    def create_temp_file(
        self, file_data: bytes, mime_type: str, prefix: str = "file_", original_filename: str | None = None
    ) -> str:
        """
        Create a temporary file and return its path.

        Args:
            file_data: Binary file data
            mime_type: MIME type (e.g., "image/png")
            prefix: Prefix for temp file name
            original_filename: Optional original filename (not used, kept for compatibility)

        Returns:
            Absolute path to the created temp file
        """
        suffix = self._get_suffix_from_mime_type(mime_type)
        file_id = str(uuid.uuid4())

        temp_file = tempfile.NamedTemporaryFile(
            delete=False, suffix=suffix, prefix=f"{prefix}{file_id}_", dir=self.base_dir
        )

        temp_file.write(file_data)
        temp_file.close()

        return str(Path(temp_file.name).absolute())

    def create_temp_file_from_base64(self, base64_data: str, mime_type: str, prefix: str = "file_") -> str:
        """
        Create a temporary file from base64 data.

        Args:
            base64_data: Base64 encoded data (without data URL prefix)
            mime_type: MIME type (e.g., "image/png")
            prefix: Prefix for temp file name

        Returns:
            Absolute path to the created temp file
        """
        file_data = base64.b64decode(base64_data)
        return self.create_temp_file(file_data, mime_type, prefix)

    def cleanup_file(self, file_path: str) -> bool:
        """
        Delete a temporary file.

        Args:
            file_path: Path to file to delete

        Returns:
            True if file was deleted, False otherwise
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def _get_suffix_from_mime_type(mime_type: str) -> str:
        """Get file suffix from MIME type"""
        mime_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/jpg": ".jpg",
            "image/gif": ".gif",
            "image/webp": ".webp",
            "application/pdf": ".pdf",
            "text/plain": ".txt",
            "application/json": ".json",
        }
        return mime_map.get(mime_type, ".bin")


# Global instance for convenience
temp_file_manager = TempFileManager()
