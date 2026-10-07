import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_generation_job_success(async_client: AsyncClient):
    payload = {
        "title": "Certificate of Achievement",
        "event_name": "Full Stack Engineering Workshop 2026",
        "issue_date": "2026-10-07",
        "recipients": [
            {
                "name": "Alice Smith",
                "email": "alice@example.com",
                "custom_attributes": {"score": "95%"}
            },
            {
                "name": "Bob Jones",
                "email": "bob@example.com"
            }
        ]
    }

    response = await async_client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()

    assert "id" in data
    assert data["title"] == payload["title"]
    assert data["event_name"] == payload["event_name"]
    assert data["status"] in ["PENDING", "PROCESSING", "COMPLETED"]
    assert data["progress"]["total"] == 2
    assert data["progress"]["processed"] >= 0


@pytest.mark.asyncio
async def test_list_jobs(async_client: AsyncClient):
    # Create a job first
    payload = {
        "title": "Listing Test Job",
        "event_name": "Event",
        "recipients": [{"name": "User 1", "email": "user1@example.com"}]
    }
    await async_client.post("/api/v1/jobs", json=payload)

    response = await async_client.get("/api/v1/jobs")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["title"] == "Listing Test Job"
