
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
  PROJECT_NAME: str = "Video RAG FastAPI"
  API_V1_STR: str = "/api/v1"

  # Base directories
  BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
  TEMP_DIR: Path = BASE_DIR / "temp"
  OUTPUT_DIR: Path = BASE_DIR / "output"
  CHROMA_DB_PATH: Path = BASE_DIR / "chroma_db"


  # Audio normalization settings
  TARGET_SAMPLE_RATE: int = 16000
  TARGET_CHANNELS: int = 1  # mono
  TARGET_FORMAT: str = "wav"
  
  # Demucs settings
  DEMUCS_MODEL: str = "mdx_extra_q"
  DEMUCS_DEVICE: str = "cpu"  # auto-detect GPU if available

  # VAD settings
  VAD_THRESHOLD: float = 0.5
  VAD_MIN_SPEECH_DURATION_MS: int = 250
  VAD_MIN_SILENCE_DURATION_MS: int = 300

  # Chunking settings
  CHUNK_MIN_DURATION_SEC: int = 10
  CHUNK_MAX_DURATION_SEC: int = 30

  # Whisper settings
  WHISPER_MODEL: str = "small" #"large-v3"
  WHISPER_LANGUAGE: str = "hi"
  WHISPER_BEAM_SIZE: int = 5
  WHISPER_BEST_OF: int = 5
  WHISPER_TEMPERATURE: float = 0.0
  WHISPER_COMPUTE_TYPE: str = "int8"  # "float16" for GPU, "int8" for CPU

  # Output settings
  OUTPUT_FORMATS: list[str] = ["json", "srt", "txt"]

  # Logging
  LOG_LEVEL: str = "INFO"
  LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
  LOG_DATEFMT: str = "%Y-%m-%d %H:%M:%S"

  # FFmpeg
  FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "ffmpeg")
  FFPROBE_PATH: str = os.getenv("FFPROBE_PATH", "ffprobe")

  # Gemini Models
  GOOGLE_GEMINI_API_KEY: str
  GEMINI_MODEL: str = "gemini-2.5-flash-lite" 
  EMBEDDING_MODEL: str = "gemini-embedding-001"
  
  # Security
  CORS_ORIGINS: list[str] = ["*"]
  AUTH_TOKEN: str

  # You can add DB URIs, secret keys, etc. below:
  # DATABASE_URI: str = "postgresql://user:pass@localhost:5432/db"
  # OPENAI_API_KEY: str | None = None

  model_config = SettingsConfigDict(
      env_file=".env",
      env_ignore_empty=True,
      extra="ignore",
  )
    

settings = Settings()