"""
Image Generation Tool - Reusable image generation with reference support

This tool provides a simple interface for generating images using Google's Gemini
image generation model. It can be used by any node that needs image generation
(seed images, book illustrations, etc.).
"""

import logging
from typing import Literal
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ImageGenerationInput(BaseModel):
    """Input schema for image generation"""

    prompt: str = Field(description="Detailed prompt describing the image to generate")
    reference_image_urls: list[str] = Field(
        default_factory=list, description="Optional list of reference image URLs (data:image or http URLs)"
    )
    model: str = Field(default="models/gemini-2.5-flash-image", description="Gemini model to use")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_output_tokens: int = Field(default=8192, description="Maximum output tokens")


class ImageGenerationOutput(BaseModel):
    """Output schema for image generation"""

    image_base64: str = Field(description="Generated image as base64 string (without data URL prefix)")
    mime_type: Literal["image/png", "image/jpeg"] = Field(default="image/png", description="Image MIME type")
    prompt_used: str = Field(description="The prompt that was used for generation")


def generate_image(
    prompt: str,
    reference_image_urls: list[str] | None = None,
    api_key: str | None = None,
    model: str = "models/gemini-2.5-flash-image",
    temperature: float = 0.7,
    max_output_tokens: int = 8192,
) -> ImageGenerationOutput:
    """
    Generate an image using Google's Gemini image generation model.

    This is a pure function that takes inputs and returns an image.
    It does not handle file storage or session management.

    Args:
        prompt: Detailed description of the image to generate
        reference_image_urls: Optional list of reference images (data:image or http URLs)
        api_key: Google API key (required)
        model: Gemini model name
        temperature: Temperature for generation
        max_output_tokens: Maximum tokens for output

    Returns:
        ImageGenerationOutput with base64 image data

    Raises:
        ValueError: If API key is missing or image generation fails
    """
    if not api_key:
        raise ValueError("Google API key is required for image generation")

    if reference_image_urls is None:
        reference_image_urls = []

    logger.info(
        f"Generating image with model={model}, references={len(reference_image_urls)}, prompt_length={len(prompt)}"
    )

    # Initialize Gemini model
    llm = ChatGoogleGenerativeAI(
        google_api_key=api_key,
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )

    # Build multimodal message
    content_parts = [{"type": "text", "text": prompt}]

    for image_url in reference_image_urls:
        content_parts.append({"type": "image_url", "image_url": {"url": image_url}})

    multimodal_message = HumanMessage(content=content_parts)

    # Generate image
    try:
        response = llm.invoke([multimodal_message], generation_config=dict(response_modalities=["TEXT", "IMAGE"]))

        if not isinstance(response.content, list):
            raise ValueError(f"Unexpected response format: {type(response.content)}")

        # Extract base64 image from response
        image_base64 = _extract_image_base64_from_response(response.content)

        return ImageGenerationOutput(
            image_base64=image_base64, mime_type="image/png", prompt_used=prompt  # Gemini typically returns PNG
        )

    except Exception as e:
        logger.error(f"Image generation failed: {type(e).__name__}: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to generate image: {str(e)}") from e


def _extract_image_base64_from_response(response_content: list) -> str:
    """
    Extract base64 image data from Gemini response content.

    Args:
        response_content: List of response parts from Gemini

    Returns:
        Base64 image string (without data URL prefix)

    Raises:
        ValueError: If no image is found in response
    """
    for part in response_content:
        if isinstance(part, dict):
            # Check for image_url format
            if "image_url" in part and "url" in part["image_url"]:
                image_data_url = part["image_url"]["url"]
                # Remove data:image/png;base64, prefix
                return image_data_url.split(",")[-1]
            # Check for inline_data format
            elif "inline_data" in part:
                return part["inline_data"].get("data", "")

    raise ValueError(f"No image found in response: {response_content}")
