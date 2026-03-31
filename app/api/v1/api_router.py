from app.api.v1.endpoints import query
from fastapi import APIRouter

from app.api.v1.endpoints import ingest
from app.api.v1.endpoints import health

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(ingest.router, tags=["ingest"])
api_router.include_router(query.router, tags=["query"])
