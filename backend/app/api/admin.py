import json
import io
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_admin
from app.api.schemas import (
    AdminStats,
    ContactRequestResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import (
    ActivityLog,
    ContactRequest,
    GarminCredentials,
    Message,
    SharedWorkout,
    User,
    UserRole,
    Workout,
)

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get dashboard statistics for admin."""
    total_users = (await db.execute(select(func.count(User.id)))).scalar() or 0
    total_coaches = (
        await db.execute(
            select(func.count(User.id)).where(User.role == UserRole.COACH)
        )
    ).scalar() or 0
    total_athletes = (
        await db.execute(
            select(func.count(User.id)).where(User.role == UserRole.ATHLETE)
        )
    ).scalar() or 0
    total_shared = (
        await db.execute(select(func.count(SharedWorkout.id)))
    ).scalar() or 0
    total_contacts = (
        await db.execute(select(func.count(ContactRequest.id)))
    ).scalar() or 0

    recent_result = await db.execute(
        select(User)
        .options(selectinload(User.garmin_credentials))
        .where(User.last_login.isnot(None))
        .order_by(User.last_login.desc())
        .limit(10)
    )
    recent_users = recent_result.scalars().all()

    return AdminStats(
        total_users=total_users,
        total_coaches=total_coaches,
        total_athletes=total_athletes,
        total_workouts_shared=total_shared,
        total_contact_requests=total_contacts,
        recent_logins=[
            UserResponse(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=u.role.value,
                is_active=u.is_active,
                avatar_url=u.avatar_url,
                venmo_link=u.venmo_link,
                coach_id=u.coach_id,
                created_at=u.created_at,
                last_login=u.last_login,
                garmin_connected=u.garmin_credentials is not None
                and u.garmin_credentials.is_connected,
            )
            for u in recent_users
        ],
    )


@router.get("/users", response_model=UserListResponse)
async def list_users(
    role: Optional[str] = Query(None, pattern="^(admin|coach|athlete)$"),
    search: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all users with optional filtering."""
    query = select(User).options(selectinload(User.garmin_credentials))
    count_query = select(func.count(User.id))

    if role:
        query = query.where(User.role == UserRole(role))
        count_query = count_query.where(User.role == UserRole(role))
    if search:
        search_filter = (
            User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(User.created_at.desc()).offset(skip).limit(limit)
    )
    users = result.scalars().all()

    return UserListResponse(
        users=[
            UserResponse(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                role=u.role.value,
                is_active=u.is_active,
                avatar_url=u.avatar_url,
                venmo_link=u.venmo_link,
                coach_id=u.coach_id,
                created_at=u.created_at,
                last_login=u.last_login,
                garmin_connected=u.garmin_credentials is not None
                and u.garmin_credentials.is_connected,
            )
            for u in users
        ],
        total=total,
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new user (admin can create any role including coach)."""
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=data.email,
        hashed_password=get_password_hash(data.password),
        full_name=data.full_name,
        role=UserRole(data.role),
    )
    db.add(user)
    await db.flush()

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        avatar_url=user.avatar_url,
        venmo_link=user.venmo_link,
        coach_id=user.coach_id,
        created_at=user.created_at,
        last_login=user.last_login,
        garmin_connected=False,
    )


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's profile (admin only)."""
    result = await db.execute(
        select(User).options(selectinload(User.garmin_credentials)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if data.full_name is not None:
        user.full_name = data.full_name
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.role is not None:
        user.role = UserRole(data.role)
    if data.coach_id is not None:
        if data.coach_id == 0:
            user.coach_id = None
        else:
            coach = await db.execute(
                select(User).where(User.id == data.coach_id, User.role == UserRole.COACH)
            )
            if not coach.scalar_one_or_none():
                raise HTTPException(status_code=400, detail="Invalid coach ID")
            user.coach_id = data.coach_id

    await db.flush()

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        is_active=user.is_active,
        avatar_url=user.avatar_url,
        venmo_link=user.venmo_link,
        coach_id=user.coach_id,
        created_at=user.created_at,
        last_login=user.last_login,
        garmin_connected=user.garmin_credentials is not None
        and user.garmin_credentials.is_connected,
    )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a user account."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    await db.delete(user)
    await db.flush()


@router.get("/contacts", response_model=list[ContactRequestResponse])
async def list_contacts(
    unread_only: bool = False,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List contact form submissions."""
    query = select(ContactRequest).order_by(ContactRequest.created_at.desc())
    if unread_only:
        query = query.where(ContactRequest.is_read == False)
    result = await db.execute(query)
    return result.scalars().all()


@router.put("/contacts/{contact_id}/read")
async def mark_contact_read(
    contact_id: int,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Mark a contact request as read."""
    result = await db.execute(
        select(ContactRequest).where(ContactRequest.id == contact_id)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact request not found")
    contact.is_read = True
    await db.flush()
    return {"status": "ok"}


@router.get("/backup")
async def download_database_backup(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Download a JSON backup of the entire database."""
    backup = {"backup_timestamp": datetime.now(timezone.utc).isoformat(), "data": {}}

    # Export users (excluding hashed passwords for security)
    users_result = await db.execute(select(User).order_by(User.id))
    users = users_result.scalars().all()
    backup["data"]["users"] = [
        {
            "id": u.id,
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role.value,
            "is_active": u.is_active,
            "avatar_url": u.avatar_url,
            "venmo_link": u.venmo_link,
            "coach_id": u.coach_id,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None,
        }
        for u in users
    ]

    # Export workouts
    workouts_result = await db.execute(select(Workout).order_by(Workout.id))
    workouts = workouts_result.scalars().all()
    backup["data"]["workouts"] = [
        {
            "id": w.id,
            "garmin_workout_id": w.garmin_workout_id,
            "coach_id": w.coach_id,
            "workout_name": w.workout_name,
            "workout_type": w.workout_type,
            "description": w.description,
            "created_at": w.created_at.isoformat() if w.created_at else None,
        }
        for w in workouts
    ]

    # Export shared workouts
    shared_result = await db.execute(select(SharedWorkout).order_by(SharedWorkout.id))
    shared = shared_result.scalars().all()
    backup["data"]["shared_workouts"] = [
        {
            "id": s.id,
            "workout_id": s.workout_id,
            "coach_id": s.coach_id,
            "athlete_id": s.athlete_id,
            "status": s.status,
            "shared_at": s.shared_at.isoformat() if s.shared_at else None,
            "imported_at": s.imported_at.isoformat() if s.imported_at else None,
        }
        for s in shared
    ]

    # Export messages
    msgs_result = await db.execute(select(Message).order_by(Message.id))
    msgs = msgs_result.scalars().all()
    backup["data"]["messages"] = [
        {
            "id": m.id,
            "sender_id": m.sender_id,
            "recipient_id": m.recipient_id,
            "subject": m.subject,
            "body": m.body,
            "is_read": m.is_read,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in msgs
    ]

    # Export contact requests
    contacts_result = await db.execute(select(ContactRequest).order_by(ContactRequest.id))
    contacts = contacts_result.scalars().all()
    backup["data"]["contact_requests"] = [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "message": c.message,
            "is_read": c.is_read,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in contacts
    ]

    json_bytes = json.dumps(backup, indent=2, default=str).encode("utf-8")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    return StreamingResponse(
        io.BytesIO(json_bytes),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="tc_backup_{timestamp}.json"'},
    )
