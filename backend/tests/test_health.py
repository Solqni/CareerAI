import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_root() -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        assert "CareerAI" in resp.json()["message"]
