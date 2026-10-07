import logging
import asyncio
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.job import Job, JobStatus
from app.models.certificate import Certificate, CertificateStatus
from app.services.pdf_generator import generate_certificate_pdf

logger = logging.getLogger("certificate_worker")


async def process_bulk_job(job_id: str, db: Optional[AsyncSession] = None):
    """
    Background worker function to process a bulk certificate generation job.
    Executes each certificate generation independently, isolating failures so valid items complete.
    """
    if db is not None:
        await _process_job_with_session(job_id, db)
    else:
        async with AsyncSessionLocal() as session:
            await _process_job_with_session(job_id, session)


async def _process_job_with_session(job_id: str, session: AsyncSession):
    try:
        # 1. Fetch Job
        result = await session.execute(select(Job).where(Job.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            logger.error(f"Job {job_id} not found for background processing.")
            return

        # Mark job as PROCESSING
        job.status = JobStatus.PROCESSING
        await session.commit()

        # 2. Fetch all PENDING certificate items for this job
        cert_result = await session.execute(
            select(Certificate).where(Certificate.job_id == job_id, Certificate.status == CertificateStatus.PENDING)
        )
        certificates = cert_result.scalars().all()

        # 3. Process each certificate individually
        for cert in certificates:
            cert.status = CertificateStatus.GENERATING
            await session.commit()

            try:
                # Check for simulated test failure trigger in custom_attributes if present
                if cert.custom_attributes and cert.custom_attributes.get("simulate_failure") is True:
                    raise ValueError("Simulated certificate generation failure for testing.")

                # Generate PDF file
                file_path, checksum = generate_certificate_pdf(
                    certificate_id=cert.id,
                    recipient_name=cert.recipient_name,
                    title=job.title,
                    event_name=job.event_name,
                    issue_date=job.issue_date,
                    custom_attributes=cert.custom_attributes
                )

                cert.status = CertificateStatus.SUCCESS
                cert.file_path = file_path
                cert.checksum = checksum
                cert.error_message = None

                job.success_count += 1
                job.processed_count += 1

            except Exception as e:
                logger.exception(f"Failed to generate certificate {cert.id} for recipient {cert.recipient_name}: {e}")
                cert.status = CertificateStatus.FAILED
                cert.error_message = str(e)

                job.failed_count += 1
                job.processed_count += 1

            await session.commit()
            await asyncio.sleep(0.001)

        # 4. Finalize Job Status
        if job.failed_count == 0:
            job.status = JobStatus.COMPLETED
        elif job.success_count > 0:
            job.status = JobStatus.PARTIALLY_FAILED
        else:
            job.status = JobStatus.FAILED

        await session.commit()
        logger.info(f"Job {job_id} completed with status {job.status}. Success: {job.success_count}, Failed: {job.failed_count}")

    except Exception as e:
        logger.exception(f"Unhandled error in job processing {job_id}: {e}")
        try:
            result = await session.execute(select(Job).where(Job.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                job.status = JobStatus.FAILED
                await session.commit()
        except Exception:
            pass
