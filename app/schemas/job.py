from typing import List, Optional
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.schemas.certificate import RecipientInput, CertificateResponse


class JobCreateRequest(BaseModel):
    title: str = Field(..., description="Certificate title (e.g. Certificate of Completion)", json_schema_extra={"example": "Certificate of Excellence"})
    event_name: str = Field(..., description="Event or Course Name", json_schema_extra={"example": "Python & Fast API Masterclass 2026"})
    issue_date: Optional[str] = Field(default=None, description="Date of issuance (YYYY-MM-DD or readable string)", json_schema_extra={"example": "2026-10-07"})
    template_name: str = Field(default="default", description="Predefined template design to use", json_schema_extra={"example": "default"})
    recipients: List[RecipientInput] = Field(..., min_length=1, description="List of recipient items for bulk generation")

    @field_validator("title", "event_name")
    def string_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or blank")
        return v.strip()

    @field_validator("issue_date", mode="before")
    def set_default_date(cls, v: Optional[str]) -> str:
        if not v or not str(v).strip():
            return date.today().isoformat()
        return str(v).strip()


class JobProgressSummary(BaseModel):
    total: int
    processed: int
    successful: int
    failed: int
    percentage: float


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    event_name: str
    issue_date: str
    template_name: str
    status: str
    progress: JobProgressSummary
    created_at: datetime
    updated_at: datetime


class JobDetailResponse(JobResponse):
    certificates: List[CertificateResponse] = []
