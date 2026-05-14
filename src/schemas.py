from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


# --- Request Models ---
class TraceUploadRequest(BaseModel):
    target_url: str = Field(
        ..., description="The URL that was visited during the trace."
    )
    vm_id: str = Field(
        ...,
        description="Identifier for the Virtual Machine where the trace was captured.",
    )
    # The actual file content will be sent as a FastAPI UploadFile


# --- Data Models (for internal use/DuckDB) ---
class TraceMetadata(BaseModel):
    id: str = Field(
        ...,
        description="Unique identifier for the trace (e.g., SHA256 hash of the file).",
    )
    file_path: str = Field(..., description="Path to the raw file in SeaweedFS.")
    target_url: str = Field(..., description="The URL that was visited.")
    vm_id: str = Field(..., description="Identifier of the VM.")
    timestamp: datetime = Field(..., description="Timestamp of the upload.")
    sha256_hash: str = Field(..., description="SHA256 hash of the uploaded file.")
    risk_score: Optional[float] = Field(
        None, description="Calculated risk score for the trace."
    )


class NetworkEvent(BaseModel):
    trace_id: str = Field(..., description="Foreign key to the trace metadata.")
    src_ip: str
    dst_ip: str
    port: int
    entropy: float
    # Add other relevant network fields as needed
