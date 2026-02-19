import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_coach_list_users_as_coach(client: AsyncClient, db_session: AsyncSession, coach_token: str):
    """Coaches can list users with role and filters."""
    # Create test users
    athlete = User(
        email="athlete@example.com",
        hashed_password="hash",
        full_name="Test Athlete",
        role=UserRole.ATHLETE,
        is_active=True,
    )
    other_coach = User(
        email="othercoach@example.com",
        hashed_password="hash",
        full_name="Other Coach",
        role=UserRole.COACH,
        is_active=True,
    )
    db_session.add(athlete)
    db_session.add(other_coach)
    await db_session.commit()

    # List all users
    resp = await client.get("/api/v1/coach/users", headers={"Authorization": f"Bearer {coach_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["users"]) >= 2
    roles = {u["role"] for u in data["users"]}
    assert "athlete" in roles
    assert "coach" in roles

    # Filter by role
    resp = await client.get("/api/v1/coach/users?role=athlete", headers={"Authorization": f"Bearer {coach_token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert all(u["role"] == "athlete" for u in data["users"])

    # Search by name
    resp = await client.get(
        "/api/v1/coach/users?search=Test", headers={"Authorization": f"Bearer {coach_token}"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert any("Test" in u["full_name"] for u in data["users"])


@pytest.mark.asyncio
async def test_coach_link_athlete_success(client: AsyncClient, db_session: AsyncSession, coach_token: str):
    """Coach can link an unlinked athlete."""
    athlete = User(
        email="athlete@example.com",
        hashed_password="hash",
        full_name="Test Athlete",
        role=UserRole.ATHLETE,
        is_active=True,
    )
    db_session.add(athlete)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/coach/athletes/{athlete.id}/link",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert resp.status_code == 200
    assert "linked to you" in resp.json()["message"]
    await db_session.refresh(athlete)
    assert athlete.coach_id is not None


@pytest.mark.asyncio
async def test_coach_link_already_linked_fails(client: AsyncClient, db_session: AsyncSession, coach_token: str):
    """Coach cannot link an athlete already linked to them."""
    athlete = User(
        email="athlete@example.com",
        hashed_password="hash",
        full_name="Test Athlete",
        role=UserRole.ATHLETE,
        is_active=True,
    )
    # Pre-link to the same coach (assume coach id = 1 for test)
    athlete.coach_id = 1
    db_session.add(athlete)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/coach/athletes/{athlete.id}/link",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert resp.status_code == 400
    assert "already linked to you" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_coach_link_athlete_linked_to_other_coach_fails(
    client: AsyncClient, db_session: AsyncSession, coach_token: str
):
    """Coach cannot link an athlete already linked to another coach."""
    other_coach = User(
        email="othercoach@example.com",
        hashed_password="hash",
        full_name="Other Coach",
        role=UserRole.COACH,
        is_active=True,
    )
    db_session.add(other_coach)
    await db_session.commit()
    athlete = User(
        email="athlete@example.com",
        hashed_password="hash",
        full_name="Test Athlete",
        role=UserRole.ATHLETE,
        is_active=True,
        coach_id=other_coach.id,
    )
    db_session.add(athlete)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/coach/athletes/{athlete.id}/link",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert resp.status_code == 400
    assert "already linked to another coach" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_coach_link_non_athlete_fails(client: AsyncClient, db_session: AsyncSession, coach_token: str):
    """Coach cannot link a user who is not an athlete."""
    other_coach = User(
        email="othercoach@example.com",
        hashed_password="hash",
        full_name="Other Coach",
        role=UserRole.COACH,
        is_active=True,
    )
    db_session.add(other_coach)
    await db_session.flush()

    resp = await client.post(
        f"/api/v1/coach/athletes/{other_coach.id}/link",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert resp.status_code == 404
    assert "Athlete not found" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_unauthorized_cannot_list_users(client: AsyncClient, athlete_token: str):
    """Non-coaches cannot access the coach users endpoint."""
    resp = await client.get("/api/v1/coach/users", headers={"Authorization": f"Bearer {athlete_token}"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_unauthenticated_cannot_list_users(client: AsyncClient):
    """Unauthenticated users cannot access the coach users endpoint."""
    resp = await client.get("/api/v1/coach/users")
    assert resp.status_code == 401
