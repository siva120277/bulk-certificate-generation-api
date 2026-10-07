import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.worker import process_bulk_job

@pytest.mark.asyncio
async def test_certificate_retrieval_and_download(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Create job
    payload = {
        "title": "Retrieval Test Job",
        "event_name": "API Testing Course",
        "recipients": [
            {
                "name": "Diana Prince",
                "email": "diana@example.com"
            }
        ]
    }

    create_res = await async_client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == 202
    job_id = create_res.json()["id"]

    # 2. Process job using test db_session
    await process_bulk_job(job_id, db=db_session)

    # 3. Get job details to retrieve certificate ID
    job_res = await async_client.get(f"/api/v1/jobs/{job_id}")
    assert job_res.status_code == 200
    cert_id = job_res.json()["certificates"][0]["id"]

    # 4. Get certificate metadata
    cert_res = await async_client.get(f"/api/v1/certificates/{cert_id}")
    assert cert_res.status_code == 200
    cert_meta = cert_res.json()
    assert cert_meta["recipient_name"] == "Diana Prince"
    assert cert_meta["status"] == "SUCCESS"
    assert cert_meta["download_url"] is not None

    # 5. Download certificate PDF
    download_res = await async_client.get(f"/api/v1/certificates/{cert_id}/download")
    assert download_res.status_code == 200
    assert download_res.headers["content-type"] == "application/pdf"
    assert len(download_res.content) > 1000

    # 6. Verify Certificate authenticity endpoint
    verify_res = await async_client.get(f"/api/v1/certificates/verify/{cert_id}")
    assert verify_res.status_code == 200
    verify_data = verify_res.json()
    assert verify_data["valid"] is True
    assert verify_data["recipient_name"] == "Diana Prince"

    # 7. Download all certificates ZIP
    zip_res = await async_client.get(f"/api/v1/jobs/{job_id}/download-all")
    assert zip_res.status_code == 200
    assert zip_res.headers["content-type"] == "application/zip"
    assert len(zip_res.content) > 500
