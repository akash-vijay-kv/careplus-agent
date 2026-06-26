"""Authentication-related Pydantic schemas."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request with email and password."""

    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class LoginResponse(BaseModel):
    """Successful login response with user info and token."""

    user_id: int = Field(..., description="Authenticated user ID")
    name: str = Field(..., description="User full name")
    email: str = Field(..., description="User email address")
    token: str = Field(..., description="Authentication token for subsequent requests")
