from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """Standard successful response"""

    success: bool = True
    message: str = "OK"
    data: T | None = None


class ErrorResponseModel(BaseModel):
    """Standard error response"""

    success: bool = False
    message: str
    data: dict[str, object] | None = None
