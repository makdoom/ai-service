"""
Audio cleaning using Demucs source separation.
Separates vocals from background noise/music.
"""

from app.core.config import settings
import logging
import shutil
import subprocess
import sys
from pathlib import Path


logger = logging.getLogger(__name__)


def clean_audio_demucs(
  input_file: str | Path,
  output_file: str | Path | None = None,
  model: str = settings.DEMUCS_MODEL,
  device: str = settings.DEMUCS_DEVICE,
) -> str:
  input_path = Path(input_file).resolve()

  if not input_path.exists():
    raise FileNotFoundError(f"Input file not found: {input_path}")

  if output_file is None:
    output_file = settings.TEMP_DIR / f"{input_path.stem}_cleaned.wav"
  else:
    output_file = Path(output_file)

  output_file.parent.mkdir(parents=True, exist_ok=True)

  demucs_output = settings.TEMP_DIR / "demucs_output"
  demucs_output.mkdir(parents=True, exist_ok=True)

  cmd = [
    sys.executable,
    "-m",
    "demucs",
    "-n",
    model,
    "--two-stems=vocals",
    f"--device={device}",
    "--out",
    str(demucs_output),
    str(input_path),
  ]

  logger.info("Running Demucs source separation on: %s", input_path.name)
  logger.debug("Demucs command: %s", " ".join(cmd))

  try:
    result = subprocess.run(
      cmd,
      capture_output=True,
      text=True,
      check=True,
      timeout=1800,
    )
    logger.info("Demucs separation completed")
  except subprocess.CalledProcessError as e:
    logger.error("Demucs separation failed: %s", e.stderr)
    raise RuntimeError(f"Demucs separation failed: {e.stderr}") from e
  except subprocess.TimeoutExpired:
    logger.error("Demucs separation timed out")
    raise RuntimeError("Demucs separation timed out after 1800s") from None

  vocals_path = demucs_output / model / input_path.stem / "vocals.wav"

  if not vocals_path.exists():
    raise FileNotFoundError(
        f"Demucs output not found at expected path: {vocals_path}"
    )

  shutil.copy2(vocals_path, output_file)
  logger.info("Cleaned vocals saved to: %s", output_file.name)

  shutil.rmtree(demucs_output, ignore_errors=True)

  return str(output_file)


def clean_audio_spectral_gate(
  input_file: str | Path,
  output_file: str | Path | None = None,
  noise_reduction_strength: float = 0.8,
) -> str:
  input_path = Path(input_file).resolve()

  if not input_path.exists():
    raise FileNotFoundError(f"Input file not found: {input_path}")

  if output_file is None:
    output_file = input_path.with_name(f"{input_path.stem}_spectral_cleaned.wav")
  else:
    output_file = Path(output_file)

  output_file.parent.mkdir(parents=True, exist_ok=True)

  try:
    import noisereduce as nr
    import soundfile as sf
    import numpy as np

    logger.info("Loading audio for spectral gating...")
    audio, sr = sf.read(str(input_path))

    if len(audio.shape) > 1:
        audio = audio.mean(axis=1)

    noise_sample = audio[: int(sr * 0.5)]
    noise_clip = np.tile(noise_sample, (audio.shape[0] // len(noise_sample) + 1,))[:audio.shape[0]]

    logger.info("Applying spectral gating noise reduction...")
    reduced = nr.reduce_noise(
      y=audio,
      sr=sr,
      y_noise=noise_clip,
      stationary=True,
      prop_decrease=noise_reduction_strength,
    )

    sf.write(str(output_file), reduced, sr)
    logger.info("Spectral gating complete: %s", output_file.name)
    return str(output_file)

  except ImportError:
    logger.warning("noisereduce not installed, using FFmpeg fallback")
    return _clean_audio_ffmpeg_filter(input_file, output_file, "highpass=f=200")


def clean_audio_highpass(
  input_file: str | Path,
  output_file: str | Path | None = None,
  cutoff_freq: int = 200,
) -> str:
  input_path = Path(input_file).resolve()

  if not input_path.exists():
    raise FileNotFoundError(f"Input file not found: {input_path}")

  if output_file is None:
    output_file = input_path.with_name(f"{input_path.stem}_highpass.wav")
  else:
    output_file = Path(output_file)

  return _clean_audio_ffmpeg_filter(
    input_file,
    output_file,
    f"highpass=f={cutoff_freq},lowpass=f=8000",
  )


def clean_audio_compress(
  input_file: str | Path,
  output_file: str | Path | None = None,
  threshold: str = "-20dB",
  ratio: float = 4.0,
) -> str:
  input_path = Path(input_file).resolve()

  if not input_path.exists():
    raise FileNotFoundError(f"Input file not found: {input_path}")

  if output_file is None:
    output_file = input_path.with_name(f"{input_path.stem}_compressed.wav")
  else:
    output_file = Path(output_file)

  return _clean_audio_ffmpeg_filter(
    input_file,
    output_file,
    f"acompressor=threshold={threshold}:ratio={ratio}:attack=5:release=50",
  )


def clean_audio_enhance(
  input_file: str | Path,
  output_file: str | Path | None = None,
) -> str:
  input_path = Path(input_file).resolve()

  if not input_path.exists():
    raise FileNotFoundError(f"Input file not found: {input_path}")

  if output_file is None:
    output_file = input_path.with_name(f"{input_path.stem}_enhanced.wav")
  else:
    output_file = Path(output_file)

  filters = (
    "highpass=f=150,"
    "lowpass=f=6000"
  )

  return _clean_audio_ffmpeg_filter(input_file, output_file, filters)


def _clean_audio_ffmpeg_filter(
  input_file: str | Path,
  output_file: str | Path,
  filters: str,
) -> str:
  output_file = Path(output_file)
  output_file.parent.mkdir(parents=True, exist_ok=True)

  cmd = [
    settings.FFMPEG_PATH,
    "-y",
    "-i",
    str(input_file),
    "-af",
    filters,
    "-ar",
    "16000",
    "-ac",
    "1",
    "-f",
    "wav",
    str(output_file),
  ]

  logger.info("Applying audio filter: %s", filters.replace(",", " | "))
  logger.debug("FFmpeg command: %s", " ".join(cmd))

  try:
    result = subprocess.run(
      cmd,
      capture_output=True,
      text=True,
      check=True,
      timeout=120,
    )
    logger.info("Audio enhancement complete: %s", output_file.name)
    return str(output_file)
  except subprocess.CalledProcessError as e:
    logger.error("FFmpeg filter failed: %s", e.stderr)
    raise RuntimeError(f"Audio enhancement failed: {e.stderr}") from e
  except subprocess.TimeoutExpired:
    logger.error("FFmpeg filter timed out")
    raise RuntimeError("Audio enhancement timed out after 120s") from None
