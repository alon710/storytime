"""Base class for AI generators in StoryTime."""

from abc import ABC, abstractmethod
from typing import Optional, Any
from google import genai
from google.genai import types
from app.utils.logger import logger


class BaseAIGenerator(ABC):
    def __init__(self, client: genai.Client, model: str):
        self.client = client
        self.model = model

    def _with_error_handling(self, operation_name: str, func, *args, **kwargs):
        try:
            logger.debug(
                "Starting ai operation",
                extra={"operation": operation_name},
            )

            result = func(*args, **kwargs)

            if result is not None:
                logger.info(
                    "Operation was successfully completed",
                    extra={"operation": operation_name},
                )
            else:
                logger.warning(
                    "Operation completed but returned no result",
                    extra={"operation": operation_name},
                )

            return result

        except Exception as e:
            error_details = {
                "operation": operation_name,
                "error_type": type(e).__name__,
                "error_message": str(e),
            }

            if hasattr(e, "status_code"):
                error_details["status_code"] = e.status_code
            if hasattr(e, "response"):
                error_details["response"] = str(e.response)

            logger.error("AI operation failed", extra=error_details, exc_info=True)
            return None

    def _generate_content(
        self,
        contents: list[Any],
        response_modalities: Optional[list[str]] = None,
    ) -> Optional[Any]:
        if response_modalities is None:
            response_modalities = ["Text"]

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(response_modalities=response_modalities),
        )

        if not response or not response.candidates:
            logger.warning("No response received from Gemini API")
            return None

        return response

    def _extract_text_response(self, response) -> Optional[str]:
        if (
            not response
            or not response.candidates
            or not response.candidates[0].content.parts
        ):
            return None

        for part in response.candidates[0].content.parts:
            if part.text is not None:
                return part.text.strip()

        return None

    @abstractmethod
    def generate(self, *args, **kwargs):
        pass
