from src.repositories.duckdb import DuckDBRepository
from src.services.s3_storage import S3StorageService
from src.services.duckdb_analytics import DuckDBAnalyticsService

# Initialize singletons
_duckdb_repo = DuckDBRepository()
_s3_service = S3StorageService()
_analytics_service = DuckDBAnalyticsService(duckdb_repo=_duckdb_repo)


def get_duckdb_repository() -> DuckDBRepository:
    """Returns the DuckDB repository singleton."""
    return _duckdb_repo


def get_s3_storage_service() -> S3StorageService:
    """Returns the S3 storage service singleton."""
    return _s3_service


def get_analytics_service() -> DuckDBAnalyticsService:
    """Returns the DuckDB analytics service singleton."""
    return _analytics_service
