import numpy as np
import logging
import os
import warnings
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sklearn.metrics.pairwise import cosine_distances
from sentence_transformers import SentenceTransformer

# Silence HuggingFace and SentenceTransformers warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"
warnings.filterwarnings("ignore", category=UserWarning, module="huggingface_hub")
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

# Initialize the tiny local model. This model is efficient for topic shift detection.
try:
    logger.info("Loading Advanced Semantic Model (all-MiniLM-L6-v2)...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
except Exception as e:
    logger.error(f"❌ Failed to load SentenceTransformer model. Details: {e}")
    raise e

@dataclass
class TranscriptSegment:
    text: str
    start: float
    end: float

@dataclass
class Sentence:
    text: str
    start: float
    end: float

def clean_and_reconstruct_sentences(segments: List[Any]) -> List[Sentence]:
    """
    Groups raw segments into logical sentences based on punctuation.
    Maintains start/end timestamps from the original segments.
    """
    sentences = []
    current_text = []
    current_start = None
    
    sentence_endings = ('.', '!', '?', '।', '…') # Support various punctuation marks
    
    for seg in segments:
        text = seg.text.strip().replace('\n', ' ')
        if current_start is None:
            current_start = seg.start
            
        current_text.append(text)
        
        # Check if the segment ends a sentence
        if text.rstrip().endswith(sentence_endings):
            full_text = " ".join(current_text)
            sentences.append(Sentence(text=full_text, start=round(current_start, 2), end=round(seg.end, 2)))
            current_text = []
            current_start = None
            
    # Handle any remaining text as a final sentence
    if current_text:
        sentences.append(Sentence(text=" ".join(current_text), start=round(current_start, 2), end=round(segments[-1].end, 2)))
        
    return sentences

def advanced_chunk_transcript(segments: List[Any],  percentile_threshold=80,  max_duration=100,  overlap_count=2) -> Dict[str, List[Dict]]:
    """
    Advanced YouTube-style chunking pipeline:
    Transcript -> Clean Text -> Embeddings -> Semantic Split -> Overlap -> Micro/Macro
    """
    logger.info("🧠 Running Advanced Semantic Chunking...")
    
    # 1. Clean and Reconstruct Sentences (preserving metadata)
    sentences = clean_and_reconstruct_sentences(segments)
    
    if not sentences:
        return {"micro": [], "macro": []}
    
    if len(sentences) == 1:
        single = {"text": sentences[0].text, "start": sentences[0].start, "end": sentences[0].end}
        return {"micro": [single], "macro": [single]}

    # 2. Get embeddings for each sentence for similarity logic
    sentence_texts = [s.text for s in sentences]
    embeddings = model.encode(sentence_texts)
    
    # 3. Calculate cosine distances between consecutive sentences
    distances = []
    for i in range(len(embeddings) - 1):
        emb1 = embeddings[i].reshape(1, -1)
        emb2 = embeddings[i+1].reshape(1, -1)
        dist = cosine_distances(emb1, emb2)[0][0]
        distances.append(dist)
    
    # 4. Semantic Split Points based on distance peaks
    threshold = np.percentile(distances, percentile_threshold)
    
    # 5. Build Macro Chunks with Time-based limits
    macro_chunks = []
    current_sentences = []
    
    def save_macro(sent_list):
        if not sent_list: return
        
        start = sent_list[0].start
        end = sent_list[-1].end
        # Format text with internal markers for LLM visibility
        text_with_ts = "\n".join([f"[{s.start}s]: {s.text}" for s in sent_list])
        macro_chunks.append({
            "text": text_with_ts,
            "start": round(start, 2),
            "end": round(end, 2),
            "sentence_count": len(sent_list)
        })

    for i, s in enumerate(sentences):
        current_sentences.append(s)
        
        is_last = (i == len(sentences) - 1)
        is_topic_shift = False
        if not is_last:
            is_topic_shift = distances[i] > threshold
            
        current_duration = current_sentences[-1].end - current_sentences[0].start
        is_too_long = current_duration >= max_duration
        
        if is_last or is_topic_shift or is_too_long:
            save_macro(current_sentences)
            current_sentences = []
            
    # 6. Linking Micro Chunks to Macro Blocks
    # This architecture provides high-precision search with broad context.
    
    final_output = {"micro": [], "macro": macro_chunks}
    
    # Re-map each micro sentence to its parent macro text
    curr_macro_idx = 0
    for s in sentences:
        # Avoid out-of-bounds error and keep within macro boundaries 
        # (small allowance for precision)
        if s.start >= macro_chunks[curr_macro_idx]["end"] - 0.01 and curr_macro_idx < len(macro_chunks) - 1:
            curr_macro_idx += 1
            
        final_output["micro"].append({
            "text": s.text,
            "start": s.start,
            "end": s.end,
            "macro_parent": macro_chunks[curr_macro_idx]["text"]
        })
        
    logger.info(f"✅ Generated {len(final_output['micro'])} micro chunks linked to {len(macro_chunks)} macro blocks.")
    return final_output
