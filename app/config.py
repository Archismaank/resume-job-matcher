# app/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load the .env file
load_dotenv()


class Settings(BaseSettings):
    # AI provider keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # Adzuna API
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""

    # JSearch RapidAPI
    jsearch_api_key: str = ""

    # AI provider
    ai_provider: str = "openai"

    # App settings
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # JWT Auth settings
    secret_key: str = "change-this-to-a-long-random-secret-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 10080  # 7 days

    # This is the modern Pydantic V2 way of configuring settings
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()