from abc import ABC, abstractmethod
from typing import Any
import structlog
from langchain.tools import BaseTool as LangChainBaseTool
from pydantic import Field

logger = structlog.get_logger()


class BaseTool(LangChainBaseTool, ABC):
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    system_prompt: str = Field(..., description="System prompt for this tool")
    model: str = Field(..., description="Model to use for this tool")

    model_config = {"extra": "allow"}

    def __init__(self, model: str, **kwargs):
        super().__init__(model=model, **kwargs)
        self.logger = logger.bind(tool=self.__class__.__name__, model=model)

    @abstractmethod
    async def _arun(self, *args, **kwargs) -> Any | None:
        pass

    def _run(self, *args, **kwargs) -> Any | None:
        raise NotImplementedError("This tool only supports async execution")

    @abstractmethod
    async def execute(self, *args, **kwargs) -> Any | None:
        pass

    def log_start(self, operation: str, **context) -> None:
        self.logger.info("Operation started", operation=operation, **context)

    def log_success(self, operation: str, **context) -> None:
        self.logger.info("Operation completed", operation=operation, **context)

    def log_failure(self, operation: str, error: str, **context) -> None:
        self.logger.error("Operation failed", operation=operation, error=error, **context)