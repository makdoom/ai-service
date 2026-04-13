
from app.transcription.transcription_pipeline import TranscriptionPipeline
from app.schemas.payloads import IngestVideoRequest
from app.core.config import settings
import os

def initiate_transcription(request: IngestVideoRequest):
  video_path = os.path.join(settings.TEMP_DIR, f"{request.video_id}.mp4")
  audio_path = os.path.join(settings.TEMP_DIR, f"{request.video_id}.wav")

  status = 'SUCCESS'

  try:
    pipeline = TranscriptionPipeline()
    pipeline.run(str(request.video_url), str(video_path))
  except Exception as e:
    status = 'FAILED'
    # logger.error(f"Transcription failed: {e}")
    print(f"Transcription failed: {e}")
  finally:
    #Clean up
    pass