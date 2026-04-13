from dataclasses import field
from dataclasses import dataclass
import numpy as np
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionSegment:
  id: int
  start: float
  end: float
  text: str
  words: list[dict] = field(default_factory=list)

  def to_dict(self) -> dict:
    return {
      "id": self.id,
      "start": round(self.start, 3),
      "end": round(self.end, 3),
      "text": self.text.strip(),
      "words": self.words,
    }


@dataclass
class TranscriptionResult:
  segments: list[TranscriptionSegment]
  language: str
  full_text: str

  def to_dict(self) -> dict:
    return {
      # "language": self.language,
      "full_text": self.full_text,
      "segments": [seg.to_dict() for seg in self.segments],
    }


class WhisperEngine:
  def __init__(
    self,
    model_name: str = settings.WHISPER_MODEL,
    # language: str = settings.WHISPER_LANGUAGE,
    beam_size: int = settings.WHISPER_BEAM_SIZE,
    best_of: int = settings.WHISPER_BEST_OF,
    temperature: float = settings.WHISPER_TEMPERATURE,
    compute_type: str = settings.WHISPER_COMPUTE_TYPE,
  ):
    self.model_name = model_name
    # self.language = language
    self.beam_size = beam_size
    self.best_of = best_of
    self.temperature = temperature
    self.compute_type = compute_type
    self._model = None

  def _load_model(self):
    if self._model is not None:
      return

    logger.info(
      "⚙️ Loading Whisper model: %s (compute_type=%s)",
      self.model_name,
      self.compute_type,
    )

    try:
      from faster_whisper import WhisperModel

      self._model = WhisperModel(
        self.model_name,
        compute_type=self.compute_type,
        cpu_threads=4,
        num_workers=1,
      )
      logger.info("✅ Whisper model loaded successfully")
    except ImportError:
      logger.error(
        "❌ faster-whisper not installed. Run: uv add faster-whisper"
      )
      raise
    except Exception as e:
      logger.error("❌ Failed to load Whisper model: %s", e)
      raise

  def transcribe_audio(self, audio: np.ndarray) -> TranscriptionResult:
    self._load_model()

    logger.info("Transcribing audio (%.2fs)", len(audio) / settings.TARGET_SAMPLE_RATE)

    segments, info = self._model.transcribe(
      audio,
      # language=self.language,
      beam_size=self.beam_size,
      best_of=self.best_of,
      temperature=self.temperature,
      vad_filter=False,
      word_timestamps=True,
    )

    logger.info(
      "Detected language: %s (probability: %.2f)",
      info.language,
      info.language_probability,
    )

    result_segments = []
    full_text_parts = []

    for idx, segment in enumerate(segments):
      words = []
      if segment.words:
        for word in segment.words:
          words.append(
            {
              "word": word.word,
              "start": round(word.start, 3),
              "end": round(word.end, 3),
              "probability": round(word.probability, 3),
            }
          )

      seg = TranscriptionSegment(
        id=idx,
        start=segment.start,
        end=segment.end,
        text=segment.text.strip(),
        words=words,
      )
      result_segments.append(seg)
      full_text_parts.append(segment.text.strip())

    result = TranscriptionResult(
      segments=result_segments,
      language=info.language,
      full_text=" ".join(full_text_parts),
    )

    logger.info("Transcription complete: %d segments", len(result_segments))
    return result


  def transcribe_chunks(
    self,
    chunks: list[tuple[float, float, np.ndarray]],
    global_offset: float = 0.0,
  ) -> TranscriptionResult:
    all_segments = []
    full_text_parts = []
    segment_id = 0
    language = "en"  # Default fallback

    for chunk_idx, (chunk_start, chunk_end, chunk_audio) in enumerate(chunks):
      logger.info(
        "Transcribing chunk %d/%d (%.2fs - %.2fs)",
        chunk_idx + 1,
        len(chunks),
        chunk_start,
        chunk_end,
      )

      result = self.transcribe_audio(chunk_audio)
      if chunk_idx == 0:
        language = result.language

      for seg in result.segments:
        seg.id = segment_id
        seg.start += chunk_start + global_offset
        seg.end += chunk_start + global_offset

        for word in seg.words:
            word["start"] += chunk_start + global_offset
            word["end"] += chunk_start + global_offset

        all_segments.append(seg)
        full_text_parts.append(seg.text)
        segment_id += 1

    result = TranscriptionResult(
      segments=all_segments,
      language=language,
      full_text=" ".join(full_text_parts),
    )

    logger.info("Chunked transcription complete: %d total segments", len(all_segments))
    return result


  