from fastapi import APIRouter

router = APIRouter()

@router.get("/health", summary="Health Check")
async def check_health() -> dict[str, str]:
    """
    Check if the application is running smoothly.
    """
    return {"status": "OK", "message": "Service is healthy"}
