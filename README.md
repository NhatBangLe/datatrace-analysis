# DataTrace Analysis (DTA) Project

This project implements the backend for a security data lake, designed to analyze system-level impacts of visiting suspicious URLs. It combines FastAPI for a robust API, SeaweedFS for S3-compatible storage, and DuckDB for fast local analytics.

## Architecture Overview

The system follows a "Dirty-to-Clean" pipeline:
1.  **Transmission (API):** The VM securely pushes the captured data bundle to the DTA FastAPI endpoint.
2.  **Storage (SeaweedFS):** The API stores the raw binary data (e.g., PCAP, Procmon logs) in SeaweedFS.
3.  **Indexing (DuckDB):** The API extracts key metadata (IPs, hashes, timestamps, URLs) and indexes it in a local DuckDB database.
4.  **Analysis (Researcher):** Researchers can query the DuckDB database directly (e.g., via Jupyter notebooks) for statistical insights.

## Components

*   **FastAPI (`src/main.py`):** The core API for data ingestion and querying.
*   **SeaweedFS:** S3-compatible object storage for raw trace files.
*   **DuckDB:** An in-process SQL OLAP database for metadata indexing and fast analytics.
*   **boto3:** Python library for interacting with SeaweedFS (as an S3 endpoint).

## Setup and Installation

### Prerequisites

*   Python 3.8+
*   Docker (recommended for SeaweedFS)

### 1. SeaweedFS Setup (using Docker)

Run SeaweedFS with master, volume, and S3 gateway. For example:

```bash
docker run -d --name seaweedfs -p 9333:9333 -p 8333:8333 -p 8080:8080 chrislusf/seaweedfs:latest \
    master -defaultReplication=1 -volumeSizeLimitMB=1000 \
    & docker run -d --name seaweedfs-volume --network container:seaweedfs chrislusf/seaweedfs:latest volume \
    & docker run -d --name seaweedfs-s3 --network container:seaweedfs -p 8333:8333 chrislusf/seaweedfs:latest s3
```

Or check `docker-compose.yml` for more details.


Ensure a bucket named `datatrace-raw` is created (e.g., via `s3cmd` or `mc` client, or it will be created on first upload by `boto3`).

### 2. Python Environment

```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuration

Create a `src/.env` file or set environment variables for sensitive settings.
Read `src/.env.example` file to get more details.

### 4. Run the FastAPI Application

```bash
fastapi run ./src/main.py
```

The API will be accessible at `http://localhost:8000`.

## API Endpoints

### `POST /trace/upload`

Uploads a trace file and its associated metadata.

*   **Method:** `POST`
*   **Headers:**
    *   `X-HMAC-Signature`: HMAC-SHA256 signature of the request body, using `HMAC_SECRET_KEY`.
*   **Form Data:**
    *   `file`: The raw trace file (`UploadFile`).
    *   `target_url`: The URL visited during the trace (`str`).
    *   `vm_id`: Identifier of the VM (`str`).
*   **Response:** `{"message": "Trace uploaded and indexed successfully", "trace_id": "...", "s3_key": "..."}`

### `GET /trace/{trace_id}/stats`

Retrieves immediate statistics for a specific trace.

*   **Method:** `GET`
*   **Path Parameters:**
    *   `trace_id`: The SHA256 hash of the trace file.
*   **Response:** JSON object containing trace metadata.

### `GET /analysis/summary`

Retrieves aggregate statistics across all indexed traces.

*   **Method:** `GET`
*   **Response:** `{"total_traces": ..., "average_risk_score": ...}`

## Development Notes

*   **Security Hardening:** The `POST /trace/upload` endpoint includes HMAC signing for request integrity and authentication. Ensure `HMAC_SECRET_KEY` is kept secret and robust.
*   **File Validation:** Basic file content validation is present. Further checks (e.g., magic bytes for file type, size limits) can be added.
*   **Risk Scoring:** The `risk_score` field in `TraceMetadata` is a placeholder. Implement the `RiskScore = (N_unique_ips * 0.4) + (Entropy_avg * 0.6)` calculation as part of a post-processing step or directly during ingestion if network event parsing is integrated.
*   **Network Event Parsing:** The `network_events` table is defined, but the logic to parse PCAP/log files and insert data into it is not yet implemented. This would typically involve libraries like `scapy` for PCAP or custom log parsers.
*   **Timeline Generator:** The "Timeline Generator" endpoint is not yet implemented but can be added by querying `network_events` and `traces` tables.