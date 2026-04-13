
from fastapi import APIRouter
from fastapi import BackgroundTasks
from app.schemas.payloads import IngestVideoRequest, IngestVideoResponse
from app.services.initiate_transcription import initiate_transcription

# router = APIRouter(dependencies=[Depends(get_auth_token)])
router = APIRouter()

@router.post("/ingest-video", summary="Ingest Video", response_model=IngestVideoResponse)
async def ingest_video(
  request: IngestVideoRequest,
  background_tasks: BackgroundTasks
):
  """ Ingest video into the system """

  # Initiate background task
  background_tasks.add_task(
    initiate_transcription,
    request
  )

  return IngestVideoResponse(
    status="Processing started",
    message="Video is being downloaded and indexed in the background."
  )