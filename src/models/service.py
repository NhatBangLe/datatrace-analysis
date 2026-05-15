from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class TraceFile(BaseModel):
    id: Optional[str] = Field(
        default=None,
        description="Unique identifier of the file. Default is None if not saved yet.",
    )
    file_path: str = Field(description="Path to the raw file.")
    sha256_hash: str = Field(description="SHA256 hash of the uploaded file.")
    mime_type: str = Field(description="MIME type of the uploaded file.")
    created_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of the upload. Default is None if not saved yet.",
    )


class Trace(BaseModel):
    id: Optional[str] = Field(
        default=None,
        description="Unique identifier of the trace. Default is None if not saved yet.",
    )
    target_url: str = Field(description="The URL that was visited.")
    vm_id: str = Field(description="Identifier of the VM.", max_length=100)
    duration: Optional[int] = Field(None, description="Duration of the trace.")
    vul_error: Optional[str] = Field(None, description="Vulnerability error.")
    description: Optional[str] = Field(None, description="Description of the trace.")
    risk_score: Optional[float] = Field(
        None, description="Calculated risk score for the trace."
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of the upload. Default is None if not saved yet.",
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp of the last update. Default is None if not saved yet.",
    )
    files: List[TraceFile] = Field(default=[], description="List of associated files.")
