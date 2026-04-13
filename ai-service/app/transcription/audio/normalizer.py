"""
Audio normalization to target sample rate, channels, and format.
"""

from app.core.config import settings
import logging
import subprocess
from pathlib import Path


logger = logging.getLogger(__name__)


def normalize_audio(
    input_file: str | Path,
    output_file: str | Path | None = None,
    sample_rate: int = settings.TARGET_SAMPLE_RATE,
    channels: int = settings.TARGET_CHANNELS,
    output_format: str = settings.TARGET_FORMAT,
) -> str:
    input_path = Path(input_file).resolve()

    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if output_file is None:
        output_file = input_path.with_name(f"{input_path.stem}_normalized.{output_format}")
    else:
        output_file = Path(output_file)

    output_file.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        settings.FFMPEG_PATH,
        "-y",
        "-i",
        str(input_path),
        "-ar",
        str(sample_rate),
        "-ac",
        str(channels),
        "-af",
        "loudnorm=I=-20:TP=-2.0:LRA=11",
        "-f",
        output_format,
        str(output_file),
    ]

    logger.info(
        "Normalizing audio: %s -> %s (%dkHz, %dch, %s)",
        input_path.name,
        output_file.name,
        sample_rate,
        channels,
        output_format,
    )
    logger.debug("FFmpeg command: %s", " ".join(cmd))

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=300,
        )
        logger.info("Audio normalized successfully: %s", output_file.name)
        return str(output_file)
    except subprocess.CalledProcessError as e:
        logger.error("Audio normalization failed: %s", e.stderr)
        raise RuntimeError(f"Audio normalization failed: {e.stderr}") from e
    except subprocess.TimeoutExpired:
        logger.error("Audio normalization timed out")
        raise RuntimeError("Audio normalization timed out after 300s") from None
