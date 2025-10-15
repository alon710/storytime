"""
Image generation utilities using Google Gemini
"""

import logging
from typing import Literal
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class ImageGenerationOutput(BaseModel):
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
    if not api_key:
        raise ValueError("Google API key is required for image generation")

    if reference_image_urls is None:
        reference_image_urls = []

    logger.info(
        f"Generating image with model={model}, references={len(reference_image_urls)}, prompt_length={len(prompt)}"
    )

    llm = ChatGoogleGenerativeAI(
        google_api_key=api_key,
        model=model,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )

    content_parts = [{"type": "text", "text": prompt}]

    for image_url in reference_image_urls:
        content_parts.append({"type": "image_url", "image_url": {"url": image_url}})

    multimodal_message = HumanMessage(content=content_parts)

    try:
        response = llm.invoke([multimodal_message], generation_config=dict(response_modalities=["TEXT", "IMAGE"]))

        if not isinstance(response.content, list):
            raise ValueError(f"Unexpected response format: {type(response.content)}")

        image_base64 = _extract_image_base64_from_response(response.content)

        return ImageGenerationOutput(
            image_base64=image_base64,
            mime_type="image/png",
            prompt_used=prompt,
        )

    except Exception as e:
        logger.error(f"Image generation failed: {type(e).__name__}: {str(e)}", exc_info=True)
        raise ValueError(f"Failed to generate image: {str(e)}") from e


def _extract_image_base64_from_response(response_content: list) -> str:
    for part in response_content:
        if isinstance(part, dict):
            if "image_url" in part and "url" in part["image_url"]:
                image_data_url = part["image_url"]["url"]

                return image_data_url.split(",")[-1]

            elif "inline_data" in part:
                return part["inline_data"].get("data", "")

    raise ValueError("Response does not contain image data")
