"""Project API Models."""

from pydantic import BaseModel, Field


class AnalyzeProjectRequest(BaseModel):
    """Request model for starting an analysis on a local path."""

    local_path: str = Field(
        ..., description="Absolute path to the local repository.", examples=["/path/to/repo"]
    )


class AnalyzeProjectResponse(BaseModel):
    """Response model for starting an analysis."""

    execution_id: str = Field(
        ...,
        description="The unique identifier for the execution session.",
        examples=["123e4567-e89b-12d3-a456-426614174000"],
    )
    status: str = Field(
        ..., description="Initial status of the execution.", examples=["PENDING", "RUNNING"]
    )
