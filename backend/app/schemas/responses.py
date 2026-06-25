"""General API response schemas."""

from pydantic import BaseModel


class HealthCheckResponse(BaseModel):
    """Health check endpoint response."""

    status: str = "healthy"
    service: str = "CarePlus Medical Assistant"
