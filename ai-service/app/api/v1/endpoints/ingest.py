from app.services.background_video_processing import background_video_processing
from fastapi import BackgroundTasks
import logging
from fastapi import Depends
from fastapi import APIRouter
from app.core.security import get_auth_token
from app.schemas.payloads import IngestVideoResponse, IngestVideoRequest

logger = logging.getLogger(__name__)

# Protected Router
router = APIRouter(dependencies=[Depends(get_auth_token)])


@router.post("/ingest-video", summary="Ingest Video", response_model=IngestVideoResponse)
async def ingest_video(request: IngestVideoRequest, background_tasks: BackgroundTasks):
    """
    Ingest video into the system.
    TODO: need to validate video and webhook url
    """
    logger.info(f"Video ingestion triggered using token")

    background_tasks.add_task(background_video_processing, request)
    return IngestVideoResponse(status="Processing started", message="Video is being downloaded and indexed in the background.")
