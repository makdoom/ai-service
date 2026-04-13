from pydantic import BaseModel
from typing import List

class IngestVideoRequest(BaseModel):
    video_url: str
    video_id: str
    webhook_url: str

class IngestVideoResponse(BaseModel):
    status: str
    message: str

class QueryRequest(BaseModel):
    video_id: str
    query: str

class QueryResponse(BaseModel):
    answer: str
    context_used: List[str]
