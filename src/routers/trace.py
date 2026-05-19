import hashlib
import uuid
import logging
from typing import Annotated, Any, Dict

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import AfterValidator
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)
from src.models.request import CreateTraceRequest
from src.models.service import Trace, TraceFile

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
async def create_trace(data: CreateTraceRequest) -> str:
    try:
        from src.main import analytics_service

        trace_metadata = Trace(
            duration=data.duration,
            vul_error=data.vul_error,
            description=data.description,
            target_url=data.target_url,
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
    except Exception as e:
        logging.error(f"Error during trace upload: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process trace: {e}",
        )


@router.post("/{trace_id}/upload")
async def upload_trace_file(
    trace_id: TraceId,
    file: Annotated[
        UploadFile, File(description="The raw trace file (e.g., PCAP, log file).")
    ],
):
    """
    Uploads a new trace file along with its metadata.
    The file content is stored in SeaweedFS, and metadata is indexed in DuckDB.
    """
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
        from src.main import s3_service, analytics_service

        mime_type = file.content_type or "application/octet-stream"

        # 3. Storage
        s3_key = s3_service.upload_file(
            file_content=file_content,
            filename=filename_in_s3,
            mime_type=mime_type,
            folder=trace_id,
        )

        # 4. Indexing
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
        logging.error(f"Error during trace upload: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process trace file: {e}",
        )


@router.get("/{trace_id}/stats")
async def get_trace_stats(trace_id: TraceId) -> Dict[str, Any]:
    """Returns immediate statistics about a specific capture."""
    try:
        from src.main import analytics_service

        stats = analytics_service.get_trace_stats(trace_id)
        if not stats:
            raise HTTPException(
                status_code=HTTP_404_NOT_FOUND, detail="Trace not found."
            )
        return stats
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error during trace upload: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process trace stats: {e}",
        )
