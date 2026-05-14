import duckdb
import logging
from typing import Dict, Any

from src.config import settings
from src.schemas import TraceMetadata
from src.services import IAnalyticsService

logger = logging.getLogger(__name__)


class DuckDBAnalyticsService(IAnalyticsService):
    """
    Service to interact with the DuckDB database for metadata storage and analytics.
    """

    def __init__(self):
        self._db_path: str | None = None
        self._conn: duckdb.DuckDBPyConnection | None = None
        self._mode: str | None = None

    def connect(self, **kwargs):
        """
        Connects to the DuckDB database.
        """
        self._db_path = settings.DUCKDB_DATABASE
        self._mode = "in-memory" if ":memory" in self._db_path else "persistence"
        self._conn = duckdb.connect(database=self._db_path, read_only=False)

        self._initialize_db()
        logger.info(
            f"DuckDBAnalyticsService initialized for database (mode: {self._mode}): {self._db_path}"
        )

    def _initialize_db(self):
        """
        Initializes the necessary tables in the DuckDB database if they don't exist.
        """
        if self._conn is None:
            return

        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id VARCHAR PRIMARY KEY,
                file_path VARCHAR NOT NULL,
                target_url VARCHAR NOT NULL,
                vm_id VARCHAR NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                sha256_hash VARCHAR NOT NULL,
                risk_score DOUBLE
            );
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS network_events (
                trace_id VARCHAR,
                src_ip VARCHAR,
                dst_ip VARCHAR,
                port INTEGER,
                entropy DOUBLE,
                FOREIGN KEY (trace_id) REFERENCES traces(id)
            );
        """)
        logger.info("DuckDB tables 'traces' and 'network_events' ensured.")

    def insert_trace_metadata(self, metadata: TraceMetadata):
        """
        Inserts new trace metadata into the 'traces' table.
        """
        if self._conn is None:
            raise RuntimeError("Database connection not established.")

        self._conn.execute(
            "INSERT INTO traces (id, file_path, target_url, vm_id, timestamp, sha256_hash, risk_score) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                metadata.id,
                metadata.file_path,
                metadata.target_url,
                metadata.vm_id,
                metadata.timestamp,
                metadata.sha256_hash,
                metadata.risk_score,
            ),
        )
        logger.debug(f"Inserted trace metadata for ID: {metadata.id}")

    def get_trace_stats(self, trace_id: str, **kwargs) -> Dict[str, Any]:
        """
        Retrieves immediate statistics for a specific trace.
        This is a placeholder and can be expanded with more complex queries.
        """
        if self._conn is None:
            raise RuntimeError("Database connection not established.")

        result = self._conn.execute(
            f"SELECT * FROM traces WHERE id = '{trace_id}'"
        ).fetch_df()
        if not result.empty:
            return result.iloc[0].to_dict()  # type: ignore
        return {}

    def get_analysis_summary(self, **kwargs) -> Dict[str, Any]:
        """
        Retrieves aggregate statistics across all traces.
        This is a placeholder and can be expanded with more complex queries.
        """
        if self._conn is None:
            raise RuntimeError("Database connection not established.")

        total_traces_row = self._conn.execute("SELECT COUNT(*) FROM traces").fetchone()
        total_traces = total_traces_row[0] if total_traces_row else 0

        avg_risk_row = self._conn.execute(
            "SELECT AVG(risk_score) FROM traces"
        ).fetchone()
        avg_risk_score = avg_risk_row[0] if avg_risk_row else None

        return {"total_traces": total_traces, "average_risk_score": avg_risk_score}
