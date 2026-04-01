import logging
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

def transcribe_audio(audio_path: str):
    logger.info(f"🎙️ Transcribing audio from '{audio_path}'...")
    try:
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_path, beam_size=5, vad_filter=True)

        raw_segments = []
        for segment in segments:
            text = segment.text.strip().replace("\n", " ")
            if not text or len(text) < 3: continue
            raw_segments.append(segment)
        
        from app.services.advanced_chunking import advanced_chunk_transcript
        smart_chunks = advanced_chunk_transcript(raw_segments)
        return smart_chunks
    except Exception as e:
        logger.error(f"❌ Error transcribing audio: {e}")
        raise e
