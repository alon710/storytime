"""
Clean story processor for StoryTime using Google GenAI

This module processes PDF stories and generates illustrated PDF booklets using:
- Gemini 2.5 Flash Image Preview (nano-banana) for image generation
- Direct character image reference for consistency
- Rate limiting and retry logic for quota errors
- Intelligent backoff for API limits
"""
import io
import os
import time
import tempfile
import json
from typing import List, Dict, Optional

import streamlit as st
from PIL import Image
from google import genai
from google.genai import types

# PDF processing
import pdfplumber
from langdetect import detect

# PDF generation
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from config import settings


class StoryProcessor:
    """
    Clean story processor for generating illustrated children's books
    
    Uses Gemini 2.5 Flash Image Preview (nano-banana) to:
    1. Extract text from PDF stories
    2. Generate consistent character illustrations using reference image
    3. Create professional PDF booklets with images and text
    4. Fail fast if image generation doesn't work
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
    
    def extract_text_from_pdf(self, pdf_file) -> tuple[str, str]:
        """Extract text from uploaded PDF file"""
        try:
            full_text = ""
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
            
            if not full_text.strip():
                raise ValueError("No text found in PDF")
            
            # Detect language
            try:
                language = detect(full_text)
            except:
                language = 'en'
            
            return full_text.strip(), language
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    def split_into_pages(self, text: str) -> List[str]:
        """Split text into story pages"""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if not paragraphs:
            sentences = [s.strip() + '.' for s in text.split('.') if s.strip()]
            paragraphs = sentences
        
        # Process all paragraphs from PDF
        
        # Ensure reasonable length per page
        pages = []
        for para in paragraphs:
            if len(para) > 300:
                words = para.split()
                current = ""
                for word in words:
                    if len(current + " " + word) > 300:
                        if current:
                            pages.append(current.strip())
                        current = word
                    else:
                        current += " " + word if current else word
                if current:
                    pages.append(current.strip())
            else:
                pages.append(para)
        
        return pages
    
    def generate_image_for_page(self, character_image, character_name: str, character_age: int, 
                               character_gender: str, page_text: str, art_style: str) -> Optional[str]:
        """
        Generate image for a story page using Gemini 2.5 Flash Image Preview (nano-banana)
        
        This is the core image generation method that:
        1. Takes character reference image + story text + style
        2. Sends to Gemini with proper response modalities ['Text', 'Image']
        3. Extracts binary image data from response
        4. Saves to temporary file for PDF generation
        5. Returns file path or None if generation fails
        
        Args:
            character_image: PIL image of character for consistency
            character_name: Name of character
            character_age: Age for age-appropriate illustrations
            character_gender: Gender (Boy/Girl) for character consistency
            page_text: Story text for this page
            art_style: Art style (storybook, watercolor, etc.)
            
        Returns:
            Path to generated image file, or None if failed
        """
        # Try generating with retries for quota errors
        for attempt in range(settings.max_retries + 1):
            try:
                # Add delay between attempts (except first)
                if attempt > 0:
                    delay = settings.base_retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    print(f"Quota limit hit. Retrying in {delay} seconds... (attempt {attempt + 1})")
                    
                    # Show countdown to user
                    progress_placeholder = st.empty()
                    for remaining in range(delay, 0, -1):
                        progress_placeholder.info(f"⏳ Waiting for API quota reset: {remaining} seconds...")
                        time.sleep(1)
                    progress_placeholder.empty()
                
                # Add standard delay between requests to avoid hitting limits
                elif attempt == 0 and settings.delay_between_images > 0:
                    print(f"Adding {settings.delay_between_images}s delay between requests...")
                    time.sleep(settings.delay_between_images)
                
                # Reset file pointer for character image
                character_image.seek(0)
                character_image_pil = Image.open(character_image)
                character_image.seek(0)  # Reset for next use
                
                # Create system prompt for image generation
                system_prompt = f"""
                Generate a single wordless {art_style} style children's book illustration for this story page without any text or words.
                
                Character: {character_name}, a {character_age}-year-old {character_gender.lower()}
                Story text: {page_text}
                
                Use the character image as reference to maintain visual consistency.
                Create one complete illustration scene that is warm and child-friendly, engaging for ages 2-8.
                Do not create a grid, collage, or multiple panels - generate only one single cohesive image.
                Do not include any text, letters, or words in the illustration.
                """
                
                # Create contents list with system prompt, text, and character image
                contents = [system_prompt, page_text, character_image_pil]
                
                # Call Gemini with image generation
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        response_modalities=['Text', 'Image']
                    )
                )
                
                if not response or not response.candidates:
                    print("No response from Gemini")
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
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                            generated_image.save(tmp_file.name, 'PNG')
                            temp_path = tmp_file.name
                        
                        print(f"Generated image saved: {temp_path}")
                        print(f"Response text: {response_text[:200]}...")
                        return temp_path
                
                # If we reach here, no image was generated
                print(f"No image in response. Text only: {response_text[:200]}...")
                return None
                
            except Exception as e:
                error_str = str(e)
                print(f"Error generating image (attempt {attempt + 1}): {error_str}")
                
                # Check if it's a quota error
                if "429" in error_str and "RESOURCE_EXHAUSTED" in error_str:
                    if not settings.retry_on_quota_error:
                        st.error("❌ Google API quota exceeded. Please wait or upgrade your plan.")
                        return None
                    
                    # Parse retry delay from error if available
                    try:
                        if 'retryDelay' in error_str:
                            # Try to extract retry delay from error
                            import re
                            match = re.search(r"'retryDelay': '(\d+)s'", error_str)
                            if match:
                                suggested_delay = int(match.group(1))
                                settings.base_retry_delay = max(suggested_delay, settings.base_retry_delay)
                    except:
                        pass
                    
                    if attempt < settings.max_retries:
                        st.warning(f"⚠️ API quota exceeded. Retrying... (attempt {attempt + 1}/{settings.max_retries + 1})")
                        continue
                    else:
                        st.error(f"❌ API quota exceeded after {settings.max_retries + 1} attempts. Please wait or upgrade your Google API plan.")
                        st.info("💡 Try again in a few minutes, or upgrade to paid tier for higher quotas.")
                        return None
                else:
                    # Non-quota error - don't retry
                    st.error(f"❌ Image generation failed: {error_str}")
                    return None
        
        return None
    
    def create_pdf_booklet(self, story_title: str, character_name: str,
                          pages: List[str], image_paths: List[Optional[str]], 
                          output_path: str, language: str = "English") -> str:
        """Create PDF booklet with images and text"""
        pdf_path = f"{output_path}/{story_title.replace(' ', '_')}_storybook.pdf"
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=0.75*inch,
            rightMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        story_elements = []
        styles = getSampleStyleSheet()
        
        # Set up Hebrew RTL support if needed
        is_hebrew = language == "Hebrew"
        if is_hebrew:
            # Try to register a Hebrew font (fallback to default if not available)
            try:
                # This would need a Hebrew font file - for now we'll use default with RTL alignment
                pass
            except:
                pass
        
        # Title page
        title_style = styles['Title']
        title_style.fontSize = 24
        title_style.alignment = TA_CENTER
        
        # Create Hebrew-aware styles
        if is_hebrew:
            hebrew_style = ParagraphStyle(
                'Hebrew',
                parent=styles['Normal'],
                alignment=TA_RIGHT,
                fontName='Helvetica'  # ReportLab default font with limited Hebrew support
            )
            hebrew_title_style = ParagraphStyle(
                'HebrewTitle',
                parent=title_style,
                alignment=TA_CENTER
            )
        else:
            hebrew_style = styles['Normal']
            hebrew_title_style = title_style
        
        story_elements.append(Paragraph(story_title, hebrew_title_style))
        story_elements.append(Spacer(1, 20))
        subtitle = f"The Adventures of {character_name}" if not is_hebrew else f"הרפתקאות של {character_name}"
        story_elements.append(Paragraph(subtitle, hebrew_style))
        story_elements.append(PageBreak())
        
        # Story pages
        for i, (page_text, image_path) in enumerate(zip(pages, image_paths)):
            page_data = []
            
            # Image cell
            if image_path and os.path.exists(image_path):
                img = ReportLabImage(image_path, width=3*inch, height=3*inch)
            else:
                img = Paragraph("[Image not generated]", styles['Normal'])
            
            # Text cell
            text_para = Paragraph(page_text, hebrew_style)
            page_data.append([img, text_para])
            
            # Create table
            table = Table(page_data, colWidths=[3.5*inch, 3.5*inch])
            table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ]))
            
            story_elements.append(table)
            story_elements.append(Spacer(1, 20))
            
            # Page number
            page_num = Paragraph(f"Page {i+1}", styles['Normal'])
            page_num.alignment = 1
            story_elements.append(page_num)
            
            if i < len(pages) - 1:
                story_elements.append(PageBreak())
        
        # Build PDF
        doc.build(story_elements)
        return pdf_path
    
    def process_story(self, pdf_file, character_image, character_name: str,
                     character_age: int, character_gender: str, art_style: str, output_folder: str,
                     language: str = "English", progress_bar=None) -> Dict:
        """
        Main processing function with fail-fast image generation
        """
        results = {
            "success": False,
            "pdf_path": None,
            "pages_processed": 0,
            "error": None,
            "processing_time": 0
        }
        
        start_time = time.time()
        
        try:
            # Step 1: Extract text from PDF
            if progress_bar:
                progress_bar.progress(10, "Extracting text from PDF...")
            
            story_text, detected_lang = self.extract_text_from_pdf(pdf_file)
            story_pages = self.split_into_pages(story_text)
            
            # Step 2: Generate images for each page (fail fast if any fails)
            if progress_bar:
                progress_bar.progress(30, "Generating illustrations...")
            
            image_paths = []
            for i, page_text in enumerate(story_pages):
                if progress_bar:
                    progress = 30 + (50 * (i + 1) / len(story_pages))
                    progress_bar.progress(int(progress), f"Generating image {i+1}/{len(story_pages)}...")
                
                image_path = self.generate_image_for_page(
                    character_image, character_name, character_age, character_gender, page_text, art_style
                )
                
                if image_path is None:
                    # FAIL FAST - don't continue without images
                    results["error"] = "Image generation not supported with current model. Please use a model that supports image generation like DALL-E or Stable Diffusion."
                    if progress_bar:
                        progress_bar.progress(0, "Error: Image generation failed")
                    return results
                
                image_paths.append(image_path)
            
            # Step 3: Create PDF booklet (only if all images generated)
            if progress_bar:
                progress_bar.progress(85, "Creating PDF booklet...")
            
            story_title = f"{character_name}'s Adventure"
            pdf_path = self.create_pdf_booklet(
                story_title, character_name, story_pages, image_paths, output_folder, language
            )
            
            if progress_bar:
                progress_bar.progress(100, "Complete!")
            
            results.update({
                "success": True,
                "pdf_path": pdf_path,
                "pages_processed": len(story_pages),
                "processing_time": time.time() - start_time
            })
            
        except Exception as e:
            results["error"] = str(e)
            if progress_bar:
                progress_bar.progress(0, f"Error: {str(e)}")
        
        return results