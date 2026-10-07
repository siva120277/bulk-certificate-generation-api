from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class RecipientInput(BaseModel):
    name: str = Field(..., description="Full name of the recipient", json_schema_extra={"example": "Jane Doe"})
    email: EmailStr = Field(..., description="Email address of the recipient", json_schema_extra={"example": "jane.doe@example.com"})
    custom_attributes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom metadata for template rendering")

    @field_validator("name")

    def name_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Recipient name cannot be empty or blank")
        return v.strip()


class CertificateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    job_id: str
    recipient_name: str
    recipient_email: str
    status: str
    error_message: Optional[str] = None
    file_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CertificateDetailResponse(CertificateResponse):
    custom_attributes: Optional[Dict[str, Any]] = None
    download_url: Optional[str] = None
    verification_url: Optional[str] = None
    checksum: Optional[str] = None
