import numpy as np
import logging
import os
import warnings
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from sklearn.metrics.pairwise import cosine_distances
from sentence_transformers import SentenceTransformer

# Silence HuggingFace and SentenceTransformers warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# Initialize the model at module level (singleton pattern)
try:
    logger.info("Loading Advanced Semantic Model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.error(f"❌ Failed to load SentenceTransformer model. Details: {e}")
    raise e

@dataclass(frozen=True)
class TranscriptSegment:
    text: str
    start: float
    end: float

@dataclass
class Sentence:
    text: str
    start: float
    end: float
    index: int

def clean_and_reconstruct_sentences(segments: List[Any]) -> List[Sentence]:
    """
    Groups raw Whisper segments into grammatical sentences with metadata.
    Uses regex-based boundary detection to handle abbreviations and quotes.
    """
    all_sentences: List[Sentence] = []
    buffer_text: List[str] = []
    buffer_start: Optional[float] = None
    
    # Matches sentence endings while respecting abbreviations (e.g., Mr., Dr., etc.)
    # and capturing trailing quotes/brackets.
    sentence_pattern = re.compile(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|!|।|…)\s')

    for seg in segments:
        text = seg.text.strip().replace('\n', ' ')
        if not text: continue
        
        if buffer_start is None:
            buffer_start = seg.start
            
        buffer_text.append(text)
        current_block = " ".join(buffer_text)
        
        # Split block into sentences
        found_splits = sentence_pattern.split(current_block)
        
        # If more than one sentence found, the ones before the last are complete
        if len(found_splits) > 1:
            for s_text in found_splits[:-1]:
                s_trimmed = s_text.strip()
                if not s_trimmed: continue
                all_sentences.append(Sentence(
                    text=s_trimmed,
                    start=round(buffer_start, 2),
                    end=round(seg.end, 2),
                    index=len(all_sentences)
                ))
            
            # Keep the last fragment in the buffer
            buffer_text = [found_splits[-1]]
            buffer_start = seg.start # Approximate start for the next sentence
            
    # Flush remaining buffer
    final_text = " ".join(buffer_text).strip()
    if final_text:
        all_sentences.append(Sentence(
            text=final_text,
            start=round(buffer_start if buffer_start is not None else 0.0, 2),
            end=round(segments[-1].end, 2),
            index=len(all_sentences)
        ))
        
    return all_sentences

def advanced_chunk_transcript(segments: List[Any], 
                             percentile_threshold: int = 80, 
                             max_duration: int = 120, 
                             min_duration: int = 15) -> Dict[str, List[Dict]]:
    """
    Expert hierarchical chunking pipeline with semantic splits and stability floors.
    """
    logger.info("🧠 Running Expert Semantic Chunking...")
    
    # 1. Reconstruction
    sentences = clean_and_reconstruct_sentences(segments)
    if not sentences:
        return {"micro": [], "macro": []}
    
    if len(sentences) == 1:
        s = sentences[0]
        single = {"text": s.text, "start": s.start, "end": s.end}
        return {"micro": [single], "macro": [single]}

    # 2. Embeddings (with batching for stability)
    sentence_texts = [s.text for s in sentences]
    embeddings = model.encode(sentence_texts, batch_size=32, show_progress_bar=False)
    
    # 3. Distance Calculation
    distances = []
    for i in range(len(embeddings) - 1):
        dist = cosine_distances(embeddings[i].reshape(1, -1), embeddings[i+1].reshape(1, -1))[0][0]
        distances.append(dist)
    
    # 4. Semantic Strategy
    threshold = np.percentile(distances, percentile_threshold)
    
    # 5. Assembly (Macro Blocks)
    macro_chunks: List[Dict] = []
    current_indices: List[int] = []
    
    def finalize_macro(indices: List[int]):
        if not indices: return
        s_list = [sentences[idx] for idx in indices]
        text_with_ts = "\n".join([f"[{s.start}s]: {s.text}" for s in s_list])
        macro_chunks.append({
            "text": text_with_ts,
            "start": round(s_list[0].start, 2),
            "end": round(s_list[-1].end, 2),
            "indices": indices # Primary key for Micro mapping
        })

    for i, s in enumerate(sentences):
        current_indices.append(i)
        
        is_last = (i == len(sentences) - 1)
        is_topic_shift = False if is_last else distances[i] > threshold
        
        duration = sentences[i].end - sentences[current_indices[0]].start
        is_too_long = duration >= max_duration
        
        # Split trigger, but respect the 'min_duration' floor to avoid fragmentation
        if is_last or is_topic_shift or is_too_long:
            if not is_last and duration < min_duration and not is_too_long:
                continue # Skip split if it's too early (unless forced by duration or last)
            
            finalize_macro(current_indices)
            current_indices = []
            
    # 6. Reliable Micro-to-Macro Mapping (Index-based)
    final_micro: List[Dict] = []
    for m in macro_chunks:
        m_text = m["text"]
        for idx in m["indices"]:
            s = sentences[idx]
            final_micro.append({
                "text": s.text,
                "start": s.start,
                "end": s.end,
                "macro_parent": m_text
            })
            
    # Clean up internal metadata before return
    for m in macro_chunks:
        del m["indices"]
        
    logger.info(f"✅ Success: {len(final_micro)} micro chunks mapped to {len(macro_chunks)} macro blocks.")
    return {"micro": final_micro, "macro": macro_chunks}
