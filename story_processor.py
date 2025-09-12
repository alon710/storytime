"""
Story processor for StoryTime using Google GenAI

This module generates illustrated PDF booklets using:
- Gemini 2.5 Flash Image Preview for image generation
- Custom illustration prompts for each page
- Direct character image reference for consistency
- Image-only PDF output without text
"""

import io
import os
import time
import tempfile
from typing import List, Dict, Optional

from PIL import Image
from google import genai
from google.genai import types


# PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as ReportLabImage,
    PageBreak,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

from config import settings
from logger import logger


class StoryProcessor:
    """
    Story processor for generating illustrated children's books

    Uses Gemini 2.5 Flash Image Preview to:
    1. Generate consistent character illustrations using reference image
    2. Create custom illustrations based on user prompts
    3. Generate image-only PDF booklets
    4. Maintain character consistency across all pages
    """

    def __init__(self):
        """
        Initialize the processor with Google GenAI client

        Sets up:
        - Environment variable for API key
        - GenAI client with user's API key
        - Model name from settings
        """
        os.environ["GEMINI_API_KEY"] = settings.google_api_key
        self.client = genai.Client(api_key=settings.google_api_key)
        self.model = settings.model


    def generate_image_for_page(
        self,
        character_image,
        character_name: str,
        character_age: int,
        character_gender: str,
        illustration_prompt: str,
        art_style: str,
        book_title: str,
        page_title: str,
        story_text: str = "",
    ) -> Optional[str]:
        """
        Generate custom illustration using Gemini 2.5 Flash Image Preview

        This method:
        1. Takes character reference image + custom illustration prompt + style + context
        2. Sends to Gemini with proper response modalities ['Text', 'Image']
        3. Extracts binary image data from response
        4. Saves to temporary file for PDF generation
        5. Returns file path or None if generation fails

        Args:
            character_image: PIL image of character for consistency
            character_name: Name of character
            character_age: Age for age-appropriate illustrations
            character_gender: Gender (Boy/Girl) for character consistency
            illustration_prompt: Custom prompt describing the desired illustration
            art_style: Art style (storybook, watercolor, etc.)
            book_title: Title of the book for thematic consistency
            page_title: Title of this specific page
            story_text: Optional story context for this page

        Returns:
            Path to generated image file, or None if failed
        """
        try:
            # Reset file pointer for character image
            character_image.seek(0)
            character_image_pil = Image.open(character_image)
            character_image.seek(0)  # Reset for next use

            # Create comprehensive system prompt for image generation
            context_info = f"\nStory context: {story_text}" if story_text.strip() else ""
            
            system_prompt = f"""
            Generate a single wordless {art_style} style children's book illustration without any text or words.
            
            Book: "{book_title}"
            Page: "{page_title}"
            Character: {character_name}, a {character_age}-year-old {character_gender.lower()}
            Illustration request: {illustration_prompt}{context_info}
            
            CRITICAL STYLE CONSISTENCY REQUIREMENTS:
            - Use the character image as reference to maintain EXACT visual consistency across ALL pages
            - Keep the SAME art style ({art_style}) throughout the entire book - same color palette, same line quality, same lighting
            - Maintain consistent character appearance: same face, hair, clothing style, and proportions on every page
            - Use consistent background elements and environmental style
            - Keep the same illustration technique and visual treatment across all images
            - Ensure uniform color saturation and brightness levels
            - This illustration is part of "{book_title}" and should fit the overall story theme
            
            Create one complete illustration scene that is warm and child-friendly, engaging for ages 2-8.
            Do not create a grid, collage, or multiple panels - generate only one single cohesive image.
            Do not include any text, letters, or words in the illustration.
            This illustration must look like it belongs in the same book as all other pages.
            """

            # Create contents list with system prompt, illustration prompt, and character image
            contents = [system_prompt, illustration_prompt, character_image_pil]

            # Call Gemini with image generation
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_modalities=["Text", "Image"]
                ),
            )

            if not response or not response.candidates:
                logger.warning("No response received from Gemini API")
                return None

            # Extract image from response
            generated_image = None
            response_text = ""

            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    response_text += part.text
                elif part.inline_data is not None:
                    # Found image data - save to temporary file
                    image_data = part.inline_data.data
                    generated_image = Image.open(io.BytesIO(image_data))

                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(
                        suffix=".png", delete=False
                    ) as tmp_file:
                        generated_image.save(tmp_file.name, "PNG")
                        temp_path = tmp_file.name

                    logger.info("Successfully generated image for page", extra={"page_title": page_title, "temp_path": temp_path})
                    logger.debug("Gemini response text", extra={"response_text": response_text[:200]})
                    return temp_path

            # If we reach here, no image was generated
            logger.warning("No image generated for page - text response only", extra={"page_title": page_title, "response_text": response_text[:200]})
            return None

        except Exception as e:
            error_str = str(e)
            logger.error("Image generation failed for page", extra={"page_title": page_title, "error": error_str}, exc_info=True)
            return None

    def create_pdf_booklet(
        self,
        book_title: str,
        pages_data: List[Dict],
        image_paths: List[Optional[str]],
        output_path: str,
    ) -> str:
        """Create illustrated PDF booklet with titles, images, and story text"""
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

        # Title page
        title_style = styles["Title"]
        title_style.fontSize = 24
        title_style.alignment = TA_CENTER

        story_elements.append(Paragraph(book_title, title_style))
        story_elements.append(Spacer(1, 40))
        story_elements.append(Paragraph("AI-Generated Illustrated Storybook", styles["Normal"]))
        story_elements.append(PageBreak())

        # Story pages with title, image, and text
        for i, (page_data, image_path) in enumerate(zip(pages_data, image_paths)):
            # Page title
            page_title = Paragraph(page_data["title"], styles["Heading2"])
            story_elements.append(page_title)
            story_elements.append(Spacer(1, 15))

            # Create table with image and story text side by side
            table_data = []
            
            # Image cell
            if image_path and os.path.exists(image_path):
                img = ReportLabImage(image_path, width=4 * inch, height=4 * inch)
            else:
                img = Paragraph("[Image not generated]", styles["Normal"])

            # Story text cell
            story_text = page_data.get("story_text", "")
            if story_text.strip():
                # Create a styled paragraph for story text
                story_style = styles["Normal"]
                story_style.fontSize = 12
                story_style.leading = 16
                text_para = Paragraph(story_text, story_style)
            else:
                text_para = Paragraph("[No story text provided]", styles["Normal"])

            # Add to table: [Image, Text]
            table_data.append([img, text_para])

            # Create table
            table = Table(table_data, colWidths=[4.2 * inch, 3.3 * inch])
            table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 10),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                        ("GRID", (0, 0), (-1, -1), 0.5, (0.8, 0.8, 0.8)),
                    ]
                )
            )

            story_elements.append(table)
            story_elements.append(Spacer(1, 20))

            if i < len(pages_data) - 1:
                story_elements.append(PageBreak())

        # Build PDF
        doc.build(story_elements)
        return pdf_path

    def process_story(
        self,
        pages_data: List[Dict],
        character_image,
        character_name: str,
        character_age: int,
        character_gender: str,
        art_style: str,
        book_title: str,
        output_folder: str,
        progress_bar=None,
    ) -> Dict:
        """
        Main processing function for generating illustrated storybooks
        
        Args:
            pages_data: List of page dictionaries with title, story_text, and illustration_prompt
            character_image: Uploaded character image for consistency
            character_name: Name of the character
            character_age: Age of character for age-appropriate illustrations
            character_gender: Gender of character
            art_style: Art style for illustrations
            book_title: Title of the book
            output_folder: Directory to save the PDF
            progress_bar: Streamlit progress bar (optional)
            
        Returns:
            Dictionary with success status, pdf_path, pages_processed, error, processing_time
        """
        results = {
            "success": False,
            "pdf_path": None,
            "pages_processed": 0,
            "error": None,
            "processing_time": 0,
        }

        start_time = time.time()

        try:
            # Step 1: Generate images for each page (fail fast if any fails)
            if progress_bar:
                progress_bar.progress(30, "Generating illustrations...")

            image_paths = []
            for i, page_data in enumerate(pages_data):
                if progress_bar:
                    progress = 10 + (70 * (i + 1) / len(pages_data))
                    progress_bar.progress(
                        int(progress), f"Generating image {i + 1}/{len(pages_data)}..."
                    )

                image_path = self.generate_image_for_page(
                    character_image,
                    character_name,
                    character_age,
                    character_gender,
                    page_data["illustration_prompt"],
                    art_style,
                    book_title,
                    page_data["title"],
                    page_data.get("story_text", ""),
                )

                if image_path is None:
                    # FAIL FAST - don't continue without images
                    results["error"] = (
                        f"Image generation failed for {page_data['title']}. Please check your API key and model settings."
                    )
                    if progress_bar:
                        progress_bar.progress(0, "Error: Image generation failed")
                    return results

                image_paths.append(image_path)

            # Step 2: Create PDF booklet (only if all images generated)
            if progress_bar:
                progress_bar.progress(85, "Creating PDF booklet...")

            pdf_path = self.create_pdf_booklet(
                book_title,
                pages_data,
                image_paths,
                output_folder,
            )

            if progress_bar:
                progress_bar.progress(100, "Complete!")

            results.update(
                {
                    "success": True,
                    "pdf_path": pdf_path,
                    "pages_processed": len(pages_data),
                    "processing_time": time.time() - start_time,
                }
            )

        except Exception as e:
            results["error"] = str(e)
            if progress_bar:
                progress_bar.progress(0, f"Error: {str(e)}")

        return results
