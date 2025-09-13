from typing import Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as reportlab_colors
from app.ai.text_personalizer import TextPersonalizer
from app.pdf.font_manager import FontManager
from app.utils.logger import logger
from app.utils.schemas import Gender, Suffix
from app.utils.temp_file import save_bytes_to_temp


class PDFBuilder:
    def __init__(self, text_personalizer: TextPersonalizer):
        self.text_personalizer = text_personalizer
        self.font_manager = FontManager()
        self.fonts = self.font_manager.setup_fonts()

    def create_booklet(
        self,
        book_title: str,
        character_name: str,
        character_age: int,
        character_gender: Gender,
        pages_data: list[dict],
        image_paths: list[Optional[str]],
    ) -> Optional[str]:
        import io
        
        # Create PDF in memory buffer
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4

        logger.info(
            "Starting PDF creation with child-friendly styling",
            book_title=book_title,
            total_pages=len(pages_data),
            fonts_available=self.fonts,
        )

        # Title page
        self._create_title_page(c, width, height, book_title, character_age)

        # Story pages with AI-generated colors
        for i, (page_data, image_path) in enumerate(zip(pages_data, image_paths)):
            c.showPage()  # New page

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
        
        # Save PDF buffer to temporary file
        pdf_data = buffer.getvalue()
        buffer.close()
        
        temp_pdf_path = save_bytes_to_temp(pdf_data, Suffix.pdf)
        
        logger.info(
            "PDF creation completed",
            temp_pdf_path=temp_pdf_path,
        )
        return temp_pdf_path

    def _create_title_page(
        self,
        c: canvas.Canvas,
        width: float,
        height: float,
        book_title: str,
        character_age: int,
    ):
        """Create playful title page with child-friendly styling."""
        # Background gradient effect using rectangles
        self._draw_gradient_background(c, width, height, "#FFF8E7", "#E8F4FD")

        # Title with playful font
        title_font = self.fonts["title"]
        c.setFont(title_font, 32)
        c.setFillColor(reportlab_colors.HexColor("#2E4057"))  # Dark blue-gray

        # Center the title
        title_width = c.stringWidth(book_title, title_font, 32)
        x = (width - title_width) / 2
        c.drawString(x, height - 150, book_title)

        # Decorative subtitle with smaller playful font
        c.setFont(self.fonts["body"], 16)
        c.setFillColor(reportlab_colors.HexColor("#7B8FA4"))  # Lighter blue-gray
        subtitle = f"A Magical Adventure for {character_age}-Year-Olds"
        subtitle_width = c.stringWidth(subtitle, self.fonts["body"], 16)
        x = (width - subtitle_width) / 2
        c.drawString(x, height - 200, subtitle)

        # AI attribution at bottom
        c.setFont(self.fonts["body"], 10)
        c.setFillColor(reportlab_colors.HexColor("#A0A8B5"))
        attribution = "AI-Generated Illustrated Storybook"
        attr_width = c.stringWidth(attribution, self.fonts["body"], 10)
        x = (width - attr_width) / 2
        c.drawString(x, 60, attribution)

    def _create_story_page(
        self,
        c: canvas.Canvas,
        width: float,
        height: float,
        page_data: dict,
        image_path: Optional[str],
        character_name: str,
        character_age: int,
        character_gender: Gender,
        previous_pages: list[dict] | None = None,
    ):
        colors = {"background": "#FFF8E7", "banner": "#E8F4FD", "accent": "#FFE4E1"}

        # Full-page background color
        c.setFillColor(reportlab_colors.HexColor(colors["background"]))
        c.rect(0, 0, width, height, stroke=0, fill=1)

        # Full-page image (if available) with padding
        image_margin = 20
        if image_path:
            try:
                # Calculate image dimensions to fill most of the page
                img_width = width - (2 * image_margin)
                img_height = height - 120  # Leave space for text banner
                c.drawImage(
                    image_path,
                    image_margin,
                    60,  # Start above text banner
                    width=img_width,
                    height=img_height,
                    preserveAspectRatio=True,
                )
            except Exception as e:
                logger.warning(
                    "Failed to draw story image",
                    image_path=image_path,
                    error=str(e),
                )
                self._draw_image_placeholder(c, width, height, colors["accent"])
        else:
            self._draw_image_placeholder(c, width, height, colors["accent"])

        # Colored text banner at bottom
        banner_height = 80
        c.setFillColor(reportlab_colors.HexColor(colors["banner"]))
        self._draw_rounded_rect(c, 0, 0, width, banner_height, 0)

        # Story text in banner
        story_text = page_data.get("story_text", "")
        if story_text.strip():
            personalized_text = self.text_personalizer.personalize(
                story_text,
                character_name,
                character_age,
                character_gender,
                previous_pages,
            )

            # Text styling
            c.setFont(self.fonts["body"], 14)
            c.setFillColor(reportlab_colors.HexColor("#2E4057"))  # Dark text

            # Text with padding in banner
            text_margin = 20
            self._draw_wrapped_text_in_banner(
                c,
                personalized_text,
                text_margin,
                banner_height - 15,
                width - (2 * text_margin),
                18,
            )

        # Page title overlay at top with semi-transparent background
        title_banner_height = 40
        c.setFillColor(reportlab_colors.HexColor(colors["accent"]))
        c.setStrokeColor(reportlab_colors.HexColor(colors["accent"]))
        self._draw_rounded_rect(
            c, 20, height - title_banner_height - 20, width - 40, title_banner_height, 8
        )

        # Title text
        c.setFont(self.fonts["title"], 18)
        c.setFillColor(reportlab_colors.HexColor("#2E4057"))
        title_width = c.stringWidth(page_data["title"], self.fonts["title"], 18)
        title_x = (width - title_width) / 2
        c.drawString(title_x, height - 40, page_data["title"])

    def _draw_wrapped_text_in_banner(
        self,
        c: canvas.Canvas,
        text: str,
        x: float,
        y: float,
        max_width: float,
        line_height: float,
    ):
        """Draw text with word wrapping optimized for text banner."""
        words = text.split()
        lines = []
        current_line = ""
        font_name = self.fonts["body"]
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

    def _draw_rounded_rect(
        self,
        c: canvas.Canvas,
        x: float,
        y: float,
        width: float,
        height: float,
        radius: float,
    ):
        """Draw a rounded rectangle."""
        if radius == 0:
            c.rect(x, y, width, height, stroke=0, fill=1)
            return

        c.roundRect(x, y, width, height, radius, stroke=0, fill=1)

    def _draw_gradient_background(
        self, c: canvas.Canvas, width: float, height: float, color1: str, color2: str
    ):
        """Draw a simple gradient effect using multiple rectangles."""
        steps = 20
        step_height = height / steps

        for i in range(steps):
            # Simple linear interpolation between colors
            i / steps
            # For simplicity, just use the first color - real gradients are complex in ReportLab
            c.setFillColor(reportlab_colors.HexColor(color1))
            c.rect(0, i * step_height, width, step_height, stroke=0, fill=1)

    def _draw_image_placeholder(
        self, c: canvas.Canvas, width: float, height: float, accent_color: str
    ):
        """Draw a placeholder when image is not available."""
        # Light background
        c.setFillColor(reportlab_colors.HexColor(accent_color))
        placeholder_height = height - 120
        c.rect(20, 60, width - 40, placeholder_height, stroke=0, fill=1)

        # Placeholder text
        c.setFont(self.fonts["body"], 16)
        c.setFillColor(reportlab_colors.HexColor("#7B8FA4"))
        placeholder_text = "✨ Illustration Coming Soon ✨"
        text_width = c.stringWidth(placeholder_text, self.fonts["body"], 16)
        text_x = (width - text_width) / 2
        text_y = height / 2
        c.drawString(text_x, text_y, placeholder_text)

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
