from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred", "details": str(exc)},
    )

def configure_exception_handlers(app: FastAPI):
    app.add_exception_handler(Exception, global_exception_handler)
