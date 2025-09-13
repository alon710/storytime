from typing import Optional
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors as reportlab_colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from app.ai.text_personalizer import TextPersonalizer
from app.utils.logger import logger
from app.utils.schemas import Colors, Gender, Suffix, PageData
from app.utils.temp_file import save_bytes_to_temp
import io


class PDFBuilder:
    def __init__(self, text_personalizer: TextPersonalizer):
        self.text_personalizer = text_personalizer
        self.regular_font = "ComicNeue-Regular"
        self.bold_font = "ComicNeue-Bold"
        self.fallback_font = "Helvetica"
        self._register_fonts()

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
        len(pages_data)

        for i, (page_data, image_path) in enumerate(zip(pages_data, image_paths)):
            if i > 0:  # Don't add extra page for the first page
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
        # Draw full-page background image with proper aspect ratio handling
        if image_path:
            self._draw_fitted_image(c, image_path, width, height)

        # Add story text in bottom 1/5 of page
        story_text = page_data.story_text
        if story_text.strip():
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

        # Draw lines
        for i, line in enumerate(lines):
            c.drawString(x, y - (i * line_height), line)

    def _register_fonts(self):
        """Register Comic Neue fonts with ReportLab, fallback to system fonts."""
        # Start with fallback fonts as default
        self.regular_font = self.fallback_font
        self.bold_font = self.fallback_font
        
        try:
            # Get the absolute path to the fonts directory
            current_dir = os.path.dirname(os.path.abspath(__file__))
            fonts_dir = os.path.join(current_dir, "..", "assets", "fonts")
            
            regular_font_path = os.path.join(fonts_dir, "ComicNeue-Regular.ttf")
            bold_font_path = os.path.join(fonts_dir, "ComicNeue-Bold.ttf")
            
            # Only try to register fonts if they exist and are valid TTF files
            if os.path.exists(regular_font_path):
                try:
                    # Validate it's a real TTF file by reading the header
                    with open(regular_font_path, 'rb') as f:
                        header = f.read(4)
                        if header in [b'\x00\x01\x00\x00', b'OTTO', b'true']:  # TTF/OTF signatures
                            pdfmetrics.registerFont(TTFont("ComicNeue-Regular", regular_font_path))
                            self.regular_font = "ComicNeue-Regular"
                            logger.info("Registered Comic Neue Regular font")
                        else:
                            logger.warning(f"File at {regular_font_path} is not a valid font file")
                except Exception as e:
                    logger.warning(f"Failed to register regular font: {e}")
                    
            if os.path.exists(bold_font_path):
                try:
                    # Validate it's a real TTF file by reading the header
                    with open(bold_font_path, 'rb') as f:
                        header = f.read(4)
                        if header in [b'\x00\x01\x00\x00', b'OTTO', b'true']:  # TTF/OTF signatures
                            pdfmetrics.registerFont(TTFont("ComicNeue-Bold", bold_font_path))
                            self.bold_font = "ComicNeue-Bold"
                            logger.info("Registered Comic Neue Bold font")
                        else:
                            logger.warning(f"File at {bold_font_path} is not a valid font file")
                except Exception as e:
                    logger.warning(f"Failed to register bold font: {e}")
                
            logger.info(f"Using fonts - Regular: {self.regular_font}, Bold: {self.bold_font}")
                
        except Exception as e:
            logger.warning(f"Font registration error: {e}. Using fallback fonts.")
            self.regular_font = self.fallback_font
            self.bold_font = self.fallback_font

    def _draw_text_banner(
        self,
        c: canvas.Canvas,
        text: str,
        width: float,
        height: float,
    ):
        """Draw story text in a full-width banner at the bottom 1/5 of the page."""
        # Calculate banner dimensions
        banner_height = height / 5
        banner_y = 0
        padding = 20  # Internal padding for text readability
        
        # Draw full-width pastel background
        c.setFillColor(reportlab_colors.HexColor(Colors.SECONDARY))
        c.rect(
            x=0,
            y=banner_y,
            width=width,
            height=banner_height,
            stroke=0,
            fill=1
        )
        
        # Set up text properties
        c.setFillColor(reportlab_colors.HexColor(Colors.PRIMARY))
        font_size = 16
        line_height = 20
        
        # Calculate text area with padding for readability
        text_x = padding
        text_y = banner_y + padding
        text_width = width - (2 * padding)
        text_height = banner_height - (2 * padding)
        
        self._draw_wrapped_text_with_font(
            c=c,
            text=text,
            x=text_x,
            y=text_y + text_height - line_height,  # Start from top of text area
            max_width=text_width,
            max_height=text_height,
            font_name=self.regular_font,
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
        font_name: str,
        font_size: int,
        line_height: float,
    ):
        """Draw text with word wrapping and proper font handling."""
        c.setFont(font_name, font_size)
        
        words = text.split()
        lines = []
        current_line = ""
        
        # Build lines that fit within max_width
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
        
        # Limit lines to fit within max_height
        max_lines = int(max_height / line_height)
        if len(lines) > max_lines:
            lines = lines[:max_lines - 1]
            if lines:
                lines[-1] += "..."
        
        # Center text vertically in available space
        total_text_height = len(lines) * line_height
        start_y = y - (total_text_height - line_height) / 2
        
        # Draw each line centered horizontally
        for i, line in enumerate(lines):
            line_width = c.stringWidth(line, font_name, font_size)
            line_x = x + (max_width - line_width) / 2
            c.drawString(line_x, start_y - (i * line_height), line)

    def _draw_fitted_image(self, c: canvas.Canvas, image_path: str, page_width: float, page_height: float):
        """Draw image in top 4/5 of page, leaving bottom 1/5 for text."""
        image_height = page_height * 4/5
        image_y = page_height / 5  # Position image above text banner
        
        c.drawImage(
            image=image_path,
            x=0,
            y=image_y,
            width=page_width,
            height=image_height,
            preserveAspectRatio=False,
            mask='auto'
        )
