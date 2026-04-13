import logging
import asyncio
from app.core.config import settings
from app.services.vector_db import GeminiEmbeddingFunction
from app.core.clients import get_genai_client, get_chroma_client

logger = logging.getLogger(__name__)

def to_timestamp(seconds: float) -> str:
  mins = int(seconds // 60)
  secs = int(seconds % 60)
  return f"{mins}:{secs:02d}"

async def query_rag(query: str, video_id: str):
  logger.info(f"\n🔍 Searching for: '{query}' in video {video_id}...")
  try:
    chroma_client = get_chroma_client()
    gemini_embedding_func = GeminiEmbeddingFunction()
    
    collection = await asyncio.to_thread(chroma_client.get_collection, name=video_id, embedding_function=gemini_embedding_func)
  except Exception as error:
    logger.error(f"❌ Collection not found for {video_id}. Details: {error}")
    return None, []

  results = await asyncio.to_thread(collection.query, query_texts=[query], n_results=5)
  
  if not results["documents"] or not results["documents"][0]:
    logger.warning("❌ No relevant context found.")
    return None, []
  
  context_blocks = []
  context_used = []
  seen_context = set()
  
  for i in range(len(results["documents"][0])):
    meta = results["metadatas"][0][i]
    chunk_type = meta.get("type", "micro")
    
    # Priority Context: If it's a micro chunk, the real context is its macro parent
    if chunk_type == "micro":
        context_text = meta.get("macro_parent", results["documents"][0][i])
    else:
        context_text = results["documents"][0][i]
        
    if context_text in seen_context:
        continue
    seen_context.add(context_text)
    
    start_ts = to_timestamp(meta['start'])
    end_ts = to_timestamp(meta['end'])
    display_ts = f"({start_ts}-{end_ts})"
    
    context_used.append(f"{display_ts}: {context_text[:100]}...") # Log summary
    context_blocks.append(f"[CONTEXT BLOCK {len(context_blocks)+1}]\nSOURCE TIMESTAMP: {display_ts}\nTEXT: {context_text}")

  context_text = "\n\n".join(context_blocks)
  logger.info(f"📚 Context retrieval complete. Found {len(context_blocks)} distinct context blocks.")

  system_prompt = (
    "You are an AI Video Assistant that answers questions based on a provided timestamped transcript.\n"
    "Your goal is to provide accurate, helpful, and concise answers using ONLY the context provided.\n\n"

    "Context Format:\n"
    "- You will receive context blocks containing text prepended with internal markers like [XX.Xs] (decimal seconds).\n"
    "- High-precision citations are required for all facts.\n\n"

    "Instructions:\n"
    "1. Citations:\n"
    "- Every fact or claim MUST be immediately followed by a citation in (M:SS) format.\n"
    "- Convert the decimal [XX.Xs] markers into standard (M:SS) format. (Example: [75.0s] becomes (1:15)).\n"
    "- If a specific internal marker is available for a fact, always prefer it for pinpoint accuracy.\n\n"

    "2. Synthesis & Context:\n"
    "- Combine multiple relevant points into a coherent, organized response.\n"
    "- Start with a clear and direct answer to the user's question.\n"
    "- Use the surrounding context within the larger context blocks to provide better nuance and depth.\n\n"

    "3. Constraints:\n"
    "- Maintain a professional and objective tone suitable for any video content (tutorials, podcasts, news, etc.).\n"
    "- If the answer is not explicitly found in the context, respond EXACTLY with: 'I cannot find the answer in the video context.'\n\n"

    "Answer:"
  )

  genai_client = get_genai_client()

  for attempt in range(3):
    try:
      # Use Async client (aio)
      response = await genai_client.aio.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=f"{context_text}\n\nQuestion: {query}",
        config={"system_instruction": system_prompt}
      )
      return response.text, context_used
    except Exception as e:
      if attempt == 2:
          logger.error(f"❌ Error generating response: {e}")
          raise e
      await asyncio.sleep(2 ** attempt)
