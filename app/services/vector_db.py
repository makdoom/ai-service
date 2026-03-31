import logging
import uuid
import chromadb
from google import genai
from app.core.config import settings

logger = logging.getLogger(__name__)

class GeminiEmbeddingFunction(chromadb.EmbeddingFunction):
  def __init__(self):
    self.client = genai.Client(api_key=settings.GOOGLE_GEMINI_API_KEY)

  def __call__(self, input: chromadb.Documents):
    for attempt in range(3):
      try:
        response = self.client.models.embed_content(
          model="gemini-embedding-001",
          contents=input,
          config={"task_type":"RETRIEVAL_DOCUMENT"}
        )
        return [e.values for e in response.embeddings]
      except Exception as e:
        import time
        if attempt == 2:
            raise e
        time.sleep(2 ** attempt)

def store_in_chroma(chunks: list, video_id: str):
    logger.info(f"🧠 Generating Gemini embeddings for video {video_id}...")
    try:
        client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        gemini_embedding_func = GeminiEmbeddingFunction()
        
        # collection per video_id
        collection = client.get_or_create_collection(name=video_id, embedding_function=gemini_embedding_func)

        documents, metadatas, ids = [], [], []
        for i, chunk in enumerate(chunks):
            if not chunk["text"]: continue
            documents.append(chunk["text"])
            metadatas.append({"start": chunk["start"], "end": chunk["end"], "chunk_index": i})
            ids.append(str(uuid.uuid4()))

        if not documents:
            logger.warning("⚠️ No valid documents to store.")
            return

        BATCH_SIZE = 50
        for i in range(0, len(documents), BATCH_SIZE):
            collection.add(
                documents=documents[i:i+BATCH_SIZE],
                metadatas=metadatas[i:i+BATCH_SIZE],
                ids=ids[i:i+BATCH_SIZE]
            )
        logger.info(f"✅ Successfully indexed {len(documents)} chunks.")
    except Exception as error:
        logger.error(f"❌ Error connecting to Chroma. Details: {error}")
        raise error
