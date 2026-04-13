
"""
Voice Activity Detection (VAD) using Silero VAD and audio chunking.
"""

from app.core.config import settings
from pathlib import Path
import numpy as np
import logging
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class SpeechSegment:
    start: float
    end: float
    audio: np.ndarray


def load_audio(input_file: str | Path, sample_rate: int = settings.TARGET_SAMPLE_RATE) -> tuple[np.ndarray, int]:
  import soundfile as sf

  input_path = Path(input_file).resolve()
  if not input_path.exists():
    raise FileNotFoundError(f"Audio file not found: {input_path}")

  audio, sr = sf.read(input_path, dtype="float32")

  if len(audio.shape) > 1:
    audio = audio.mean(axis=1)

  if sr != sample_rate:
    import librosa

    audio = librosa.resample(audio, orig_sr=sr, target_sr=sample_rate)
    sr = sample_rate

  return audio, sr



def chunk_audio(
  audio: np.ndarray,
  sample_rate: int = settings.TARGET_SAMPLE_RATE,
  min_duration: float = settings.CHUNK_MIN_DURATION_SEC,
  max_duration: float = settings.CHUNK_MAX_DURATION_SEC,
) -> list[SpeechSegment]:
  speech_segments = detect_speech_vad(audio, sample_rate)

  if not speech_segments:
      logger.warning("No speech detected, processing entire audio as single chunk")
      total_duration = len(audio) / sample_rate
      return [SpeechSegment(start=0.0, end=total_duration, audio=audio)]

  chunks = []

  for start, end in speech_segments:
      segment_duration = end - start

      if segment_duration <= max_duration:
          start_sample = int(start * sample_rate)
          end_sample = int(end * sample_rate)
          segment_audio = audio[start_sample:end_sample]
          chunks.append(SpeechSegment(start=start, end=end, audio=segment_audio))
      else:
          num_chunks = int(np.ceil(segment_duration / max_duration))
          chunk_duration = segment_duration / num_chunks

          for i in range(num_chunks):
              chunk_start = start + i * chunk_duration
              chunk_end = min(chunk_start + chunk_duration, end)

              start_sample = int(chunk_start * sample_rate)
              end_sample = int(chunk_end * sample_rate)
              segment_audio = audio[start_sample:end_sample]

              chunks.append(
                  SpeechSegment(
                      start=chunk_start,
                      end=chunk_end,
                      audio=segment_audio,
                  )
              )

  logger.info("Split audio into %d chunks", len(chunks))
  return chunks



def detect_speech_vad(
    audio: np.ndarray,
    sample_rate: int = settings.TARGET_SAMPLE_RATE,
    threshold: float = settings.VAD_THRESHOLD,
    min_speech_ms: int = settings.VAD_MIN_SPEECH_DURATION_MS,
    min_silence_ms: int = settings.VAD_MIN_SILENCE_DURATION_MS,
) -> list[tuple[float, float]]:
    try:
      import torch
      from silero_vad import load_silero_vad, get_speech_timestamps

      model = load_silero_vad()

      wav_tensor = torch.from_numpy(audio).float()

      speech_timestamps = get_speech_timestamps(
        wav_tensor,
        model,
        threshold=threshold,
        sampling_rate=sample_rate,
        min_speech_duration_ms=min_speech_ms,
        min_silence_duration_ms=min_silence_ms,
        return_seconds=True,
      )

      segments = [(ts["start"], ts["end"]) for ts in speech_timestamps]
      logger.info("VAD detected %d speech segments", len(segments))
      return segments

    except Exception as e:
      logger.warning("Silero VAD failed, falling back to energy-based VAD: %s", e)
      return _energy_based_vad(audio, sample_rate, threshold)


def _energy_based_vad(
    audio: np.ndarray,
    sample_rate: int,
    threshold: float,
    frame_duration_ms: int = 30,
    min_speech_ms: int = settings.VAD_MIN_SPEECH_DURATION_MS,
    min_silence_ms: int = settings.VAD_MIN_SILENCE_DURATION_MS,
) -> list[tuple[float, float]]:
  frame_size = int(sample_rate * frame_duration_ms / 1000)
  energy = np.array(
    [
      np.sum(audio[i : i + frame_size] ** 2)
      for i in range(0, len(audio) - frame_size + 1, frame_size)
    ]
  )

  energy_threshold = threshold * np.max(energy)
  is_speech = energy > energy_threshold

  min_speech_frames = int(min_speech_ms / frame_duration_ms)
  min_silence_frames = int(min_silence_ms / frame_duration_ms)

  segments = []
  in_speech = False
  speech_start = 0
  silence_counter = 0

  for i, speech in enumerate(is_speech):
    if speech:
      if not in_speech:
          speech_start = i
          in_speech = True
      silence_counter = 0
    else:
      if in_speech:
        silence_counter += 1
        if silence_counter >= min_silence_frames:
          speech_end = i - silence_counter
          duration_frames = speech_end - speech_start
          if duration_frames >= min_speech_frames:
            segments.append(
              (
                speech_start * frame_duration_ms / 1000,
                speech_end * frame_duration_ms / 1000,
              )
            )
          in_speech = False
          silence_counter = 0

  if in_speech:
    speech_end = len(is_speech)
    duration_frames = speech_end - speech_start
    if duration_frames >= min_speech_frames:
      segments.append(
        (
          speech_start * frame_duration_ms / 1000,
          speech_end * frame_duration_ms / 1000,
        )
      )

  logger.info("Energy-based VAD detected %d speech segments", len(segments))
  return segments
