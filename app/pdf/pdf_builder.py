from typing import Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as reportlab_colors
from app.ai.text_personalizer import TextPersonalizer
from app.utils.schemas import Colors, Gender, Suffix, PageData, PersonalizedStoryBook
from app.utils.temp_file import save_bytes_to_temp
import io


class PDFBuilder:
    def __init__(self, text_personalizer: TextPersonalizer):
        self.text_personalizer = text_personalizer
        self.page_width, self.page_height = A4
        self.image_height = self.page_height * 4 / 5
        self.text_area_height = self.page_height / 5
        self.body_font_size = 16
        self.banner_height = self.page_height / 5
        self.padding = 10
        self.line_height = 18

    def create_book(
        self,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        pages_data: list[PageData],
        image_paths: list[Optional[str]],
        personalized_book: PersonalizedStoryBook | None = None,
    ) -> Optional[str]:
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)

        for i, (page_data, image_path) in enumerate(zip(pages_data, image_paths)):
            previous_pages = pages_data[:i] if i > 0 else None

            # Get personalized text if available
            personalized_text = None
            if personalized_book and i < len(personalized_book.personalized_pages):
                personalized_text = personalized_book.personalized_pages[i].personalized_text

            self._create_story_page(
                c=c,
                page_data=page_data,
                image_path=image_path,
                character_name=character_name,
                character_age=character_age,
                character_gender=character_gender,
                previous_pages=previous_pages,
                personalized_text=personalized_text,
            )

        c.save()

        pdf_data = buffer.getvalue()
        buffer.close()

        return save_bytes_to_temp(pdf_data, Suffix.pdf)

    def _create_story_page(
        self,
        c: canvas.Canvas,
        page_data: PageData,
        image_path: str | None,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        previous_pages: list[PageData] | None = None,
        personalized_text: str | None = None,
    ):
        self._draw_fitted_image(
            c=c,
            image_path=image_path,
        )

        if story_text := page_data.story_text:
            # Use pre-personalized text if available, otherwise personalize on the fly
            final_text = personalized_text
            if not final_text:
                final_text = self.text_personalizer.personalize(
                    story_text,
                    character_name,
                    character_age,
                    character_gender,
                    previous_pages,
                )

            if final_text:
                self._draw_text_banner(c=c, text=final_text)

        c.showPage()

    def _draw_text_banner(
        self,
        c: canvas.Canvas,
        text: str,
    ):
        c.setFillColor(reportlab_colors.HexColor(Colors.SECONDARY))
        c.rect(
            x=0,
            y=0,
            width=self.page_width,
            height=self.banner_height,
            stroke=0,
            fill=1,
        )

        c.setFillColor(reportlab_colors.HexColor(Colors.PRIMARY))
        c.setFont("Helvetica", self.body_font_size)

        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            if c.stringWidth(
                test_line, "Helvetica", self.body_font_size
            ) <= self.page_width - (2 * self.padding):
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        total_text_height = len(lines) * self.line_height
        text_area_height = self.banner_height - (2 * self.padding)
        start_y = self.padding + (text_area_height + total_text_height) / 2

        for i, line in enumerate(lines):
            line_width = c.stringWidth(line, "Helvetica", self.body_font_size)
            line_x = (self.page_width - line_width) / 2
            c.drawString(line_x, start_y - (i * self.line_height), line)

    def _draw_fitted_image(
        self,
        c: canvas.Canvas,
        image_path: str,
    ):
        c.drawImage(
            image=image_path,
            x=0,
            y=self.banner_height,
            width=self.page_width,
            height=self.image_height,
            preserveAspectRatio=False,
        )
