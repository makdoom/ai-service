
from app.core.config import settings
from pathlib import Path
import logging
import subprocess

logger = logging.getLogger(__name__)


SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv"}
SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}


def is_audio_file(filepath: str | Path) -> bool:
    return Path(filepath).suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS

def is_video_file(filepath: str | Path) -> bool:
    return Path(filepath).suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS

def extract_audio(input_file: str | Path, output_file:str | Path | None = None) -> str:
  input_path = Path(input_file).resolve()
  if not input_path.exists():
    raise FileNotFoundError(f"Input file not found: {input_path}")

  if is_audio_file(input_path):
    logger.info("Input is already audio, skipping extraction: %s", input_path.name)
    return str(input_path)

  if not is_video_file(input_path):
    raise ValueError(f"Unsupported file format: {input_path.suffix}")

  if output_file is None:
    output_file = settings.TEMP_DIR / f"{input_path.stem}_extracted.wav"
  else:
    output_file = Path(output_file)

  output_file.parent.mkdir(parents=True, exist_ok=True)

  cmd = [
    settings.FFMPEG_PATH,
    "-y",
    "-i",
    str(input_path),
    "-vn",
    "-acodec",
    "pcm_s16le",
    "-ar",
    "48000",
    "-ac",
    "1",
    str(output_file),
  ]

  logger.info("Extracting audio from video: %s", input_path.name)
  logger.debug("FFmpeg command: %s", " ".join(cmd))

  try:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=True,
        timeout=600,
    )
    logger.info("Audio extracted successfully: %s", output_file.name)
    return str(output_file)
  except subprocess.CalledProcessError as e:
      logger.error("FFmpeg extraction failed: %s", e.stderr)
      raise RuntimeError(f"Audio extraction failed: {e.stderr}") from e
  except subprocess.TimeoutExpired:
      logger.error("FFmpeg extraction timed out")
      raise RuntimeError("Audio extraction timed out after 600s") from None