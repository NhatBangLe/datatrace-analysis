import hashlib
import uuid
import logging
from typing import Annotated, Any, Dict

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import AfterValidator
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from src.models.request import CreateTraceRequest
from src.models.service import Trace, TraceFile
from src.dependencies import get_analytics_service, get_s3_storage_service
from src.services.s3_storage import S3StorageService
from src.services.duckdb_analytics import DuckDBAnalyticsService
from src.helpers import guess_mime_type

TraceId = Annotated[str, AfterValidator(lambda x: str(uuid.UUID(x, version=4)))]

router = APIRouter(
    prefix="/trace",
    tags=["Trace"],
    responses={
        HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        HTTP_404_NOT_FOUND: {"description": "Not found"},
        HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@router.post(path="/create", description="Create a new trace and return its ID.")
async def create_trace(
    data: CreateTraceRequest,
    analytics_service: DuckDBAnalyticsService = Depends(get_analytics_service),
) -> str:
    try:
        trace_metadata = Trace(
            duration=data.duration,
            vul_error=data.vul_error,
            description=data.description,
            target_url=str(data.target_url),
            vm_id=data.vm_id,
            risk_score=data.risk_score,
        )
        trace = analytics_service.create_trace(trace_metadata)
        if not trace:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create trace.",
            )

        return str(trace.id)
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error during trace creation: {e}", exc_info=True)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process trace metadata due to an internal error.",
        )


@router.post("/{trace_id}/upload")
async def upload_trace_file(
    trace_id: TraceId,
    file: Annotated[
        UploadFile, File(description="The raw trace file (e.g., PCAP, log file).")
    ],
    s3_service: S3StorageService = Depends(get_s3_storage_service),
    analytics_service: DuckDBAnalyticsService = Depends(get_analytics_service),
):
    """
    Uploads a new trace file along with its metadata.
    The file content is stored in SeaweedFS, and metadata is indexed in DuckDB.
    """
    # 1. Validation & stream hashing + size computation to avoid memory OOM
    sha256 = hashlib.sha256()
    file_size = 0

    await file.seek(0)
    while True:
        chunk = await file.read(65536)  # Read in 64KB chunks
        if not chunk:
            break
        sha256.update(chunk)
        file_size += len(chunk)

    if file_size == 0:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Uploaded file is empty."
        )

    sha256_hash = sha256.hexdigest()
    filename_in_s3 = f"{sha256_hash}_{file.filename}"

    # Reset file cursor so boto3 can read the stream
    await file.seek(0)

    try:
        # Determine the MIME type using registered types and fallbacks
        mime_type = guess_mime_type(file.filename, file.content_type)

        # 2. Storage using file-like object directly (streaming upload)
        s3_key = s3_service.upload_file(
            file_content=file.file,
            filename=filename_in_s3,
            mime_type=mime_type,
            folder=trace_id,
            content_length=file_size,
        )

        # 3. Indexing
        trace_file = TraceFile(
            file_path=s3_key,
            sha256_hash=sha256_hash,
            mime_type=mime_type,
        )
        saved_trace_file = analytics_service.add_trace_file(trace_id, trace_file)
        if not saved_trace_file:
            raise HTTPException(
                status_code=HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save trace file.",
            )

        return s3_key
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error during trace file upload: {e}", exc_info=True)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process trace file due to an internal error.",
        )


@router.get("/{trace_id}/stats")
async def get_trace_stats(
    trace_id: TraceId,
    analytics_service: DuckDBAnalyticsService = Depends(get_analytics_service),
) -> Dict[str, Any]:
    """Returns immediate statistics about a specific capture."""
    try:
        stats = analytics_service.get_trace_stats(trace_id)
        if not stats:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="Trace not found."
            )
        return stats
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error during trace stats retrieval: {e}", exc_info=True)
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process trace stats due to an internal error.",
        )
