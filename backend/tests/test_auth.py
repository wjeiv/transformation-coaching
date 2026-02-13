import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_register_athlete(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newathlete@test.com",
            "password": "password123",
            "full_name": "New Athlete",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, athlete_user: User):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "athlete@test.com",
            "password": "password123",
            "full_name": "Duplicate",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_register_weak_password(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "weak@test.com",
            "password": "short",
            "full_name": "Weak Password",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, athlete_user: User):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "athletepass123"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, athlete_user: User):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@test.com", "password": "password123"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, athlete_token: str):
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "athlete@test.com"
    assert data["role"] == "athlete"
    assert data["full_name"] == "Test Athlete"


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, athlete_user: User):
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "athletepass123"},
    )
    refresh = login_resp.json()["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )
    assert resp.status_code == 401
