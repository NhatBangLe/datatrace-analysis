from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.helpers import setup_logging
from src.repositories.duckdb import DuckDBRepository
from src.services.s3_storage import S3StorageService
from src.services.duckdb_analytics import DuckDBAnalyticsService
from src.routers.trace import router as trace_router
from src.routers.analysis import router as analysis_router

# Initialize dependencies
duckdb_repo = DuckDBRepository()

s3_service = S3StorageService()
analytics_service = DuckDBAnalyticsService(duckdb_repo=duckdb_repo)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize logging
    setup_logging()

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
