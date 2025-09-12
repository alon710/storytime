"""AI-powered children's storybook processor using Google GenAI."""

import io
import os
import time
import tempfile
from typing import List, Dict, Optional

from PIL import Image
from google import genai
from google.genai import types


from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage, PageBreak, Table, TableStyle

from config import settings
from logger import logger


class StoryProcessor:
    """Generates illustrated children's books using Google GenAI."""

    def __init__(self):
        """Initialize processor with Google GenAI client."""
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
        """Generate illustration using character reference and custom prompt."""
        try:
            character_image.seek(0)
            character_image_pil = Image.open(character_image)
            character_image.seek(0)

            context_info = f"\nStory context: {story_text}" if story_text.strip() else ""
            
            system_prompt = f"""
            Generate a {art_style} style children's book illustration without text.
            
            Book: "{book_title}" | Page: "{page_title}"
            Character: {character_name} ({character_age}-year-old {character_gender.lower()})
            Request: {illustration_prompt}{context_info}
            
            Requirements:
            - Use character image reference for visual consistency
            - Maintain {art_style} style throughout book
            - Keep consistent character appearance and proportions
            - Create warm, child-friendly scene for ages 2-8
            - Single cohesive image without text or multiple panels
            
            COMPOSITION REQUIREMENTS:
            - Fill the ENTIRE image space with the scene - no borders, frames, or vignettes
            - Extend the scene to all edges of the canvas
            - No abstract backgrounds or wallpaper patterns - use full environmental scenes
            - Characters and objects should occupy meaningful space in the composition
            - Background should be a complete environment (room, outdoor scene, etc.) not abstract patterns
            """

            contents = [system_prompt, illustration_prompt, character_image_pil]
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
        character_name: str,
        character_age: int,
        character_gender: str,
        pages_data: List[Dict],
        image_paths: List[Optional[str]],
        output_path: str,
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

        title_style = styles["Title"]
        title_style.fontSize = 24
        title_style.alignment = TA_CENTER

        story_elements.append(Paragraph(book_title, title_style))
        story_elements.append(Spacer(1, 40))
        story_elements.append(Paragraph("AI-Generated Illustrated Storybook", styles["Normal"]))
        story_elements.append(PageBreak())

        for i, (page_data, image_path) in enumerate(zip(pages_data, image_paths)):
            page_title = Paragraph(page_data["title"], styles["Heading2"])
            story_elements.append(page_title)
            story_elements.append(Spacer(1, 15))

            table_data = []
            
            if image_path and os.path.exists(image_path):
                img = ReportLabImage(image_path, width=4 * inch, height=4 * inch)
            else:
                img = Paragraph("[Image not generated]", styles["Normal"])

            story_text = page_data.get("story_text", "")
            if story_text.strip():
                personalized_text = self._personalize_text(story_text, character_name, character_age, character_gender)
                
                story_style = styles["Normal"]
                story_style.fontSize = 12
                story_style.leading = 16
                text_para = Paragraph(personalized_text, story_style)
            else:
                text_para = Paragraph("[No story text provided]", styles["Normal"])

            table_data.append([img, text_para])

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

        doc.build(story_elements)
        return pdf_path

    def _personalize_text(self, text: str, character_name: str, character_age: int, character_gender: str) -> str:
        """Personalize story text using AI for age and gender-appropriate language."""
        try:
            personalization_prompt = f"""
            Rewrite this children's story text:
            
            Original: "{text}"
            
            Requirements:
            - Replace "hero" with {character_name}
            - Use language for {character_age}-year-old {character_gender.lower()}
            - Keep same story events and meaning
            - Simple, engaging vocabulary for ages {max(2, character_age-2)}-{character_age+2}
            - Warm, child-friendly tone
            - Same approximate length
            - Appropriate pronouns
            
            Return only the rewritten text.
            """
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=[personalization_prompt],
                config=types.GenerateContentConfig(
                    response_modalities=["Text"]
                ),
            )
            
            if response and response.candidates and response.candidates[0].content.parts:
                personalized_text = response.candidates[0].content.parts[0].text.strip()
                logger.info("Successfully personalized story text", extra={"original_length": len(text), "personalized_length": len(personalized_text)})
                return personalized_text
            else:
                logger.warning("AI personalization failed, falling back to simple name replacement")
                return text.replace("hero", character_name).replace("Hero", character_name)
                
        except Exception as e:
            logger.error("AI personalization failed", extra={"error": str(e)}, exc_info=True)
            return text.replace("hero", character_name).replace("Hero", character_name)

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
        """Generate complete illustrated storybook."""
        results = {
            "success": False,
            "pdf_path": None,
            "pages_processed": 0,
            "error": None,
            "processing_time": 0,
        }

        start_time = time.time()

        try:
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
                    results["error"] = f"Image generation failed for {page_data['title']}. Please check your API key and model settings."
                    if progress_bar:
                        progress_bar.progress(0, "Error: Image generation failed")
                    return results

                image_paths.append(image_path)

            if progress_bar:
                progress_bar.progress(85, "Creating PDF booklet...")

            pdf_path = self.create_pdf_booklet(
                book_title,
                character_name,
                character_age,
                character_gender,
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
