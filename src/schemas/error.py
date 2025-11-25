"""Error response schemas"""

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Single validation error detail"""

    field: str | None = Field(None, description="Field that caused the error")
    message: str = Field(..., description="Error message")
    type: str | None = Field(None, description="Error type")


class ErrorResponse(BaseModel):
    """Structured error response"""

    error: str = Field(..., description="Error type identifier")
    message: str = Field(..., description="User-friendly error message")
    details: list[ErrorDetail] | dict[str, Any] | None = Field(
        None, description="Additional error context"
    )
    request_id: str | None = Field(None, description="Request ID for tracking")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "validation_error",
                "message": "Invalid data provided",
                "details": [
                    {
                        "field": "weight_lbs",
                        "message": "Weight must be between 50 and 500 lbs",
                        "type": "value_error",
                    }
                ],
            }
        }
