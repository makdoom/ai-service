# from app.services.video import download_video
import requests
import logging
from app.services.vector_db import store_in_chroma
from app.services.transcribe import transcribe_audio
from app.services.video import extract_audio
from app.core.config import settings
import os
from app.schemas.payloads import IngestVideoRequest

logger = logging.getLogger(__name__)


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
    chunks, full_text = transcribe_audio(audio_path)

    # store in chromadb
    store_in_chroma(chunks, request.video_id)

    # generate summary and questions
    from app.services.video_insights import generate_video_insights
    import asyncio
    
    insights = asyncio.run(generate_video_insights(full_text))
    summary = insights.get("summary", "")
    start_questions = insights.get("start_questions", [])

  except Exception as e:
    logger.error(f"Background processing failed: {e}")
    status = "FAILED"
    summary = ""
    start_questions = []
  
  finally:
    # Cleanup
    # if os.path.exists(video_path):
    #   os.remove(video_path)
    # if os.path.exists(audio_path):
    #   os.remove(audio_path)
        
    # Call Webhook
    try:
      payload = {
          "video_id": request.video_id, 
          "status": status,
          "summary": summary,
          "start_questions": start_questions
      }
      requests.post(request.webhook_url, json=payload)
      logger.info(f"✅ Webhook sent to {request.webhook_url} with insights.")
    except Exception as e:
      logger.error(f"Failed to trigger webhook: {e}")



