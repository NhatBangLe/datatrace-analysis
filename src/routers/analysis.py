import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Response
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from src.models.analysis import (
    AnalysisSummaryResponse,
    TraceResponse,
    FileSearchResponse,
    DomainStatsResponse,
    VMStatsResponse,
    TrendStatsResponse,
)
import pandas as pd

router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
    responses={
        HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        HTTP_401_UNAUTHORIZED: {"description": "Unauthorized"},
        HTTP_404_NOT_FOUND: {"description": "Not found"},
        HTTP_500_INTERNAL_SERVER_ERROR: {"description": "Internal server error"},
    },
)


@router.get("/summary", response_model=AnalysisSummaryResponse)
async def get_analysis_summary():
    """Returns aggregate statistics across all traces."""
    try:
        from src.main import analytics_service

        summary = analytics_service.get_analysis_summary()
        return summary
    except Exception as e:
        logging.error(f"Error getting analysis summary: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process analysis summary: {e}",
        )

@router.get("/traces", response_model=List[TraceResponse])
async def get_traces(
    target_url: Optional[str] = Query(None, description="Filter by target URL substring"),
    vm_id: Optional[str] = Query(None, description="Filter by VM ID"),
    min_risk_score: Optional[float] = Query(None, description="Minimum risk score"),
    max_risk_score: Optional[float] = Query(None, description="Maximum risk score"),
    has_error: Optional[bool] = Query(None, description="Filter traces with vulnerability errors"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD HH:MM:SS)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD HH:MM:SS)"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("created_at", description="Sort field: created_at, risk_score, duration"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
):
    """Retrieve and filter traces."""
    try:
        from src.main import analytics_service
        traces = analytics_service.get_filtered_traces(
            target_url=target_url,
            vm_id=vm_id,
            min_risk_score=min_risk_score,
            max_risk_score=max_risk_score,
            has_error=has_error,
            start_date=start_date,
            end_date=end_date,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        return traces
    except Exception as e:
        logging.error(f"Error getting traces: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve traces: {e}",
        )

@router.get("/files", response_model=List[FileSearchResponse])
async def get_files(
    sha256_hash: Optional[str] = Query(None, description="Filter by SHA256 Hash"),
    mime_type: Optional[str] = Query(None, description="Filter by MIME type"),
    trace_id: Optional[str] = Query(None, description="Filter by Trace ID"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Search for captured files and their trace context."""
    try:
        from src.main import analytics_service
        files = analytics_service.get_filtered_files(
            sha256_hash=sha256_hash,
            mime_type=mime_type,
            trace_id=trace_id,
            limit=limit,
            offset=offset,
        )
        return files
    except Exception as e:
        logging.error(f"Error getting files: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve files: {e}",
        )

@router.get("/stats/by-domain", response_model=List[DomainStatsResponse])
async def get_stats_by_domain():
    """Aggregate trace statistics grouped by domain."""
    try:
        from src.main import analytics_service
        return analytics_service.get_stats_by_domain()
    except Exception as e:
        logging.error(f"Error getting domain stats: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process domain stats: {e}",
        )

@router.get("/stats/by-vm", response_model=List[VMStatsResponse])
async def get_stats_by_vm():
    """Aggregate trace statistics grouped by VM."""
    try:
        from src.main import analytics_service
        return analytics_service.get_stats_by_vm()
    except Exception as e:
        logging.error(f"Error getting VM stats: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process VM stats: {e}",
        )

@router.get("/trends", response_model=List[TrendStatsResponse])
async def get_trends(
    interval: str = Query("day", description="Aggregation interval: hour, day, week")
):
    """Time-series activity trends for traces."""
    try:
        from src.main import analytics_service
        return analytics_service.get_trends(interval=interval)
    except Exception as e:
        logging.error(f"Error getting trends: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process trends: {e}",
        )

@router.get("/export")
async def export_csv(
    target_url: Optional[str] = Query(None),
    vm_id: Optional[str] = Query(None),
    min_risk_score: Optional[float] = Query(None),
):
    """Export filtered traces as a CSV file."""
    try:
        from src.main import analytics_service
        traces = analytics_service.get_filtered_traces(
            target_url=target_url,
            vm_id=vm_id,
            min_risk_score=min_risk_score,
            limit=100000, # Large limit for export
            offset=0
        )
        if not traces:
            return Response(content="No traces found", media_type="text/plain", status_code=404)
        
        df = pd.DataFrame(traces)
        csv_data = df.to_csv(index=False)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=traces_export.csv"}
        )
    except Exception as e:
        logging.error(f"Error exporting traces: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export traces: {e}",
        )
