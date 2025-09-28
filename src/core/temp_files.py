import tempfile
import os
import base64
from core.logger import logger


class TempFileManager:
    def __init__(self):
        self._temp_files: list[str] = []

    def save_from_base64(self, base64_data: str, suffix: str = ".png", prefix: str = "temp_") -> str:
        try:
            data = base64.b64decode(s=base64_data)

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=prefix) as temp_file:
                temp_file.write(data)
                temp_path = temp_file.name

            self._temp_files.append(temp_path)
            logger.info("Data saved to temp file", path=temp_path)
            return temp_path

        except Exception as e:
            logger.error("Failed to save to temp file", error=str(e))
            raise

    def save_file(self, file_content: bytes, suffix: str = ".png", prefix: str = "uploaded_") -> str:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, prefix=prefix) as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name

            self._temp_files.append(temp_path)
            logger.info("File saved to temp file", path=temp_path)
            return temp_path

        except Exception as e:
            logger.error("Failed to save file to temp", error=str(e))
            raise

    def cleanup_all_files(self):
        for temp_path in self._temp_files:
            try:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    logger.debug("Cleaned up temp file", path=temp_path)
            except Exception as e:
                logger.warning("Failed to cleanup temp file", path=temp_path, error=str(e))

        self._temp_files.clear()
        logger.info("All temp files cleaned up")


temp_file_manager = TempFileManager()
