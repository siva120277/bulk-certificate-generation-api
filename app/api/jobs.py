import os
import io
import zipfile
from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.job import Job, JobStatus
from app.models.certificate import Certificate, CertificateStatus
from app.schemas.job import JobCreateRequest, JobResponse, JobDetailResponse, JobProgressSummary
from app.schemas.certificate import CertificateResponse
from app.services.worker import process_bulk_job

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def build_job_response(job: Job) -> JobResponse:
    """Helper to convert Job ORM object to JobResponse schema."""
    percentage = 0.0
    if job.total_count > 0:
        percentage = round((job.processed_count / job.total_count) * 100.0, 2)

    progress = JobProgressSummary(
        total=job.total_count,
        processed=job.processed_count,
        successful=job.success_count,
        failed=job.failed_count,
        percentage=percentage
    )

    return JobResponse(
        id=job.id,
        title=job.title,
        event_name=job.event_name,
        issue_date=job.issue_date or date.today().isoformat(),
        template_name=job.template_name,
        status=job.status,
        progress=progress,
        created_at=job.created_at,
        updated_at=job.updated_at
    )


@router.post("", response_model=JobResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_generation_job(
    request: JobCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts a certificate generation request for a list of recipients.
    Validates input data, stores job record, and starts asynchronous background processing.
    """
    issue_date_val = request.issue_date or date.today().isoformat()

    # 1. Create Job record
    job = Job(
        title=request.title,
        event_name=request.event_name,
        issue_date=issue_date_val,
        template_name=request.template_name,
        status=JobStatus.PENDING,
        total_count=len(request.recipients),
        processed_count=0,
        success_count=0,
        failed_count=0
    )
    db.add(job)
    await db.flush()  # Populate job.id

    # 2. Create Certificate item records
    for recipient in request.recipients:
        cert = Certificate(
            job_id=job.id,
            recipient_name=recipient.name,
            recipient_email=str(recipient.email),
            custom_attributes=recipient.custom_attributes,
            status=CertificateStatus.PENDING
        )
        db.add(cert)

    await db.commit()
    await db.refresh(job)

    # 3. Schedule async background worker job
    background_tasks.add_task(process_bulk_job, job.id)

    return build_job_response(job)


@router.get("", response_model=List[JobResponse])
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List all certificate generation jobs with pagination."""
    stmt = select(Job).order_by(Job.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(stmt)
    jobs = result.scalars().all()
    return [build_job_response(j) for j in jobs]


@router.get("/{job_id}", response_model=JobDetailResponse)
async def get_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve detailed progress, metrics, and recipient list status for a specific job."""
    stmt = select(Job).options(selectinload(Job.certificates)).where(Job.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID '{job_id}' not found."
        )

    base_response = build_job_response(job)
    
    cert_responses = [
        CertificateResponse(
            id=c.id,
            job_id=c.job_id,
            recipient_name=c.recipient_name,
            recipient_email=c.recipient_email,
            status=c.status,
            error_message=c.error_message,
            file_url=f"/api/v1/certificates/{c.id}/download" if c.status == CertificateStatus.SUCCESS else None,
            created_at=c.created_at,
            updated_at=c.updated_at
        )
        for c in job.certificates
    ]

    return JobDetailResponse(
        **base_response.model_dump(),
        certificates=cert_responses
    )


@router.get("/{job_id}/download-all")
async def download_all_job_certificates(
    job_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Download a ZIP archive containing all successfully generated certificates in the job."""
    stmt = select(Job).options(selectinload(Job.certificates)).where(Job.id == job_id)
    result = await db.execute(stmt)
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    successful_certs = [c for c in job.certificates if c.status == CertificateStatus.SUCCESS and c.file_path]
    
    if not successful_certs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No successful certificates available for download in this job."
        )

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for cert in successful_certs:
            if os.path.exists(cert.file_path):
                safe_name = "".join([c if c.isalnum() or c in (" ", "_", "-") else "_" for c in cert.recipient_name])
                filename = f"Certificate_{safe_name}_{cert.id[:8]}.pdf"
                zip_file.write(cert.file_path, arcname=filename)

    zip_buffer.seek(0)
    zip_filename = f"Job_{job_id[:8]}_Certificates.zip"

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={zip_filename}"}
    )
