"""Color palette generation module for StoryTime using AI."""

from typing import Optional
from google import genai
from app.utils.logger import logger
from app.ai.base import BaseAIGenerator


class ColorGenerator(BaseAIGenerator):
    """Handles AI-powered color palette generation for child-friendly PDF layouts."""

    def __init__(self, client: genai.Client, model: str):
        """Initialize generator with GenAI client and model."""
        super().__init__(client, model)

    def generate(self, *args, **kwargs):
        """Main generation method - delegates to generate_color_palette."""
        return self.generate_color_palette(*args, **kwargs)

    def generate_color_palette(
        self,
        page_title: str,
        story_text: str,
        page_number: int,
        total_pages: int,
        character_age: int,
    ) -> Optional[dict]:
        """Generate calm, pastel color palette for a story page."""
        return self._with_error_handling(
            "color palette generation",
            self._generate_color_palette_impl,
            page_title,
            story_text,
            page_number,
            total_pages,
            character_age
        )

    def _generate_color_palette_impl(
        self,
        page_title: str,
        story_text: str,
        page_number: int,
        total_pages: int,
        character_age: int,
    ) -> Optional[dict]:
        color_prompt = f"""
        Generate a calm, pastel color palette for a children's storybook page.
        
        Page context:
        - Title: "{page_title}"
        - Story: "{story_text[:500]}..."
        - Page {page_number} of {total_pages}
        - Character age: {character_age} years old
        
        Requirements:
        - Colors must be calm, soothing, and pastel
        - Suitable for ages 2-8, especially {character_age} years old  
        - Should complement the story mood and content
        - Generate exactly 3 colors: background, banner, and accent
        - Return colors as hex codes only (e.g., #FFE4E1)
        
        Format your response as exactly 3 lines:
        background: #HEXCODE
        banner: #HEXCODE  
        accent: #HEXCODE
        
        Example:
        background: #FFF8E7
        banner: #E8F4FD
        accent: #FFE4E1
        """

        response = self._generate_content([color_prompt])
        if response is None:
            return self._fallback_colors(page_number, total_pages)
            
        color_text = self._extract_text_response(response)
        if color_text:
            colors = self._parse_colors(color_text)

            if colors:
                logger.info(
                    "Successfully generated color palette",
                    extra={
                        "page_title": page_title,
                        "page_number": page_number,
                        "colors": colors,
                    },
                )
                return colors
            else:
                logger.warning(
                    "Failed to parse AI color response, using fallback",
                    extra={"page_title": page_title, "response": color_text[:100]},
                )
                return self._fallback_colors(page_number, total_pages)
        else:
            logger.warning(
                "No color response from AI, using fallback",
                extra={"page_title": page_title},
            )
            return self._fallback_colors(page_number, total_pages)

    def _parse_colors(self, color_text: str) -> Optional[dict]:
        """Parse AI response to extract hex color codes."""
        try:
            lines = color_text.strip().split("\n")
            colors = {}

            for line in lines:
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()

                    # Extract hex code (should start with #)
                    if value.startswith("#") and len(value) == 7:
                        colors[key] = value
                    elif len(value) == 6:  # Missing #
                        colors[key] = f"#{value}"

            # Validate we have all required colors
            if all(key in colors for key in ["background", "banner", "accent"]):
                return colors

            return None

        except Exception as e:
            logger.debug(
                "Failed to parse colors", extra={"error": str(e), "text": color_text}
            )
            return None

    def _fallback_colors(self, page_number: int, total_pages: int) -> dict:
        """Generate fallback pastel colors based on page position."""
        # Cycle through predefined pastel palettes
        palettes = [
            {"background": "#FFF8E7", "banner": "#E8F4FD", "accent": "#FFE4E1"},
            {"background": "#F0FFF0", "banner": "#E6E6FA", "accent": "#F0E68C"},
            {"background": "#FDF5E6", "banner": "#F5F5DC", "accent": "#FFB6C1"},
            {"background": "#F5FFFA", "banner": "#F0F8FF", "accent": "#DDA0DD"},
            {"background": "#FFFAF0", "banner": "#FFF0F5", "accent": "#98FB98"},
        ]

        palette_index = (page_number - 1) % len(palettes)
        return palettes[palette_index]
