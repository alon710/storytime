"""PDF generation module for StoryTime."""

import os
from typing import List, Dict, Optional
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage, PageBreak, Table, TableStyle
from text_personalizer import TextPersonalizer


class PDFBuilder:
    """Handles PDF booklet creation with illustrations and personalized text."""
    
    def __init__(self, text_personalizer: TextPersonalizer):
        """Initialize PDF builder with text personalizer."""
        self.text_personalizer = text_personalizer
    
    def create_booklet(
        self,
        book_title: str,
        character_name: str,
        character_age: int,
        character_gender: str,
        pages_data: List[Dict],
        image_paths: List[Optional[str]],
        output_path: str,
        language: str = "English",
    ) -> str:
        """Create illustrated PDF booklet."""
        pdf_path = f"{output_path}/{book_title.replace(' ', '_')}_storybook.pdf"
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        story_elements = []
        styles = getSampleStyleSheet()

        self._create_title_page(story_elements, book_title, styles)
        self._create_story_pages(
            story_elements, 
            pages_data, 
            image_paths, 
            character_name,
            character_age,
            character_gender,
            language,
            styles
        )

        doc.build(story_elements)
        return pdf_path
    
    def _create_title_page(self, story_elements: List, book_title: str, styles):
        """Create the title page of the booklet."""
        title_style = styles["Title"]
        title_style.fontSize = 24
        title_style.alignment = TA_CENTER

        story_elements.append(Paragraph(book_title, title_style))
        story_elements.append(Spacer(1, 40))
        story_elements.append(Paragraph("AI-Generated Illustrated Storybook", styles["Normal"]))
        story_elements.append(PageBreak())
    
    def _create_story_pages(
        self, 
        story_elements: List, 
        pages_data: List[Dict], 
        image_paths: List[Optional[str]],
        character_name: str,
        character_age: int,
        character_gender: str,
        language: str,
        styles
    ):
        """Create the story pages with images and text."""
        for i, (page_data, image_path) in enumerate(zip(pages_data, image_paths)):
            page_title = Paragraph(page_data["title"], styles["Heading2"])
            story_elements.append(page_title)
            story_elements.append(Spacer(1, 15))

            table_data = []
            
            img = self._create_image_element(image_path, styles)
            text_para = self._create_text_element(
                page_data, 
                character_name, 
                character_age, 
                character_gender,
                language,
                styles
            )

            table_data.append([img, text_para])
            table = self._create_page_table(table_data)

            story_elements.append(table)
            story_elements.append(Spacer(1, 20))

            if i < len(pages_data) - 1:
                story_elements.append(PageBreak())
    
    def _create_image_element(self, image_path: Optional[str], styles):
        """Create image element for the page."""
        if image_path and os.path.exists(image_path):
            return ReportLabImage(image_path, width=4 * inch, height=4 * inch)
        else:
            return Paragraph("[Image not generated]", styles["Normal"])
    
    def _create_text_element(
        self, 
        page_data: Dict, 
        character_name: str, 
        character_age: int, 
        character_gender: str,
        language: str,
        styles
    ):
        """Create personalized text element for the page."""
        story_text = page_data.get("story_text", "")
        if story_text.strip():
            personalized_text = self.text_personalizer.personalize(
                story_text, character_name, character_age, character_gender, language
            )
            
            story_style = styles["Normal"]
            story_style.fontSize = 12
            story_style.leading = 16
            return Paragraph(personalized_text, story_style)
        else:
            return Paragraph("[No story text provided]", styles["Normal"])
    
    def _create_page_table(self, table_data: List) -> Table:
        """Create formatted table for page layout."""
        table = Table(table_data, colWidths=[4.2 * inch, 3.3 * inch])
        table.setStyle(
            TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, (0.8, 0.8, 0.8)),
            ])
        )
        return table