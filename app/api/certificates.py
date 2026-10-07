import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.certificate import Certificate, CertificateStatus
from app.models.job import Job
from app.schemas.certificate import CertificateDetailResponse

router = APIRouter(prefix="/certificates", tags=["Certificates"])


@router.get("/{certificate_id}", response_model=CertificateDetailResponse)
async def get_certificate(
    certificate_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve metadata and status of an individual certificate."""
    stmt = select(Certificate).options(selectinload(Certificate.job)).where(Certificate.id == certificate_id)
    result = await db.execute(stmt)
    cert = result.scalar_one_or_none()

    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found."
        )

    download_url = f"/api/v1/certificates/{cert.id}/download" if cert.status == CertificateStatus.SUCCESS else None
    verification_url = f"/api/v1/certificates/verify/{cert.id}"

    return CertificateDetailResponse(
        id=cert.id,
        job_id=cert.job_id,
        recipient_name=cert.recipient_name,
        recipient_email=cert.recipient_email,
        custom_attributes=cert.custom_attributes,
        status=cert.status,
        error_message=cert.error_message,
        file_url=download_url,
        download_url=download_url,
        verification_url=verification_url,
        checksum=cert.checksum,
        created_at=cert.created_at,
        updated_at=cert.updated_at
    )


@router.get("/{certificate_id}/download")
async def download_certificate(
    certificate_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Download the generated PDF file for a certificate."""
    stmt = select(Certificate).where(Certificate.id == certificate_id)
    result = await db.execute(stmt)
    cert = result.scalar_one_or_none()

    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate with ID '{certificate_id}' not found."
        )

    if cert.status != CertificateStatus.SUCCESS or not cert.file_path or not os.path.exists(cert.file_path):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Certificate file is not available for download. Current status: {cert.status}"
        )

    safe_name = "".join([c if c.isalnum() or c in (" ", "_", "-") else "_" for c in cert.recipient_name])
    download_filename = f"Certificate_{safe_name}_{cert.id[:8]}.pdf"

    return FileResponse(
        path=cert.file_path,
        media_type="application/pdf",
        filename=download_filename
    )


@router.get("/verify/{certificate_id}")
async def verify_certificate(
    certificate_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Public authenticity verification endpoint for a certificate.
    Returns certificate details if authentic and valid.
    """
    stmt = select(Certificate).options(selectinload(Certificate.job)).where(Certificate.id == certificate_id)
    result = await db.execute(stmt)
    cert = result.scalar_one_or_none()

    if not cert or cert.status != CertificateStatus.SUCCESS:
        return {
            "valid": False,
            "message": "Certificate not found or invalid."
        }

    return {
        "valid": True,
        "certificate_id": cert.id,
        "recipient_name": cert.recipient_name,
        "event_name": cert.job.event_name if cert.job else "Event",
        "title": cert.job.title if cert.job else "Certificate of Achievement",
        "issue_date": cert.job.issue_date if cert.job else str(cert.created_at.date()),
        "checksum": cert.checksum,
        "issued_at": cert.created_at.isoformat()
    }
