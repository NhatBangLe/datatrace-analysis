import logging

from fastapi import APIRouter, HTTPException

from fastapi import APIRouter
from starlette.status import (
    HTTP_401_UNAUTHORIZED,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

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


@router.get("/summary")
async def get_analysis_summary():
    """Returns aggregate statistics across all traces."""
    try:
        from src.main import analytics_service

        summary = analytics_service.get_analysis_summary()
        return summary
    except Exception as e:
        logging.error(f"Error during trace upload: {e}")
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process analysis summary: {e}",
        )
