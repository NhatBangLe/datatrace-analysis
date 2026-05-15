from uuid import uuid4

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class DBTraceFile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    file_path: str = Field(description="Path to the raw file.")
    sha256_hash: str = Field(description="SHA256 hash of the uploaded file.")
    mime_type: str = Field(description="MIME type of the uploaded file.")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp of the upload."
    )
    trace_id: str = Field(description="ID of the associated trace.")


class DBTrace(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    target_url: str = Field(description="The URL that was visited.")
    vm_id: str = Field(description="Identifier of the VM.", max_length=100)
    duration: Optional[int] = Field(None, description="Duration of the trace.")
    vul_error: Optional[str] = Field(None, description="Vulnerability error.")
    description: Optional[str] = Field(None, description="Description of the trace.")
    risk_score: Optional[float] = Field(
        None, description="Calculated risk score for the trace."
    )
    created_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp of the upload."
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Timestamp of the last update."
    )
