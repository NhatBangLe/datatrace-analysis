import logging
import os
from typing import Any, Dict, Optional, List
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
        
        if self._mode == "persistence":
            db_dir = os.path.dirname(self._db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
                
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

    def get_filtered_traces(
        self,
        target_url: Optional[str] = None,
        vm_id: Optional[str] = None,
        min_risk_score: Optional[float] = None,
        max_risk_score: Optional[float] = None,
        has_error: Optional[bool] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> List[Dict[str, Any]]:
        if self._conn is None:
            raise RuntimeError("Database connection not established.")

        query = "SELECT * FROM traces WHERE 1=1"
        params: List[Any] = []

        if target_url:
            query += " AND target_url LIKE ?"
            params.append(f"%{target_url}%")
        if vm_id:
            query += " AND vm_id = ?"
            params.append(vm_id)
        if min_risk_score is not None:
            query += " AND risk_score >= ?"
            params.append(min_risk_score)
        if max_risk_score is not None:
            query += " AND risk_score <= ?"
            params.append(max_risk_score)
        if has_error is not None:
            if has_error:
                query += " AND vul_error IS NOT NULL AND vul_error != ''"
            else:
                query += " AND (vul_error IS NULL OR vul_error = '')"
        if start_date:
            query += " AND created_at >= CAST(? AS TIMESTAMP)"
            params.append(start_date)
        if end_date:
            query += " AND created_at <= CAST(? AS TIMESTAMP)"
            params.append(end_date)

        allowed_sort_cols = ["created_at", "risk_score", "duration"]
        if sort_by in allowed_sort_cols:
            order = "ASC" if sort_order.lower() == "asc" else "DESC"
            query += f" ORDER BY {sort_by} {order}"
        else:
            query += " ORDER BY created_at DESC"

        query += f" LIMIT {limit} OFFSET {offset}"

        result = self._conn.execute(query, params).fetch_df()
        
        if result.empty:
            return []
            
        return result.to_dict(orient="records")  # type: ignore

    def get_filtered_files(
        self,
        sha256_hash: Optional[str] = None,
        mime_type: Optional[str] = None,
        trace_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        if self._conn is None:
            raise RuntimeError("Database connection not established.")

        query = """
            SELECT tf.*, t.target_url, t.vm_id 
            FROM trace_files tf
            JOIN traces t ON tf.trace_id = t.id
            WHERE 1=1
        """
        params: List[Any] = []

        if sha256_hash:
            query += " AND tf.sha256_hash = ?"
            params.append(sha256_hash)
        if mime_type:
            query += " AND tf.mime_type = ?"
            params.append(mime_type)
        if trace_id:
            query += " AND tf.trace_id = ?"
            params.append(trace_id)

        query += f" ORDER BY tf.created_at DESC LIMIT {limit} OFFSET {offset}"

        result = self._conn.execute(query, params).fetch_df()
        
        if result.empty:
            return []
            
        return result.to_dict(orient="records")  # type: ignore

    def get_stats_by_domain(self) -> List[Dict[str, Any]]:
        if self._conn is None:
            raise RuntimeError("Database connection not established.")

        query = """
            SELECT 
                regexp_extract(target_url, '^(?:https?://)?([^:/]+)', 1) AS domain,
                COUNT(*) AS trace_count,
                AVG(risk_score) AS average_risk_score,
                COUNT(vul_error) AS error_count
            FROM traces 
            GROUP BY domain 
            ORDER BY trace_count DESC
        """
        result = self._conn.execute(query).fetch_df()
        
        if result.empty:
            return []
            
        return result.to_dict(orient="records")  # type: ignore

    def get_stats_by_vm(self) -> List[Dict[str, Any]]:
        if self._conn is None:
            raise RuntimeError("Database connection not established.")

        query = """
            SELECT 
                vm_id,
                COUNT(*) AS trace_count,
                AVG(risk_score) AS average_risk_score,
                AVG(duration) AS average_duration,
                COUNT(vul_error) AS error_count
            FROM traces 
            GROUP BY vm_id 
            ORDER BY trace_count DESC
        """
        result = self._conn.execute(query).fetch_df()
        
        if result.empty:
            return []
            
        return result.to_dict(orient="records")  # type: ignore

    def get_trends(self, interval: str = 'day') -> List[Dict[str, Any]]:
        if self._conn is None:
            raise RuntimeError("Database connection not established.")

        query = f"""
            SELECT 
                date_trunc('{interval}', created_at) AS interval_time,
                COUNT(*) AS trace_count,
                AVG(risk_score) AS average_risk_score
            FROM traces 
            GROUP BY interval_time 
            ORDER BY interval_time ASC
        """
        result = self._conn.execute(query).fetch_df()
        
        if result.empty:
            return []
            
        # Convert timestamp to string for JSON serialization compatibility
        result['interval_time'] = result['interval_time'].astype(str)
        return result.to_dict(orient="records")  # type: ignore
