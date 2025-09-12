"""PDF generation module for StoryTime using simple canvas API."""

from typing import Optional
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from text_personalizer import TextPersonalizer


class PDFBuilder:
    """Creates PDF storybooks using canvas API with default fonts."""

    def __init__(self, text_personalizer: TextPersonalizer):
        """Initialize with text personalizer."""
        self.text_personalizer = text_personalizer

    def create_booklet(
        self,
        book_title: str,
        character_name: str,
        character_age: int,
        character_gender: str,
        pages_data: list[dict],
        image_paths: list[Optional[str]],
        output_path: str,
    ) -> str:
        """Create complete illustrated PDF storybook using canvas API."""
        pdf_path = f"{output_path}/{book_title.replace(' ', '_')}_storybook.pdf"
        c = canvas.Canvas(pdf_path, pagesize=A4)
        width, height = A4
        
        # Title page
        self._create_title_page(c, width, height, book_title)
        
        # Story pages
        for page_data, image_path in zip(pages_data, image_paths):
            c.showPage()  # New page
            self._create_story_page(
                c, width, height, page_data, image_path,
                character_name, character_age, character_gender
            )
        
        c.save()
        return pdf_path

    def _create_title_page(self, c: canvas.Canvas, width: float, height: float, book_title: str):
        """Create title page."""
        c.setFont("Helvetica-Bold", 24)
        
        # Center the title
        title_width = c.stringWidth(book_title, "Helvetica-Bold", 24)
        x = (width - title_width) / 2
        c.drawString(x, height - 100, book_title)
        
        # Subtitle
        c.setFont("Helvetica", 14)
        subtitle = "AI-Generated Illustrated Storybook"
        subtitle_width = c.stringWidth(subtitle, "Helvetica", 14)
        x = (width - subtitle_width) / 2
        c.drawString(x, height - 140, subtitle)

    def _create_story_page(
        self,
        c: canvas.Canvas,
        width: float,
        height: float,
        page_data: dict,
        image_path: Optional[str],
        character_name: str,
        character_age: int,
        character_gender: str,
    ):
        """Create story page with image and text."""
        # Page title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, page_data["title"])
        
        # Image
        if image_path:
            c.drawImage(image_path, 50, height - 350, width=300, height=250)
        else:
            c.setFont("Helvetica", 12)
            c.drawString(50, height - 200, "[Image not generated]")
        
        # Story text
        story_text = page_data.get("story_text", "")
        if story_text.strip():
            personalized_text = self.text_personalizer.personalize(
                story_text, character_name, character_age, character_gender
            )
            
            # Simple text wrapping
            c.setFont("Helvetica", 12)
            self._draw_wrapped_text(c, personalized_text, 400, height - 100, width - 450, 20)
        else:
            c.setFont("Helvetica", 12)
            c.drawString(400, height - 100, "[No story text provided]")

    def _draw_wrapped_text(
        self, c: canvas.Canvas, text: str, x: float, y: float, max_width: float, line_height: float
    ):
        """Draw text with simple word wrapping."""
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