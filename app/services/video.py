import requests
from ast import Expression
import logging
from moviepy import VideoFileClip
import os

logger = logging.getLogger(__name__)

def download_video(video_url: str, video_path: str):
  logger.info(f"⬇️ Downloading video from {video_url} to {video_path}...")

  try:
    response = requests.get(video_url, stream=True)
    response.raise_for_status()
    with open(video_path, 'wb') as f:
      for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
    
    logger.info("✅ Download complete.")
  except Expression as error:
    logger.error(f"❌ Failed to download video: {error}")
    raise e

def extract_audio(video_path: str, audio_path: str):
  logger.info(f"🎬 Extracting audio from '{video_path}'...")
  try:
    clip = VideoFileClip(video_path)
    clip.audio.write_audiofile(audio_path, logger=None)
    clip.close()
    
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 1024:
      raise ValueError("Extracted audio is exceptionally small or missing.")

    logger.info("✅ Audio extracted successfully.")
  except Exception as e:
    logger.error(f"❌ Error extracting audio: {e}")
    raise e

  
