from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Any
from google import genai
from google.genai import types
from jinja2 import Environment, FileSystemLoader
from app.utils.logger import logger
from google.genai.types import ContentListUnionDict


class BaseAIGenerator(ABC):
    def __init__(self, client: genai.Client, model: str):
        self.client = client
        self.model = model
        template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(template_dir)))

    def _generate_content(
        self,
        contents: ContentListUnionDict,
        response_modalities: Optional[list[str]] = None,
    ) -> Optional[Any]:
        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(response_modalities=response_modalities),
        )

        if not response or not response.candidates:
            logger.warning(
                "No response received from Gemini API",
                classname=self.__class__.__name__,
            )
            return None

        return response

    @abstractmethod
    def generate(self, *args, **kwargs):
        pass
