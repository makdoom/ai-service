from app.core.logging import setup_logging
from app.api.v1.router import router
from app.core.exceptions import configure_exception_handlers
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from fastapi import FastAPI

# Setup Logging
setup_logging()

def create_app() -> FastAPI: 
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
    )

    # Set up CORS middleware
    app.add_middleware(
        CORSMiddleware, 
        allow_origins=settings.CORS_ORIGINS, 
        allow_credentials=True, 
        allow_methods=["*"], 
        allow_headers=["*"]
    )



    # Global Error Handler
    configure_exception_handlers(app)

    # Include the main API router
    app.include_router(router, prefix=settings.API_V1_STR)


    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True, reload_dirs=["app"])
