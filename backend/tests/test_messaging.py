import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_send_message_athlete_to_coach(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_user: User
):
    """Athlete can send a message to their assigned coach."""
    # Link athlete to coach
    athlete_user.coach_id = coach_user.id
    await db_session.commit()

    # Login as athlete
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "athletepass123"},
    )
    token = resp.json()["access_token"]

    # Send message
    resp = await client.post(
        "/api/v1/messages/send",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "recipient_id": coach_user.id,
            "subject": "Training question",
            "body": "Can we adjust my training plan for next week?",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["sender_id"] == athlete_user.id
    assert data["recipient_id"] == coach_user.id
    assert data["subject"] == "Training question"
    assert data["is_read"] is False


@pytest.mark.asyncio
async def test_send_message_coach_to_athlete(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_user: User
):
    """Coach can send a message to their linked athlete."""
    # Link athlete to coach
    athlete_user.coach_id = coach_user.id
    await db_session.commit()

    # Login as coach
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "coach@test.com", "password": "coachpass123"},
    )
    token = resp.json()["access_token"]

    # Send message
    resp = await client.post(
        "/api/v1/messages/send",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "recipient_id": athlete_user.id,
            "body": "Great work on today's run!",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["sender_id"] == coach_user.id
    assert data["recipient_id"] == athlete_user.id


@pytest.mark.asyncio
async def test_athlete_cannot_message_unlinked_coach(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_user: User
):
    """Athlete cannot message a coach they are not linked to."""
    # athlete_user has no coach_id set
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "athletepass123"},
    )
    token = resp.json()["access_token"]

    resp = await client.post(
        "/api/v1/messages/send",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "recipient_id": coach_user.id,
            "body": "Hello coach!",
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_coach_cannot_message_unlinked_athlete(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_user: User
):
    """Coach cannot message an athlete not linked to them."""
    # athlete has no coach_id
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "coach@test.com", "password": "coachpass123"},
    )
    token = resp.json()["access_token"]

    resp = await client.post(
        "/api/v1/messages/send",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "recipient_id": athlete_user.id,
            "body": "Great job!",
        },
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_inbox(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_user: User
):
    """User can retrieve their inbox messages."""
    # Link and send a message from athlete to coach
    athlete_user.coach_id = coach_user.id
    await db_session.commit()

    athlete_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "athletepass123"},
    )
    athlete_token = athlete_resp.json()["access_token"]

    await client.post(
        "/api/v1/messages/send",
        headers={"Authorization": f"Bearer {athlete_token}"},
        json={"recipient_id": coach_user.id, "body": "Hello coach!"},
    )

    # Check coach inbox
    coach_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "coach@test.com", "password": "coachpass123"},
    )
    coach_token = coach_resp.json()["access_token"]

    resp = await client.get(
        "/api/v1/messages/inbox",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(m["body"] == "Hello coach!" for m in data["messages"])


@pytest.mark.asyncio
async def test_get_sent_messages(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_user: User
):
    """User can retrieve their sent messages."""
    athlete_user.coach_id = coach_user.id
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "athletepass123"},
    )
    token = resp.json()["access_token"]

    await client.post(
        "/api/v1/messages/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"recipient_id": coach_user.id, "body": "Sent message test"},
    )

    resp = await client.get(
        "/api/v1/messages/sent",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(m["body"] == "Sent message test" for m in data["messages"])


@pytest.mark.asyncio
async def test_mark_message_read(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_user: User
):
    """Recipient can mark a message as read."""
    athlete_user.coach_id = coach_user.id
    await db_session.commit()

    # Send from athlete
    athlete_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "athletepass123"},
    )
    athlete_token = athlete_resp.json()["access_token"]

    send_resp = await client.post(
        "/api/v1/messages/send",
        headers={"Authorization": f"Bearer {athlete_token}"},
        json={"recipient_id": coach_user.id, "body": "Please read"},
    )
    msg_id = send_resp.json()["id"]

    # Mark as read by coach
    coach_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "coach@test.com", "password": "coachpass123"},
    )
    coach_token = coach_resp.json()["access_token"]

    resp = await client.put(
        f"/api/v1/messages/{msg_id}/read",
        headers={"Authorization": f"Bearer {coach_token}"},
    )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_list_messageable_recipients_athlete(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_user: User
):
    """Athlete can list their assigned coach as messageable."""
    athlete_user.coach_id = coach_user.id
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "athletepass123"},
    )
    token = resp.json()["access_token"]

    resp = await client.get(
        "/api/v1/messages/coaches",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == coach_user.id


@pytest.mark.asyncio
async def test_list_messageable_recipients_coach(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_user: User
):
    """Coach can list their linked athletes as messageable."""
    athlete_user.coach_id = coach_user.id
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "coach@test.com", "password": "coachpass123"},
    )
    token = resp.json()["access_token"]

    resp = await client.get(
        "/api/v1/messages/coaches",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert any(r["id"] == athlete_user.id for r in data)


@pytest.mark.asyncio
async def test_send_message_empty_body_fails(
    client: AsyncClient, db_session: AsyncSession, coach_user: User, athlete_user: User
):
    """Cannot send a message with empty body."""
    athlete_user.coach_id = coach_user.id
    await db_session.commit()

    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "athlete@test.com", "password": "athletepass123"},
    )
    token = resp.json()["access_token"]

    resp = await client.post(
        "/api/v1/messages/send",
        headers={"Authorization": f"Bearer {token}"},
        json={"recipient_id": coach_user.id, "body": ""},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_send_message_nonexistent_recipient(client: AsyncClient, athlete_token: str):
    """Cannot send a message to a nonexistent user."""
    resp = await client.post(
        "/api/v1/messages/send",
        headers={"Authorization": f"Bearer {athlete_token}"},
        json={"recipient_id": 99999, "body": "Hello"},
    )
    assert resp.status_code == 404
