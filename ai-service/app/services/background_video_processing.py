# from app.services.video import download_video
from app.services.vector_db import store_in_chroma
from app.services.transcribe import transcribe_audio
from app.services.video import extract_audio
from app.core.config import settings
import os
from app.schemas.payloads import IngestVideoRequest


def background_video_processing(request: IngestVideoRequest):
  video_path = os.path.join(settings.TEMP_DIR, f"{request.video_id}.mp4")
  audio_path = os.path.join(settings.TEMP_DIR, f"{request.video_id}.wav")

  status = 'SUCCESS'

  try:
    os.makedirs(settings.TEMP_DIR, exist_ok=True)

    # Download video from s3 or given url
    # download_video(request.video_url, video_path)

    # extract audio from video
    extract_audio(video_path, audio_path)

    # transcribe audio
    chunks = transcribe_audio(audio_path)

    # store in chromadb
    store_in_chroma(chunks, request.video_id)

  except Exception as e:
    logger.error(f"Background processing failed: {e}")
    status = "FAILED"
  
  finally:
    # Cleanup
    if os.path.exists(video_path):
      os.remove(video_path)
    if os.path.exists(audio_path):
      os.remove(audio_path)
        
    # Call Webhook
    try:
      payload = {"video_id": request.video_id, "status": status}
      # requests.post(request.webhook_url, json=payload)
      print('Sending webhook to ', request.webhook_url)
    except Exception as e:
      logger.error(f"Failed to trigger webhook: {e}")



