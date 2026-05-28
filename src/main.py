from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.helpers import setup_logging
from src.routers.trace import router as trace_router
from src.routers.analysis import router as analysis_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize logging
    setup_logging()

    from src.dependencies import get_duckdb_repository
    duckdb_repo = get_duckdb_repository()
    duckdb_repo.connect()
    duckdb_repo.initialize_db()

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for DataTrace Analysis (DTA) project, managing forensic data ingestion and indexing.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(trace_router)
app.include_router(analysis_router)
