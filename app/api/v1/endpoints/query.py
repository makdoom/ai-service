from app.services.query_rag import query_rag
from app.schemas.payloads import QueryResponse, QueryRequest
import logging
from fastapi import Depends
from fastapi import APIRouter
from app.core.security import get_auth_token

logger = logging.getLogger(__name__)

# Protected Router
router = APIRouter(dependencies=[Depends(get_auth_token)])

@router.post("/query", summary="Query Video", response_model=QueryResponse)
async def ingest_video(request: QueryRequest):
  answer, context_used = query_rag(request.query, request.video_id)

  if not answer:
    raise HTTPException(status_code=404, detail="No relevant context found or video not indexed yet.")

  return QueryResponse(answer=answer, context_used=context_used)
  
