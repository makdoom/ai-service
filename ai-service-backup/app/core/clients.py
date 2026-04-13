import chromadb
from google import genai
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class ClientManager:
    _chroma_client = None
    _genai_client = None

    @classmethod
    def get_chroma_client(cls):
        if cls._chroma_client is None:
            logger.info("Initializing ChromaDB PersistentClient...")
            cls._chroma_client = chromadb.PersistentClient(path=settings.CHROMA_DB_PATH)
        return cls._chroma_client

    @classmethod
    def get_genai_client(cls):
        if cls._genai_client is None:
            logger.info("Initializing Google GenAI Client...")
            cls._genai_client = genai.Client(api_key=settings.GOOGLE_GEMINI_API_KEY)
        return cls._genai_client

# Shortcut functions
def get_chroma_client():
    return ClientManager.get_chroma_client()

def get_genai_client():
    return ClientManager.get_genai_client()
