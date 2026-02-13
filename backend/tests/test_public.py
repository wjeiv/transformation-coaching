import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_submit_contact_form(client: AsyncClient):
    resp = await client.post(
        "/api/v1/public/contact",
        json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "phone": "555-1234",
            "message": "I'm interested in coaching services for my upcoming marathon.",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_submit_contact_form_missing_fields(client: AsyncClient):
    resp = await client.post(
        "/api/v1/public/contact",
        json={"name": "Jane"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_submit_contact_form_short_message(client: AsyncClient):
    resp = await client.post(
        "/api/v1/public/contact",
        json={
            "name": "Jane",
            "email": "jane@example.com",
            "message": "Hi",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"
