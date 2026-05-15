import logging
from typing import Any, Dict, Optional
import duckdb

from src.config import settings
from src.models.database import DBTrace, DBTraceFile

logger = logging.getLogger("DuckDBRepository")


class DuckDBRepository:
    """
    Repository to interact with the DuckDB database for metadata storage and analytics.
    """

    def __init__(self):
        self._db_path: Optional[str] = None
        self._conn: Optional[duckdb.DuckDBPyConnection] = None
        self._mode: Optional[str] = None

    def connect(self):
        """
        Connects to the DuckDB database.
        """
        self._db_path = settings.DUCKDB_DATABASE
        self._mode = "in-memory" if ":memory" in self._db_path else "persistence"
        self._conn = duckdb.connect(database=self._db_path, read_only=False)

    def initialize_db(self):
        """
        Initializes the necessary tables in the DuckDB database if they don't exist.
        """
        if self._conn is None:
            raise RuntimeError("Database connection not established.")

        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS traces (
                id VARCHAR PRIMARY KEY,
                target_url VARCHAR NOT NULL,
                vm_id VARCHAR NOT NULL,
                duration INTEGER,
                vul_error VARCHAR,
                description VARCHAR,
                risk_score DOUBLE,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            );
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS trace_files (
                id VARCHAR PRIMARY KEY,
                file_path VARCHAR NOT NULL,
                sha256_hash VARCHAR NOT NULL,
                mime_type VARCHAR NOT NULL,
                created_at TIMESTAMP NOT NULL,
                trace_id VARCHAR NOT NULL,
                FOREIGN KEY (trace_id) REFERENCES traces (id)
            );
        """)

        logger.info(f"Database initialized (mode: {self._mode}): {self._db_path}")

    def insert_trace(self, trace: DBTrace):
        """
        Inserts new trace into the 'traces' table.
        """
        if self._conn is None:
            raise RuntimeError("Database connection not established.")

        self._conn.execute(
            query="""INSERT INTO traces (id, target_url, vm_id, duration, vul_error, description, risk_score, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            parameters=(
                trace.id,
                trace.target_url,
                trace.vm_id,
                trace.duration,
                trace.vul_error,
                trace.description,
                trace.risk_score,
                trace.created_at,
                trace.updated_at,
            ),
        )
        logger.debug(f"Inserted trace metadata for ID: {trace.id}")

    def insert_trace_file(self, trace_file: DBTraceFile):
        """
        Inserts new trace file metadata into the 'trace_files' table.
        """
        if self._conn is None:
            raise RuntimeError("Database connection not established.")

        self._conn.execute(
            query="""INSERT INTO trace_files (id, file_path, sha256_hash, mime_type, created_at, trace_id)
                    VALUES (?, ?, ?, ?, ?, ?)""",
            parameters=(
                trace_file.id,
                trace_file.file_path,
                trace_file.sha256_hash,
                trace_file.mime_type,
                trace_file.created_at,
                trace_file.trace_id,
            ),
        )
        logger.debug(f"Inserted trace metadata for ID: {trace_file.id}")

    def get_trace_stats(self, trace_id: str) -> Optional[Dict[str, Any]]:
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
        return None

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
