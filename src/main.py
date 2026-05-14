from contextlib import asynccontextmanager
import hashlib
import hmac
import logging
from datetime import datetime
from typing import Annotated

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Header, Depends
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_400_BAD_REQUEST,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from src.config import settings, setup_logging
from src.schemas import TraceMetadata
from src.services.s3_storage import S3StorageService
from src.services.duckdb_analytics import DuckDBAnalyticsService

# Initialize services
s3_service: S3StorageService
duckdb_service = DuckDBAnalyticsService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize logging
    setup_logging()

    duckdb_service.connect()

    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="API for DataTrace Analysis (DTA) project, managing forensic data ingestion and indexing.",
    lifespan=lifespan,
)


# Dependency for HMAC validation
async def verify_hmac_signature(
    x_hmac_signature: Annotated[str | None, Header()] = None,
    body: bytes = Depends(lambda request: request.body()),
):
    if not x_hmac_signature:
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED,
            detail="HMAC signature header 'X-HMAC-Signature' is missing.",
        )

    expected_signature = hmac.new(
        settings.HMAC_SECRET_KEY.encode("utf-8"), body, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, x_hmac_signature):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Invalid HMAC signature."
        )
    return True


@app.post("/trace/upload")
async def upload_trace(
    file: UploadFile = File(
        ..., description="The raw trace file (e.g., PCAP, log file)."
    ),
    target_url: str = Form(
        ..., description="The URL that was visited during the trace."
    ),
    vm_id: str = Form(
        ...,
        description="Identifier for the Virtual Machine where the trace was captured.",
    ),
    hmac_verified: bool = Depends(verify_hmac_signature),  # Apply HMAC validation
):
    """
    Uploads a new trace file along with its metadata.
    The file content is stored in SeaweedFS, and metadata is indexed in DuckDB.
    Requires an 'X-HMAC-Signature' header for authentication.
    """
    if (
        not hmac_verified
    ):  # This check is technically redundant due to Depends, but good for clarity
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="HMAC verification failed."
        )

    file_content = await file.read()

    # 1. Validation (Basic: file size, type can be added here)
    if not file_content:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )

    # 2. Hashing
    sha256_hash = hashlib.sha256(file_content).hexdigest()
    filename_in_s3 = f"{sha256_hash}_{file.filename}"

    try:
        # 3. Storage (SeaweedFS)
        s3_key = s3_service.upload_file(file_content, filename_in_s3)

        # 4. Indexing (DuckDB)
        trace_metadata = TraceMetadata(
            id=sha256_hash,  # Using hash as unique ID for immutability
            file_path=s3_key,
            target_url=target_url,
            vm_id=vm_id,
            timestamp=datetime.now(),
            sha256_hash=sha256_hash,
            risk_score=None,  # Risk score can be calculated asynchronously or later
        )
        duckdb_service.insert_trace_metadata(trace_metadata)

        return {
            "message": "Trace uploaded and indexed successfully",
            "trace_id": sha256_hash,
            "s3_key": s3_key,
        }
    except Exception as e:
        logging.error(f"Error during trace upload: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process trace: {e}",
        )


@app.get("/trace/{trace_id}/stats")
async def get_trace_stats(trace_id: str):
    """Returns immediate statistics about a specific capture."""
    stats = duckdb_service.get_trace_stats(trace_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Trace not found.")
    return stats


@app.get("/analysis/summary")
async def get_analysis_summary():
    """Returns aggregate statistics across all traces."""
    summary = duckdb_service.get_analysis_summary()
    return summary
