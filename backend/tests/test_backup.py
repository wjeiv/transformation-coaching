import json

import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.mark.asyncio
async def test_admin_can_download_backup(client: AsyncClient, admin_token: str, admin_user: User):
    """Admin can download a JSON database backup."""
    resp = await client.get(
        "/api/v1/admin/backup",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    assert "application/json" in resp.headers.get("content-type", "")

    data = resp.json()
    assert "backup_timestamp" in data
    assert "data" in data
    assert "users" in data["data"]
    assert "workouts" in data["data"]
    assert "shared_workouts" in data["data"]
    assert "messages" in data["data"]
    assert "contact_requests" in data["data"]
    # At least the admin user should be in the backup
    assert len(data["data"]["users"]) >= 1


@pytest.mark.asyncio
async def test_coach_cannot_download_backup(client: AsyncClient, coach_token: str):
    """Non-admin users cannot download backups."""
    resp = await client.get(
        "/api/v1/admin/backup",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_athlete_cannot_download_backup(client: AsyncClient, athlete_token: str):
    """Athletes cannot download backups."""
    resp = await client.get(
        "/api/v1/admin/backup",
        headers={"Authorization": f"Bearer {athlete_token}"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_cannot_download_backup(client: AsyncClient):
    """Unauthenticated users cannot download backups."""
    resp = await client.get("/api/v1/admin/backup")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_backup_excludes_passwords(client: AsyncClient, admin_token: str, admin_user: User):
    """Backup should not contain hashed passwords."""
    resp = await client.get(
        "/api/v1/admin/backup",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    for user in data["data"]["users"]:
        assert "hashed_password" not in user
        assert "password" not in user
