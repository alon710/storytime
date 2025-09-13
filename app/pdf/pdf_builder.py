from typing import Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as reportlab_colors
from app.ai.text_personalizer import TextPersonalizer
from app.utils.logger import logger
from app.utils.schemas import Colors, Gender, Suffix, PageData
from app.utils.temp_file import save_bytes_to_temp
import io


class PDFBuilder:
    def __init__(self, text_personalizer: TextPersonalizer):
        self.text_personalizer = text_personalizer
        self.font = "Helvetica"

    def create_book(
        self,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        pages_data: list[PageData],
        image_paths: list[Optional[str]],
    ) -> Optional[str]:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        for i, (page_data, image_path) in enumerate(zip(pages_data, image_paths)):
            previous_pages = pages_data[:i] if i > 0 else None

            self._create_story_page(
                c=c,
                width=width,
                height=height,
                page_data=page_data,
                image_path=image_path,
                character_name=character_name,
                character_age=character_age,
                character_gender=character_gender,
                previous_pages=previous_pages,
            )

        c.save()

        pdf_data = buffer.getvalue()
        buffer.close()

        temp_pdf_path = save_bytes_to_temp(pdf_data, Suffix.pdf)

        logger.info("PDF creation completed")
        return temp_pdf_path

    def _create_story_page(
        self,
        c: canvas.Canvas,
        width: float,
        height: float,
        page_data: PageData,
        image_path: str | None,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        previous_pages: list[PageData] | None = None,
    ):
        if image_path:
            self._draw_fitted_image(
                c=c,
                image_path=image_path,
                width=width,
                height=height,
            )

        if story_text := page_data.story_text:
            personalized_text = self.text_personalizer.personalize(
                story_text,
                character_name,
                character_age,
                character_gender,
                previous_pages,
            )

            self._draw_text_banner(
                c=c,
                text=personalized_text,
                width=width,
                height=height,
            )

    def _draw_wrapped_text(
        self,
        c: canvas.Canvas,
        text: str,
        x: float,
        y: float,
        max_width: float,
        line_height: float,
    ):
        """Draw text with simple word wrapping (legacy method for compatibility)."""
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            if c.stringWidth(test_line, "Helvetica", 12) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        for i, line in enumerate(lines):
            c.drawString(x, y - (i * line_height), line)

    def _draw_text_banner(
        self,
        c: canvas.Canvas,
        text: str,
        width: float,
        height: float,
    ):
        banner_height: float = height / 5
        banner_y: int = 0
        padding: int = 20

        c.setFillColor(reportlab_colors.HexColor(Colors.SECONDARY))
        c.rect(x=0, y=banner_y, width=width, height=banner_height, stroke=0, fill=1)

        c.setFillColor(reportlab_colors.HexColor(Colors.PRIMARY))
        font_size = 16
        line_height = 20

        text_x = padding
        text_y = banner_y + padding
        text_width = width - (2 * padding)
        text_height = banner_height - (2 * padding)

        self._draw_wrapped_text_with_font(
            c=c,
            text=text,
            x=text_x,
            y=text_y + text_height - line_height,
            max_width=text_width,
            max_height=text_height,
            font_size=font_size,
            line_height=line_height,
        )

    def _draw_wrapped_text_with_font(
        self,
        c: canvas.Canvas,
        text: str,
        x: float,
        y: float,
        max_width: float,
        max_height: float,
        font_size: int,
        line_height: float,
    ):
        c.setFont(self.font, font_size)

        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            if c.stringWidth(test_line, self.font, font_size) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        max_lines = int(max_height / line_height)
        if len(lines) > max_lines:
            lines = lines[: max_lines - 1]
            if lines:
                lines[-1] += "..."

        total_text_height = len(lines) * line_height
        start_y = y - (total_text_height - line_height) / 2

        for i, line in enumerate(lines):
            line_width = c.stringWidth(line, self.font, font_size)
            line_x = x + (max_width - line_width) / 2
            c.drawString(line_x, start_y - (i * line_height), line)

    def _draw_fitted_image(
        self, c: canvas.Canvas, image_path: str, page_width: float, page_height: float
    ):
        """Draw image in top 4/5 of page, leaving bottom 1/5 for text."""
        image_height = page_height * 4 / 5
        image_y = page_height / 5

        c.drawImage(
            image=image_path,
            x=0,
            y=image_y,
            width=page_width,
            height=image_height,
            preserveAspectRatio=False,
            mask="auto",
        )
