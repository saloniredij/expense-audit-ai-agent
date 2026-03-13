import pytest
from httpx import AsyncClient, ASGITransport
import uuid

from src.main import app
from src.core.database import db_manager

# Since we don't have the async test DB fully configured without Docker, 
# these tests focus on the Pydantic schema validation and route existence.

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_create_user_validation_error():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Missing required email field
        response = await ac.post("/v1/users/", json={})
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_ingest_transactions_validation_error():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        invalid_payload = {
            "account_id": "not-a-uuid",
            "transactions": []
        }
        response = await ac.post("/v1/transactions/ingest", json=invalid_payload)
    assert response.status_code == 422
