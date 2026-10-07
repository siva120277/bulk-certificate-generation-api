import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_validation_empty_recipients(async_client: AsyncClient):
    payload = {
        "title": "Valid Title",
        "event_name": "Valid Event",
        "recipients": []
    }
    response = await async_client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422  # Pydantic min_length validation failure


@pytest.mark.asyncio
async def test_validation_invalid_email(async_client: AsyncClient):
    payload = {
        "title": "Valid Title",
        "event_name": "Valid Event",
        "recipients": [
            {
                "name": "John Doe",
                "email": "not-an-email"
            }
        ]
    }
    response = await async_client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_validation_blank_name(async_client: AsyncClient):
    payload = {
        "title": "Valid Title",
        "event_name": "Valid Event",
        "recipients": [
            {
                "name": "   ",
                "email": "valid@example.com"
            }
        ]
    }
    response = await async_client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_validation_blank_title(async_client: AsyncClient):
    payload = {
        "title": "",
        "event_name": "Valid Event",
        "recipients": [
            {
                "name": "Jane Doe",
                "email": "jane@example.com"
            }
        ]
    }
    response = await async_client.post("/api/v1/jobs", json=payload)
    assert response.status_code == 422
