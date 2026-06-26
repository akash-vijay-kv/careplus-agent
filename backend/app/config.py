"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings sourced from environment or .env file."""

    database_url: str = "postgresql+psycopg://careplus:careplus_secret@localhost:5432/careplus"
    openai_api_key: str = ""
    app_name: str = "CarePlus Medical Assistant"
    debug: bool = False
    default_user_id: int = 1
    cors_origins: str = "http://localhost:3000,http://frontend:3000"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def cors_origin_list(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
