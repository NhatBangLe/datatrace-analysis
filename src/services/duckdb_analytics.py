import logging

from src.models.database import DBTrace, DBTraceFile
from src.repositories.duckdb import DuckDBRepository
from src.services import IAnalyticsService

logger = logging.getLogger("DuckDBAnalyticsService")


class DuckDBAnalyticsService(IAnalyticsService):
    """
    Service to interact with the DuckDB database for metadata storage and analytics.
    """

    def __init__(self, duckdb_repo: DuckDBRepository):
        self._duckdb_repo = duckdb_repo

    def create_trace(self, data):
        trace = DBTrace(
            duration=data.duration,
            vul_error=data.vul_error,
            description=data.description,
            target_url=data.target_url,
            vm_id=data.vm_id,
            risk_score=data.risk_score,
        )
        self._duckdb_repo.insert_trace(trace)
        logger.debug(f"Inserted trace metadata for ID: {data.id}")

        return data.model_copy(
            update={
                "id": trace.id,
                "created_at": trace.created_at,
                "updated_at": trace.updated_at,
            }
        )

    def add_trace_file(self, trace_id, data):
        trace_file = DBTraceFile(
            file_path=data.file_path,
            sha256_hash=data.sha256_hash,
            mime_type=data.mime_type,
            trace_id=trace_id,
        )
        try:
            self._duckdb_repo.insert_trace_file(trace_file)
            logger.debug(f"Added trace file for trace ID: {trace_id}")

            return data.model_copy(
                update={
                    "id": trace_file.id,
                    "created_at": trace_file.created_at,
                }
            )
        except Exception as e:
            logger.error(f"Failed to insert trace metadata: {e}")
            return None

    def get_trace_stats(self, trace_id, **kwargs):
        return self._duckdb_repo.get_trace_stats(trace_id)

    def get_analysis_summary(self, **kwargs):
        return self._duckdb_repo.get_analysis_summary()

    def get_filtered_traces(self, **kwargs):
        return self._duckdb_repo.get_filtered_traces(**kwargs)

    def get_filtered_files(self, **kwargs):
        return self._duckdb_repo.get_filtered_files(**kwargs)

    def get_stats_by_domain(self, **kwargs):
        return self._duckdb_repo.get_stats_by_domain()

    def get_stats_by_vm(self, **kwargs):
        return self._duckdb_repo.get_stats_by_vm()

    def get_trends(self, interval: str = 'day', **kwargs):
        return self._duckdb_repo.get_trends(interval=interval)
