# FastAPI Video RAG Application: Production Architecture Plan

This plan details the scaffolding of a highly scalable, production-ready FastAPI microservice tailored for a Video RAG (Retrieval-Augmented Generation) system, utilizing `uv` for lightning-fast package management.

## User Review Required

> [!IMPORTANT]
> Please review the core technologies and folder structure proposed below. To tailor this exactly to your needs, please provide feedback on the **Open Questions** section.

## Proposed Architecture & Structure

The architecture follows a strict separation of concerns (Layered Architecture):
1. **API Layer (`api/`)**: Thin routers handling HTTP requests, responses, and dependency injection.
2. **Service Layer (`services/`)**: Heavy lifting and core business logic (RAG pipeline, video processing, vector searches).
3. **Data Layer (`schemas/`, `models/`)**: Pydantic for data validation and ORM models for database state.
4. **Core Layer (`core/`)**: Cross-cutting concerns like security, configuration, and logging.

### Recommended Folder Structure

Below is the directory tree we will create directly inside your workspace (`/Users/makdoomshaikh/Desktop/Projects/ai-service`):

```text
ai-service/
├── .env.example                # Example environment variables
├── .gitignore                  # Standard Python gitignore
├── pyproject.toml              # Project configuration and dependencies (managed by uv)
├── README.md                   # Setup and usage documentation
└── src/                        # Source code root
    ├── app/
    │   ├── __init__.py
    │   ├── main.py             # FastAPI application instance & middleware setup
    │   ├── core/               # Application-wide settings and utilities
    │   │   ├── config.py       # Pydantic BaseSettings for .env management
    │   │   ├── security.py     # Authentication (e.g., API keys, JWT validation)
    │   │   ├── exceptions.py   # Global HTTP exception handlers
    │   │   └── logging.py      # Structlog or standard logging config
    │   ├── api/                # API Routers
    │   │   ├── dependencies.py # FastAPI Depends (DB session, current user, etc.)
    │   │   └── v1/             # API Versioning
    │   │       ├── api_router.py # Aggregates all v1 routes
    │   │       └── endpoints/
    │   │           ├── health.py # Readiness and liveness probes
    │   │           ├── video.py  # Endpoints: Upload, process status, ingest
    │   │           └── chat.py   # Endpoints: RAG query, chat history
    │   ├── services/           # Core Business Logic (The RAG Engine)
    │   │   ├── rag_pipeline.py # Orchestrates retrieval and generation
    │   │   ├── vector_store.py # Client wrapper for Pinecone/Qdrant/Weaviate
    │   │   ├── llm.py          # Wrapper for OpenAI/Gemini/Anthropic
    │   │   └── video_processor.py # Audio extraction, chunking, transcription
    │   ├── models/             # Relational Database Models (SQLAlchemy ORM)
    │   │   └── base.py
    │   ├── schemas/            # Pydantic Input/Output Validation Models
    │   │   ├── chat.py
    │   │   └── video.py
    │   └── utils/              # Helper functions (e.g., file handling)
    └── tests/                  # Pytest test suite
        ├── conftest.py         # Pytest fixtures
        ├── api/                # Integration tests
        └── services/           # Unit tests for RAG logic
```

### Proposed Changes

#### [NEW] `pyproject.toml`
Initialize the project using `uv init` and add core dependencies: `fastapi`, `uvicorn`, `pydantic-settings`, etc.

#### [NEW] `src/app/main.py`
Set up the FastAPI app instance, CORS middleware, and mount the API v1 router.

#### [NEW] `src/app/core/config.py`
Set up `Settings` class using `pydantic-settings` to robustly load environment variables.

#### [NEW] Scaffolding remaining directories
Create the folder structure detailed above with `__init__.py` files.

## Open Questions

Before we proceed with the execution, please let me know:

1. **Vector Database**: Which vector store are you planning to use? (e.g., Pinecone, Qdrant, Weaviate, Milvus, or pgvector?)
2. **Relational Database**: Do you need a traditional database (e.g., PostgreSQL via SQLAlchemy) for storing user metadata, chat history, or video processing statuses?
3. **LLM Provider**: Which provider are you targeting for generation and embeddings? (e.g., OpenAI, Gemini, Anthropic?)
4. **Authentication**: How will this API be secured? (e.g., API keys, JWT from an external provider like Supabase/Clerk, or internal OAuth2?)

## Verification Plan

### Automated/Manual Verification
1. I will use `uv run uvicorn src.app.main:app --reload` to start the server.
2. I will call the `/health` endpoint to ensure the application starts and routing works correctly.
3. I'll verify the generation of the `pyproject.toml` and lock files.
