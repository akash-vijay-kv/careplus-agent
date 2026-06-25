"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings sourced from environment or .env file."""

    database_url: str = "postgresql+psycopg://careplus:careplus_secret@localhost:5432/careplus"
    openai_api_key: str = ""
    app_name: str = "CarePlus Medical Assistant"
    debug: bool = False
    default_user_id: int = 1

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
