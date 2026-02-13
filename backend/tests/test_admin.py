import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_admin_stats(client: AsyncClient, admin_token: str):
    resp = await client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "total_users" in data
    assert "total_coaches" in data
    assert "total_athletes" in data


@pytest.mark.asyncio
async def test_admin_stats_forbidden_for_athlete(client: AsyncClient, athlete_token: str):
    resp = await client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {athlete_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_list_users(client: AsyncClient, admin_token: str, athlete_user: User):
    resp = await client.get(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "users" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_list_users_filter_by_role(client: AsyncClient, admin_token: str, coach_user: User):
    resp = await client.get(
        "/api/v1/admin/users?role=coach",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    for u in data["users"]:
        assert u["role"] == "coach"


@pytest.mark.asyncio
async def test_create_user(client: AsyncClient, admin_token: str):
    resp = await client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "newcoach@test.com",
            "password": "coachpass123",
            "full_name": "New Coach",
            "role": "coach",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newcoach@test.com"
    assert data["role"] == "coach"


@pytest.mark.asyncio
async def test_create_user_duplicate(client: AsyncClient, admin_token: str, athlete_user: User):
    resp = await client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "email": "athlete@test.com",
            "password": "password123",
            "full_name": "Dup",
            "role": "athlete",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, admin_token: str, athlete_user: User):
    resp = await client.put(
        f"/api/v1/admin/users/{athlete_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"full_name": "Updated Name"},
    )
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated Name"


@pytest.mark.asyncio
async def test_deactivate_user(client: AsyncClient, admin_token: str, athlete_user: User):
    resp = await client.put(
        f"/api/v1/admin/users/{athlete_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"is_active": False},
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, admin_token: str, athlete_user: User):
    resp = await client.delete(
        f"/api/v1/admin/users/{athlete_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_self_forbidden(client: AsyncClient, admin_token: str, admin_user: User):
    resp = await client.delete(
        f"/api/v1/admin/users/{admin_user.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_athlete_cannot_create_user(client: AsyncClient, athlete_token: str):
    resp = await client.post(
        "/api/v1/admin/users",
        headers={"Authorization": f"Bearer {athlete_token}"},
        json={
            "email": "hacker@test.com",
            "password": "password123",
            "full_name": "Hacker",
            "role": "admin",
        },
    )
    assert resp.status_code == 403
