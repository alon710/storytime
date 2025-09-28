from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from core.settings import settings
from core.session import session_context
from core.logger import logger
from core.temp_files import temp_file_manager
from typing import Optional
import base64
import os


@tool(description=settings.tools.images_generator.tool_description)
def generate_image(prompt: str, reference_images: Optional[list[str]] = None) -> list[str]:
    logger.info("Image generation started", has_reference=bool(reference_images))
    message_content = [{"type": "text", "text": prompt}]
    try:
        if reference_images:
            for img_path in reference_images:
                if os.path.exists(img_path):
                    with open(img_path, "rb") as f:
                        img_data = base64.b64encode(f.read()).decode()
                        message_content.append(
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}}
                        )

        image_llm = ChatGoogleGenerativeAI(
            model=settings.tools.images_generator.model_name,
            google_api_key=settings.tools.images_generator.api_key.get_secret_value(),
            temperature=settings.tools.images_generator.temperature,
            max_output_tokens=settings.tools.images_generator.max_output_tokens,
        )

        message = HumanMessage(content=message_content)
        generation_config = {"response_modalities": ["TEXT", "IMAGE"]}
        response = image_llm.invoke(input=[message], generation_config=generation_config)

        generated_image_paths = []
        if isinstance(response.content, list):
            for block in response.content:
                if isinstance(block, dict) and "image_url" in block:
                    image_data = block["image_url"]["url"].split(",")[-1]

                    temp_path = temp_file_manager.save_from_base64(image_data, prefix="generated_image_")

                    session_context.add_artifacts("images", [temp_path])
                    session_context.add_artifacts("available_images", temp_path)
                    generated_image_paths.append(temp_path)
                    logger.info("Image generated and saved to temp file", path=temp_path)

        return generated_image_paths

    except Exception as e:
        logger.error("Image generation failed", error=str(e))
        return []
