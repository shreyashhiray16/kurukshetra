from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> project root is three levels up
_ROOT_ENV = Path(__file__).resolve().parents[3] / ".env"
_BACKEND_ENV = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Career Coach"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./career_coach.db"
    
    # API Keys & Webhook Secrets
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    LLM_PROVIDER: str = "auto"
    # Gemini models
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GEMINI_FALLBACK_MODELS: str = "gemini-3-flash-preview,gemma-4-26b-a4b-it"
    # Groq models
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_FALLBACK_MODELS: str = "qwen/qwen3.8-27b,openai/gpt-oss-20b"
    LLM_MAX_RETRIES: int = 1
    GITHUB_TOKEN: str = ""
    GITHUB_WEBHOOK_SECRET: str = "test-webhook-secret-key-12345"
    YOUTUBE_API_KEY: str = ""
    
    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:1200",
        "http://127.0.0.1:1200",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]

    # Root .env is listed last so the key you edit there wins over backend/.env
    model_config = SettingsConfigDict(
        env_file=(str(_BACKEND_ENV), str(_ROOT_ENV)),
        extra="allow",
    )

settings = Settings()
