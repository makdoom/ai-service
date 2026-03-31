import logging
import asyncio
from app.core.config import settings
from app.services.vector_db import GeminiEmbeddingFunction
from app.core.clients import get_genai_client, get_chroma_client

logger = logging.getLogger(__name__)

async def query_rag(query: str, video_id: str):
  logger.info(f"\n🔍 Searching for: '{query}' in video {video_id}...")
  try:
    chroma_client = get_chroma_client()
    gemini_embedding_func = GeminiEmbeddingFunction()
    
    # collection.get_collection is sync, wrapping in thread if needed (though it's fast)
    collection = await asyncio.to_thread(chroma_client.get_collection, name=video_id, embedding_function=gemini_embedding_func)
  except Exception as error:
    logger.error(f"❌ Collection not found for {video_id}. Details: {error}")
    return None, []

  # collection.query is sync (I/O intensive), wrap in thread
  results = await asyncio.to_thread(collection.query, query_texts=[query], n_results=5)
  
  if not results["documents"] or not results["documents"][0]:
    logger.warning("❌ No relevant context found.")
    return None, []
  
  context_blocks = []
  context_used = []
  for i in range(len(results["documents"][0])):
    text = results["documents"][0][i]
    meta = results["metadatas"][0][i]
    timestamp = f"[{meta['start']:.2f}s - {meta['end']:.2f}s]"
    
    context_used.append(f"{timestamp}: {text}")
    context_blocks.append(f"[CHUNK {i+1}]\nTIMESTAMP: {timestamp}\nTEXT: {text}")

  context_text = "\n\n".join(context_blocks)

  system_prompt = (
    "You are an AI video assistant.\n"
    "Answer ONLY using the provided context.\n"
    "The context is a list of timestamped audio segments.\n"
    "You MUST find the timestamp corresponding to the specific segment where your answer is found.\n"
    "You MUST place this timestamp at the VERY END of your response.\n"
    "Example Answer: 'The grass is green. [15.0s]'\n"
    "If the answer is missing, say: 'I cannot find the answer in the video context.'\n"
    "Be concise."
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
