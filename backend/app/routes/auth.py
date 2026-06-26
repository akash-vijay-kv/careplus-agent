"""Authentication API endpoints."""

import base64
import json

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter()


def _create_token(user_id: int, email: str) -> str:
    """Create a base64-encoded authentication token.

    Parameters
    ----------
    user_id : int
        The authenticated user's ID.
    email : str
        The authenticated user's email.

    Returns
    -------
    str
        Base64-encoded token string.
    """
    payload = json.dumps({"user_id": user_id, "email": email})
    return base64.b64encode(payload.encode()).decode()


def decode_token(token: str) -> dict | None:
    """Decode a base64-encoded authentication token.

    Parameters
    ----------
    token : str
        The base64-encoded token string.

    Returns
    -------
    dict | None
        Decoded payload with user_id and email, or None if invalid.
    """
    try:
        payload = base64.b64decode(token.encode()).decode()
        return json.loads(payload)
    except Exception:
        return None


@router.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    """Authenticate a user with email and password.

    Parameters
    ----------
    request : LoginRequest
        Login credentials.
    db : Session
        Injected database session (auto-closed by FastAPI dependency).

    Returns
    -------
    LoginResponse
        User info and authentication token.

    Raises
    ------
    HTTPException
        401 if credentials are invalid.
    """
    user = db.query(User).filter(User.email == request.email).first()

    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not bcrypt.checkpw(
        request.password.encode(), user.password_hash.encode()
    ):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = _create_token(user.id, user.email)

    return LoginResponse(
        user_id=user.id,
        name=f"{user.first_name} {user.last_name}",
        email=user.email,
        token=token,
    )
