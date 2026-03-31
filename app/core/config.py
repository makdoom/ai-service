from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Video RAG FastAPI"
    API_V1_STR: str = "/api/v1"
    TEMP_DIR: Path = Path("./temp")
    GOOGLE_GEMINI_API_KEY: str
    AUTH_TOKEN: str
    CHROMA_DB_PATH: str = "./chroma_db"
    
    # Gemini Models
    GEMINI_MODEL: str = "gemini-2.5-flash" 
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    
    # Security
    CORS_ORIGINS: list[str] = ["*"]
    
    # You can add DB URIs, secret keys, etc. below:
    # DATABASE_URI: str = "postgresql://user:pass@localhost:5432/db"
    # OPENAI_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )


settings = Settings()
