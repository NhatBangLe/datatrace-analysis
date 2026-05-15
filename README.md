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

Check API Docs at `http://localhost:8000/docs`.
