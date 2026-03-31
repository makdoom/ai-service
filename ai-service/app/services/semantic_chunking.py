import numpy as np
import sys
import os
import logging
import warnings
from sklearn.metrics.pairwise import cosine_distances

# Silence HuggingFace and SentenceTransformers warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")
warnings.filterwarnings("ignore", message=".*unauthenticated requests.*")
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Initialize the tiny local model. This downloads exactly once and caches.
# It runs purely on CPU and takes fractions of a second.
try:
    logger.info("Loading Semantic Model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.error(f"❌ Failed to load SentenceTransformer model. Details: {e}")
    sys.exit(1)

def semantic_chunk_transcript(segments, percentile_threshold=85, max_chunk_size=15):
    """
    Takes raw faster-whisper segments, calculates semantic distance using 
    local embeddings, and groups them into chunks based on topic shifts.
    
    Args:
        segments: Iterable of faster-whisper segment objects.
        percentile_threshold: The percentile of distance above which we split chunks.
        max_chunk_size: Maximum number of segments (usually ~3-5 seconds each) 
                        to allow in a single chunk before forcing a split.
                        15 segments ≈ 45-60 seconds max.
                        
    Returns:
        List of dicts formatted exactly like your original `chunk_transcript` output.
    """
    logger.info("🧠 Running Custom Semantic Chunking...")
    
    # We convert the generator/iterable to a static list
    try:
        segments = list(segments)
    except Exception as e:
        logger.error(f"❌ Failed to process segments iterable. Details: {e}")
        return []
    
    if not segments:
        logger.warning("⚠️ No valid segments provided to chunker.")
        return []
        
    if len(segments) == 1:
        return [{"id": "chunk_0", "text": segments[0].text.strip(), "start": round(segments[0].start, 2), "end": round(segments[0].end, 2)}]
        
    # 1. Get embeddings for all raw Whisper segments simultaneously
    segment_texts = [seg.text.strip().replace('\n', ' ') for seg in segments]
    try:
        embeddings = model.encode(segment_texts)
    except Exception as e:
        logger.error(f"❌ Failed to encode text embeddings. Details: {e}")
        # Fallback to single chunk to prevent data loss
        return [{"id": "chunk_0", "text": "\n".join(segment_texts), "start": round(segments[0].start, 2), "end": round(segments[-1].end, 2)}]
    
    # 2. Calculate cosine distance between consecutive segments
    distances = []
    for i in range(len(embeddings) - 1):
        emb1 = embeddings[i].reshape(1, -1)
        emb2 = embeddings[i+1].reshape(1, -1)
        dist = cosine_distances(emb1, emb2)[0][0]
        distances.append(dist)
        
    # 3. Determine the dynamic threshold based on percentiles
    threshold = np.percentile(distances, percentile_threshold)
    
    # 4. Assemble chunks based on the threshold
    chunks = []
    current_chunk_segments = []
    
    for i, segment in enumerate(segments):
        current_chunk_segments.append(segment)
        
        # Check if we should split AFTER this segment
        is_last_segment = (i == len(segments) - 1)
        is_topic_shift = False
        if not is_last_segment:
            is_topic_shift = distances[i] > threshold
            
        is_too_long = len(current_chunk_segments) >= max_chunk_size
        
        if is_last_segment or is_topic_shift or is_too_long:
            # Construct the cohesive chunk from all grouped segments, mapped perfectly into a line-by-line list!
            full_text = "\n".join([f"- [{round(seg.start, 2)}s]: {seg.text.strip().replace('\n', ' ')}" for seg in current_chunk_segments])
            chunk_start = current_chunk_segments[0].start
            chunk_end = current_chunk_segments[-1].end
            
            chunks.append({
                "id": f"chunk_{len(chunks)}",
                "text": full_text,
                "start": round(chunk_start, 2),
                "end": round(chunk_end, 2)
            })
            
            # Reset for the next topic
            current_chunk_segments = []
            
    logger.info(f"✅ Compressed {len(segments)} segments into {len(chunks)} true semantic chunks.")
    return chunks
