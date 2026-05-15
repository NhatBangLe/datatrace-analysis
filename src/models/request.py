from typing import Optional

from pydantic import BaseModel, Field


class CreateTraceRequest(BaseModel):
    target_url: str = Field(description="The URL that was visited.")
    vm_id: str = Field(
        description="Identifier of the VM.", min_length=1, max_length=100
    )
    duration: Optional[int] = Field(None, description="Duration of the trace.")
    vul_error: Optional[str] = Field(None, description="Vulnerability error.")
    description: Optional[str] = Field(None, description="Description of the trace.")
    risk_score: Optional[float] = Field(
        None, description="Calculated risk score for the trace."
    )
