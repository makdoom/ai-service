
from app.utils.writer import write_all
from app.transcription.audio.vad import chunk_audio
from app.transcription.audio.vad import load_audio
from app.transcription.audio.cleaner import clean_audio_enhance
from app.transcription.audio.cleaner import clean_audio_spectral_gate
from app.transcription.audio.cleaner import clean_audio_demucs
from app.transcription.audio.normalizer import normalize_audio
from app.transcription.audio.extractor import extract_audio
from app.transcription.video.download_video import download_video
import logging
from app.transcription.whisper_engine import WhisperEngine
from app.core.config import settings
from pathlib import Path
import time

logger = logging.getLogger(__name__)


class TranscriptionPipeline:
  def __init__(
    self,
    whisper_model: str = "base", #"large-v3",
    cleaning_method: str = "enhance",
    use_vad: bool = True,
    output_formats: list[str] | None = None,
    output_dir: str | Path | None = None,
  ):
    self.whisper_model = whisper_model
    self.cleaning_method = cleaning_method
    self.use_vad = use_vad
    self.output_formats = output_formats or ["json", "srt", "txt"]
    self.output_dir = Path(output_dir) if output_dir else settings.OUTPUT_DIR

    self.whisper_engine = WhisperEngine(model_name=whisper_model)
    self._temp_files: list[Path] = []
  
  def run(self, video_url: str, input_file: str | Path) -> dict:
    input_path = Path(input_file).resolve()
    if not input_path.exists():
      raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info("=" * 60)
    logger.info("Starting transcription pipeline for: %s", input_path.name)
    logger.info("=" * 60)

    start_time = time.time()
    current_file = str(input_path)

    try:
      # current_file = self._step_download(video_url)

      current_file = self._step_extract(current_file)
      current_file = self._step_clean(current_file)
      current_file = self._step_normalize(current_file)


      audio, sr = load_audio(current_file)
      logger.info("Loaded audio: %.2fs @ %dHz", len(audio) / sr, sr)

      if self.use_vad:
        chunks = chunk_audio(audio, sr)
        chunk_list = [(c.start, c.end, c.audio) for c in chunks]
        logger.info("Processing %d VAD chunks", len(chunk_list))
        result = self.whisper_engine.transcribe_chunks(chunk_list)
      else:
        result = self.whisper_engine.transcribe_audio(audio)

      base_name = input_path.stem
      output_files = write_all(
          result, self.output_dir, base_name, self.output_formats
      )

      elapsed = time.time() - start_time

      summary = {
        "input_file": str(input_path),
        "output_files": output_files,
        "language": result.language,
        "segments": len(result.segments),
        "duration_seconds": round(elapsed, 2),
        "full_text": result.full_text,
      }

      logger.info("=" * 60)
      logger.info("Pipeline completed in %.2fs", elapsed)
      logger.info(
          "Segments: %d | Language: %s", len(result.segments), result.language
      )
      logger.info("Full transcript:\n%s", result.full_text)
      logger.info("Outputs: %s", output_files)
      logger.info("=" * 60)

    except Exception as e:
      logger.error("Pipeline failed: %s", e, exc_info=True)
      raise
    finally:
      self._cleanup_temp()
  
    
  def _step_download(self, vide_url: str) -> str:
    logger.info(" [1/4] Downloding Video...")

    downloaded_file_name = download_video(vide_url)
    return downloaded_file_name
  
  def _step_extract(self, input_file: str | Path) -> str:
    logger.info(" [2/4] Extracting Audio...")

    extracted = extract_audio(input_file)
    print(extracted, input_file)
    if extracted != input_file:
        self._temp_files.append(Path(extracted))
    return extracted
  
  def _step_normalize(self, input_file: str) -> str:
    logger.info("[4/4] Normalizing audio...")
    normalized = normalize_audio(input_file)
    self._temp_files.append(Path(normalized))
    return normalized
  
  def _step_clean(self, input_file: str) -> str:
    """ 
      Noise reduction method (default: demucs)
      - demucs (best quality, slow)
      - spectral (fast, good)
      - enhance (fastest, general)
      - none (skip)
    """

    logger.info("[3/4] Cleaning audio using %s...", self.cleaning_method)

    try:
      if self.cleaning_method == "demucs":
        cleaned = clean_audio_demucs(input_file)
      elif self.cleaning_method == "spectral":
        cleaned = clean_audio_spectral_gate(input_file)
      elif self.cleaning_method == "enhance":
        cleaned = clean_audio_enhance(input_file)
      else:
        logger.warning(
            "Unknown cleaning method '%s', skipping", self.cleaning_method
        )
        return input_file

      self._temp_files.append(Path(cleaned))
      return cleaned
    except Exception as e:
      logger.warning(
        "Cleaning failed with '%s', falling back to enhance: %s",
        self.cleaning_method,
        e,
      )
      cleaned = clean_audio_enhance(input_file)
      self._temp_files.append(Path(cleaned))
      return cleaned

  def _cleanup_temp(self):
    print("Cleaning up temp files...", self._temp_files)
    for temp_file in self._temp_files:
      try:
        if temp_file.exists():
          temp_file.unlink()
          logger.debug("Cleaned up temp file: %s", temp_file.name)
      except Exception as e:
        logger.warning("Failed to clean up %s: %s", temp_file, e)
    self._temp_files.clear()

  

