from abc import ABC, abstractmethod
from typing import Any, Type
import structlog
from langchain.tools import BaseTool as LangChainBaseTool
from pydantic import Field, BaseModel

logger = structlog.get_logger()


class BaseToolResponse(BaseModel):
    success: bool
    message: str


class BaseTool(LangChainBaseTool, ABC):
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    system_prompt: str = Field(..., description="System prompt for this tool")

    model_config = {"extra": "allow"}

    def __init__(self, **kwargs):
        self.logger = logger.bind(tool=self.__class__.__name__, model=self.model)

    @property
    @abstractmethod
    def model(self) -> str:
        raise NotImplementedError("Each tool must define a 'model' property")

    @property
    @abstractmethod
    def response_model(self) -> Type[BaseToolResponse]:
        raise NotImplementedError("Each tool must implement a response_model property")

    @abstractmethod
    async def _arun(self, *args, **kwargs) -> str:
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
        self.logger.error(
            "Operation failed", operation=operation, error=error, **context
        )
