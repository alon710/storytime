import tempfile
from typing import Optional
from PIL import Image
from app.utils.logger import logger
from app.utils.schemas import Suffix


def save_image_to_temp(
    image: Image.Image,
    suffix: Suffix = Suffix.png,
) -> Optional[str]:
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            image.save(tmp_file.name, format=suffix.lstrip(".").upper())
            logger.info("Image saved to temporary file", temp_path=tmp_file.name)
            return tmp_file.name
    except Exception as e:
        logger.error("Failed to save image to temporary file", error=str(e))
        return None


def save_bytes_to_temp(
    data: bytes,
    suffix: Suffix,
) -> Optional[str]:
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_file:
            tmp_file.write(data)
            logger.info("Data saved to temporary file", temp_path=tmp_file.name)
            return tmp_file.name
    except Exception as e:
        logger.error("Failed to save data to temporary file", error=str(object=e))
        return None
