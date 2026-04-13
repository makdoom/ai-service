from app.core.config import settings
import logging
import requests

logger = logging.getLogger(__name__)

def download_video(video_url: str):
  logger.info(f"⬇️ Downloading video from {video_url} to {settings.TEMP_DIR}...")

  try:
    response = requests.get(video_url, stream=True)
    response.raise_for_status()
    with open(settings.TEMP_DIR, 'wb') as f:
      for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
    
    logger.info("✅ Download complete.")
  except Exception as error:
    logger.error(f"❌ Failed to download video: {error}")
    raise error