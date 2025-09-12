"""Font management module for child-friendly PDF generation."""

import tempfile
from typing import Optional
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from logger import logger
import requests


class FontManager:
    """Handles downloading and registering child-friendly fonts for ReportLab."""

    def __init__(self):
        """Initialize font manager."""
        self.registered_fonts = {}

    def setup_fonts(self) -> dict:
        """Download and register child-friendly fonts, return font mapping."""
        fonts = {}

        # Try to download and register playful fonts
        title_font = self._download_and_register_font(
            "Fredoka",
            "https://fonts.gstatic.com/s/fredoka/v14/X7nP4bQ7XieDhNXgVKhVrxiePdFD5fGgKCO9.woff2",
        )

        body_font = self._download_and_register_font(
            "ComicNeue",
            "https://fonts.gstatic.com/s/comicneue/v8/4UaHrEJGsxNmFTPDnkaJx63j5pN1MwI.woff2",
        )

        # Set up font mapping with fallbacks
        fonts["title"] = title_font or "Helvetica-Bold"
        fonts["body"] = body_font or "Helvetica"
        fonts["accent"] = title_font or "Helvetica-Bold"

        logger.info(
            "Font setup completed",
            extra={
                "title_font": fonts["title"],
                "body_font": fonts["body"],
                "accent_font": fonts["accent"],
            },
        )

        return fonts

    def _download_and_register_font(self, font_name: str, url: str) -> Optional[str]:
        """Download font from URL and register with ReportLab."""
        try:
            # Check if already registered
            if font_name in self.registered_fonts:
                return self.registered_fonts[font_name]

            logger.info("Downloading font", extra={"font_name": font_name, "url": url})

            # Download font
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".ttf", delete=False) as tmp_file:
                tmp_file.write(response.content)
                font_path = tmp_file.name

            # Register with ReportLab
            try:
                pdfmetrics.registerFont(TTFont(font_name, font_path))
                self.registered_fonts[font_name] = font_name

                logger.info(
                    "Successfully registered font",
                    extra={"font_name": font_name, "path": font_path},
                )

                return font_name

            except Exception as reg_error:
                logger.warning(
                    "Failed to register font, using fallback",
                    extra={"font_name": font_name, "error": str(reg_error)},
                )

                return None

        except Exception as e:
            logger.warning(
                "Font download failed, using system fallback",
                extra={"font_name": font_name, "error": str(e)},
            )
            return None

    def get_available_fonts(self) -> list:
        """Get list of available fonts for debugging."""
        return list(pdfmetrics.getRegisteredFontNames())
