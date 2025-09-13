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
            c.showPage()
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

        logger.info(
            "PDF creation completed",
            temp_pdf_path=temp_pdf_path,
        )
        return temp_pdf_path

    def _create_story_page(
        self,
        c: canvas.Canvas,
        width: float,
        height: float,
        page_data: PageData,
        image_path: Optional[str],
        character_name: str,
        character_age: int,
        character_gender: Gender,
        previous_pages: list[PageData] | None = None,
    ):
        c.setFillColor(reportlab_colors.HexColor(val=Colors.BACKGROUND))
        c.rect(x=0, y=0, width=width, height=height, stroke=0, fill=1)

        if image_path:
            img_width = width
            img_height = height
            c.drawImage(
                image=image_path,
                x=0,
                y=0,
                width=img_width,
                height=img_height,
                preserveAspectRatio=True,
            )

        story_text = page_data.story_text
        if story_text.strip():
            personalized_text = self.text_personalizer.personalize(
                story_text,
                character_name,
                character_age,
                character_gender,
                previous_pages,
            )

            c.setFillColor(reportlab_colors.HexColor(val=Colors.BANNER))

            self._draw_wrapped_text_in_banner(
                c=c,
                text=personalized_text,
                x=20,
                y=height - (2 * 20),
                max_width=width - (2 * 20),
                line_height=18,
            )

        # Page title overlay at top with semi-transparent background
        c.setFillColor(reportlab_colors.HexColor(val=Colors.ACCENT))
        c.setStrokeColor(reportlab_colors.HexColor(val=Colors.ACCENT))

        # Title text
        c.setFont(self.font, 18)
        c.setFillColor(reportlab_colors.HexColor("#2E4057"))
        title_width = c.stringWidth(page_data.title, self.font, 18)
        title_x = (width - title_width) / 2
        c.drawString(title_x, height - 40, page_data.title)

    def _draw_wrapped_text_in_banner(
        self,
        c: canvas.Canvas,
        text: str,
        x: float,
        y: float,
        max_width: float,
        line_height: float,
    ):
        words = text.split()
        lines = []
        current_line = ""
        font_name = self.font
        font_size = 14

        for word in words:
            test_line = current_line + " " + word if current_line else word
            if c.stringWidth(test_line, font_name, font_size) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # Center text vertically in banner and draw lines
        total_text_height = len(lines) * line_height
        start_y = y - (total_text_height - line_height) / 2

        for i, line in enumerate(lines):
            # Center each line horizontally
            line_width = c.stringWidth(line, font_name, font_size)
            line_x = x + (max_width - line_width) / 2
            c.drawString(line_x, start_y - (i * line_height), line)

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

        # Draw lines
        for i, line in enumerate(lines):
            c.drawString(x, y - (i * line_height), line)
