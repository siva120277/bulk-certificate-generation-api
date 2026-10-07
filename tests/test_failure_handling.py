import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.worker import process_bulk_job

@pytest.mark.asyncio
async def test_partial_failure_isolation(async_client: AsyncClient, db_session: AsyncSession):
    # 1. Create a job request with 3 recipients (1 configured to fail via custom_attributes)
    payload = {
        "title": "Resilience Test Job",
        "event_name": "Failure Isolation Event",
        "issue_date": "2026-10-07",
        "recipients": [
            {
                "name": "Valid Recipient 1",
                "email": "valid1@example.com"
            },
            {
                "name": "Faulty Recipient",
                "email": "faulty@example.com",
                "custom_attributes": {"simulate_failure": True}
            },
            {
                "name": "Valid Recipient 2",
                "email": "valid2@example.com"
            }
        ]
    }

    create_res = await async_client.post("/api/v1/jobs", json=payload)
    assert create_res.status_code == 202
    job_id = create_res.json()["id"]

    # 2. Directly execute worker function using the test db_session
    await process_bulk_job(job_id, db=db_session)

    # 3. Verify Job progress and status
    status_res = await async_client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    job_data = status_res.json()

    assert job_data["status"] == "PARTIALLY_FAILED"
    assert job_data["progress"]["total"] == 3
    assert job_data["progress"]["successful"] == 2
    assert job_data["progress"]["failed"] == 1

    # Check recipient statuses
    certs = {c["recipient_email"]: c for c in job_data["certificates"]}
    assert certs["valid1@example.com"]["status"] == "SUCCESS"
    assert certs["valid2@example.com"]["status"] == "SUCCESS"
    assert certs["faulty@example.com"]["status"] == "FAILED"
    assert "Simulated certificate generation failure" in certs["faulty@example.com"]["error_message"]
