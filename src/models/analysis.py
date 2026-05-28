from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AnalysisSummaryResponse(BaseModel):
    total_traces: int = Field(description="Total number of traces.")
    average_risk_score: Optional[float] = Field(None, description="Average risk score across all traces.")

class TraceResponse(BaseModel):
    id: str
    target_url: str
    vm_id: str
    duration: Optional[int] = None
    vul_error: Optional[str] = None
    description: Optional[str] = None
    risk_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

class FileSearchResponse(BaseModel):
    id: str
    file_path: str
    sha256_hash: str
    mime_type: str
    created_at: datetime
    trace_id: str
    target_url: str
    vm_id: str

class DomainStatsResponse(BaseModel):
    domain: str
    trace_count: int
    average_risk_score: Optional[float] = None
    error_count: int

class VMStatsResponse(BaseModel):
    vm_id: str
    trace_count: int
    average_risk_score: Optional[float] = None
    average_duration: Optional[float] = None
    error_count: int

class TrendStatsResponse(BaseModel):
    interval_time: str
    trace_count: int
    average_risk_score: Optional[float] = None
