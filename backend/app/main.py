"""FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.routes.upload import router as upload_router
from app.schemas.responses import HealthCheckResponse

app = FastAPI(
    title=settings.app_name,
    description="AI-powered medical assistant for health data management",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(upload_router, prefix="/api")


@app.get("/api/health", response_model=HealthCheckResponse)
def health_check() -> HealthCheckResponse:
    """Return service health status."""
    return HealthCheckResponse()
