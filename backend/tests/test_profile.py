import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_update_profile_name(client: AsyncClient, athlete_token: str):
    """User can update their display name."""
    resp = await client.put(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
        json={"full_name": "Updated Athlete Name"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "Updated Athlete Name"


@pytest.mark.asyncio
async def test_update_profile_avatar(client: AsyncClient, athlete_token: str):
    """User can set their avatar URL."""
    resp = await client.put(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {athlete_token}"},
        json={"avatar_url": "https://example.com/photo.jpg"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["avatar_url"] == "https://example.com/photo.jpg"


@pytest.mark.asyncio
async def test_update_profile_venmo(client: AsyncClient, coach_token: str):
    """Coach can set their venmo link."""
    resp = await client.put(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={"venmo_link": "https://venmo.com/u/testcoach"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["venmo_link"] == "https://venmo.com/u/testcoach"


@pytest.mark.asyncio
async def test_get_me_includes_venmo(client: AsyncClient, db_session: AsyncSession, coach_user: User):
    """GET /auth/me returns venmo_link."""
    coach_user.venmo_link = "https://venmo.com/u/mycoach"
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "coach@test.com", "password": "coachpass123"},
    )
    token = resp.json()["access_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["venmo_link"] == "https://venmo.com/u/mycoach"


@pytest.mark.asyncio
async def test_update_multiple_fields(client: AsyncClient, coach_token: str):
    """User can update multiple profile fields at once."""
    resp = await client.put(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {coach_token}"},
        json={
            "full_name": "New Coach Name",
            "avatar_url": "https://example.com/avatar.png",
            "venmo_link": "https://venmo.com/u/newcoach",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["full_name"] == "New Coach Name"
    assert data["avatar_url"] == "https://example.com/avatar.png"
    assert data["venmo_link"] == "https://venmo.com/u/newcoach"


@pytest.mark.asyncio
async def test_unauthenticated_cannot_update_profile(client: AsyncClient):
    """Unauthenticated user cannot update profile."""
    resp = await client.put(
        "/api/v1/auth/me",
        json={"full_name": "Hacker"},
    )
    assert resp.status_code in (401, 403)
