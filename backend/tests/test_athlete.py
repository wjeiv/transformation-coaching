import json

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import SharedWorkout, User, UserRole, Workout


@pytest.mark.asyncio
async def test_athlete_list_coaches(client: AsyncClient, coach_user: User, athlete_token: str):
    """Athlete can list available coaches."""
    resp = await client.get(
        "/api/v1/athlete/coaches",
        headers={"Authorization": f"Bearer {athlete_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any(c["id"] == coach_user.id for c in data)
    # Verify venmo_link field is present in response
    for c in data:
        assert "venmo_link" in c


@pytest.mark.asyncio
async def test_athlete_select_coach(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_token: str
):
    """Athlete can select a coach."""
    resp = await client.post(
        f"/api/v1/athlete/select-coach/{coach_user.id}",
        headers={"Authorization": f"Bearer {athlete_token}"},
    )
    assert resp.status_code == 200
    assert "linked to coach" in resp.json()["message"]


@pytest.mark.asyncio
async def test_athlete_select_nonexistent_coach(client: AsyncClient, athlete_token: str):
    """Selecting a nonexistent coach returns 404."""
    resp = await client.post(
        "/api/v1/athlete/select-coach/99999",
        headers={"Authorization": f"Bearer {athlete_token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_athlete_get_workouts(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_user: User
):
    """Athlete can see workouts shared with them."""
    athlete_user.coach_id = coach_user.id
    workout = Workout(
        garmin_workout_id="test-123",
        coach_id=coach_user.id,
        workout_name="Test Run",
        workout_type="running",
        workout_data=json.dumps({"workoutId": "test-123"}),
        description="5K easy run",
    )
    db_session.add(workout)
    await db_session.flush()

    shared = SharedWorkout(
        workout_id=workout.id,
        coach_id=coach_user.id,
        athlete_id=athlete_user.id,
        status="pending",
    )
    db_session.add(shared)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "athletepass123"},
    )
    token = resp.json()["access_token"]

    resp = await client.get(
        "/api/v1/athlete/workouts",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(w["workout_name"] == "Test Run" for w in data["workouts"])


@pytest.mark.asyncio
async def test_athlete_remove_pending_workout(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_user: User
):
    """Athlete can remove a pending (not yet imported) workout."""
    athlete_user.coach_id = coach_user.id
    workout = Workout(
        garmin_workout_id="remove-test",
        coach_id=coach_user.id,
        workout_name="Workout to Remove",
        workout_type="running",
        workout_data=json.dumps({"workoutId": "remove-test"}),
    )
    db_session.add(workout)
    await db_session.flush()

    shared = SharedWorkout(
        workout_id=workout.id,
        coach_id=coach_user.id,
        athlete_id=athlete_user.id,
        status="pending",
    )
    db_session.add(shared)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "athletepass123"},
    )
    token = resp.json()["access_token"]

    resp = await client.delete(
        f"/api/v1/athlete/workouts/{shared.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_athlete_remove_imported_workout(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_user: User
):
    """Athlete can remove an already-imported workout."""
    athlete_user.coach_id = coach_user.id
    workout = Workout(
        garmin_workout_id="imported-test",
        coach_id=coach_user.id,
        workout_name="Imported Workout",
        workout_type="cycling",
        workout_data=json.dumps({"workoutId": "imported-test"}),
    )
    db_session.add(workout)
    await db_session.flush()

    shared = SharedWorkout(
        workout_id=workout.id,
        coach_id=coach_user.id,
        athlete_id=athlete_user.id,
        status="imported",
    )
    db_session.add(shared)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "athletepass123"},
    )
    token = resp.json()["access_token"]

    resp = await client.delete(
        f"/api/v1/athlete/workouts/{shared.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_athlete_cannot_remove_others_workout(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_user: User
):
    """Athlete cannot remove a workout that belongs to another athlete."""
    other_athlete = User(
        email="other@test.com",
        hashed_password=get_password_hash("otherpass123"),
        full_name="Other Athlete",
        role=UserRole.ATHLETE,
        coach_id=coach_user.id,
    )
    db_session.add(other_athlete)
    await db_session.flush()

    workout = Workout(
        garmin_workout_id="other-test",
        coach_id=coach_user.id,
        workout_name="Other's Workout",
        workout_type="running",
        workout_data=json.dumps({"workoutId": "other-test"}),
    )
    db_session.add(workout)
    await db_session.flush()

    shared = SharedWorkout(
        workout_id=workout.id,
        coach_id=coach_user.id,
        athlete_id=other_athlete.id,
        status="pending",
    )
    db_session.add(shared)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "athletepass123"},
    )
    token = resp.json()["access_token"]

    resp = await client.delete(
        f"/api/v1/athlete/workouts/{shared.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_coach_cannot_access_athlete_endpoints(client: AsyncClient, coach_token: str):
    """Coach role cannot access athlete-only endpoints."""
    resp = await client.get(
        "/api/v1/athlete/workouts",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert resp.status_code == 403
