import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_coach
from app.api.schemas import (
    AthleteConnectionCheck,
    GarminWorkoutListResponse,
    GarminWorkoutResponse,
    ShareWorkoutFromGarminRequest,
    SharedWorkoutListResponse,
    SharedWorkoutResponse,
    UserListResponse,
    UserResponse,
)
from app.core.database import get_db
from app.models.user import GarminCredentials, SharedWorkout, User, UserRole, Workout
from app.services.garmin_service import GarminService

router = APIRouter(prefix="/coach", tags=["coach"])


@router.get("/athletes", response_model=list[UserResponse])
async def list_my_athletes(
    coach: User = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """List all athletes linked to this coach."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.garmin_credentials))
        .where(User.coach_id == coach.id, User.role == UserRole.ATHLETE)
        .order_by(User.full_name)
    )
    athletes = result.scalars().all()
    return [
        UserResponse(
            id=a.id,
            email=a.email,
            full_name=a.full_name,
            role=a.role.value,
            is_active=a.is_active,
            avatar_url=a.avatar_url,
            venmo_link=a.venmo_link,
            coach_id=a.coach_id,
            created_at=a.created_at,
            last_login=a.last_login,
            garmin_connected=a.garmin_credentials is not None
            and a.garmin_credentials.is_connected,
        )
        for a in athletes
    ]


@router.get("/users", response_model=UserListResponse)
async def list_all_users(
    role: Optional[str] = Query(None, pattern="^(coach|athlete)$"),
    search: Optional[str] = None,
    only_unlinked: Optional[bool] = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    coach: User = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """List all users (athletes and coaches) for linking purposes."""
    query = select(User).options(selectinload(User.garmin_credentials))
    count_query = select(func.count(User.id))

    # Apply filters
    if role:
        query = query.where(User.role == UserRole(role))
        count_query = count_query.where(User.role == UserRole(role))
    if search:
        search_filter = (
            User.email.ilike(f"%{search}%") | User.full_name.ilike(f"%{search}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)
    if only_unlinked:
        query = query.where(User.coach_id.is_(None))
        count_query = count_query.where(User.coach_id.is_(None))

    total = (await db.execute(count_query)).scalar() or 0
    result = await db.execute(
        query.order_by(User.full_name).offset(skip).limit(limit)
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


@router.post("/athletes/{athlete_id}/link")
async def link_athlete(
    athlete_id: int,
    coach: User = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """Link an athlete to this coach."""
    result = await db.execute(
        select(User).where(User.id == athlete_id, User.role == UserRole.ATHLETE)
    )
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")
    
    if athlete.coach_id is not None:
        if athlete.coach_id == coach.id:
            raise HTTPException(status_code=400, detail="This athlete is already linked to you")
        else:
            raise HTTPException(
                status_code=400, 
                detail="This athlete is already linked to another coach. Only admins can reassign athletes."
            )
    
    athlete.coach_id = coach.id
    await db.flush()
    return {"status": "ok", "message": f"{athlete.full_name} is now linked to you"}


@router.post("/athletes/{athlete_id}/unlink")
async def unlink_athlete(
    athlete_id: int,
    coach: User = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """Unlink an athlete from this coach."""
    result = await db.execute(
        select(User).where(
            User.id == athlete_id,
            User.coach_id == coach.id,
            User.role == UserRole.ATHLETE,
        )
    )
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found or not linked to you")
    athlete.coach_id = None
    await db.flush()
    return {"status": "ok", "message": f"{athlete.full_name} has been unlinked"}


@router.get("/athletes/{athlete_id}/check-connection", response_model=AthleteConnectionCheck)
async def check_athlete_garmin_connection(
    athlete_id: int,
    coach: User = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """Check if an athlete's Garmin Connect account is accessible for workout sync."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.garmin_credentials))
        .where(User.id == athlete_id, User.role == UserRole.ATHLETE)
    )
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    if not athlete.garmin_credentials:
        return AthleteConnectionCheck(
            athlete_id=athlete.id,
            is_connected=False,
            athlete_name=athlete.full_name,
            error_message="This athlete has not connected their Garmin account yet.",
            recommendations=[
                "Ask the athlete to log in and connect their Garmin account",
                "The athlete needs to go to Settings > Garmin Connect and enter their credentials",
                "Once connected, you can share workouts with them",
            ],
        )

    creds = athlete.garmin_credentials
    if not creds.is_connected:
        return AthleteConnectionCheck(
            athlete_id=athlete.id,
            is_connected=False,
            athlete_name=athlete.full_name,
            error_message=creds.connection_error or "Garmin account is not connected.",
            recommendations=[
                "The athlete's Garmin credentials may be invalid",
                "Ask the athlete to re-enter their Garmin Connect credentials",
                "The athlete should verify they can log in at connect.garmin.com",
            ],
        )

    status_info = await GarminService.check_athlete_connection(
        creds.garmin_email_encrypted, creds.garmin_password_encrypted
    )

    from app.core.security import decrypt_value

    garmin_email = None
    try:
        garmin_email = decrypt_value(creds.garmin_email_encrypted)
    except Exception:
        pass

    return AthleteConnectionCheck(
        athlete_id=athlete.id,
        is_connected=status_info["is_connected"],
        athlete_name=athlete.full_name,
        garmin_email=garmin_email,
        error_message=None if status_info["is_connected"] else status_info["message"],
        recommendations=status_info.get("recommendations", []),
    )


@router.get("/workouts", response_model=GarminWorkoutListResponse)
async def get_my_garmin_workouts(
    workout_type: Optional[str] = Query(None, pattern="^(running|cycling|swimming|strength|other)$"),
    coach: User = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """Fetch workouts from the coach's Garmin Connect account."""
    result = await db.execute(
        select(GarminCredentials).where(GarminCredentials.user_id == coach.id)
    )
    creds = result.scalar_one_or_none()
    if not creds or not creds.is_connected:
        raise HTTPException(
            status_code=400,
            detail="Please connect your Garmin account first (Settings > Garmin Connect)",
        )

    success, message, workouts = await GarminService.get_workouts(
        creds.garmin_email_encrypted, creds.garmin_password_encrypted
    )
    if not success:
        raise HTTPException(status_code=502, detail=message)

    # Store/update workouts in DB
    for w in workouts:
        existing = await db.execute(
            select(Workout).where(
                Workout.garmin_workout_id == w["garmin_workout_id"],
                Workout.coach_id == coach.id,
            )
        )
        db_workout = existing.scalar_one_or_none()
        if db_workout:
            db_workout.workout_name = w["workout_name"]
            db_workout.workout_type = w["workout_type"]
            db_workout.workout_data = w["workout_data"]
            db_workout.description = w["description"]
        else:
            db_workout = Workout(
                garmin_workout_id=w["garmin_workout_id"],
                coach_id=coach.id,
                workout_name=w["workout_name"],
                workout_type=w["workout_type"],
                workout_data=w["workout_data"],
                description=w["description"],
            )
            db.add(db_workout)
    await db.flush()

    # Filter if requested
    filtered = workouts
    if workout_type:
        filtered = [w for w in workouts if w["workout_type"] == workout_type]

    return GarminWorkoutListResponse(
        workouts=[
            GarminWorkoutResponse(
                garmin_workout_id=w["garmin_workout_id"],
                workout_name=w["workout_name"],
                workout_type=w["workout_type"],
                description=w["description"],
            )
            for w in filtered
        ],
        total=len(filtered),
    )


@router.post("/share-workouts")
async def share_workouts_with_athlete(
    data: ShareWorkoutFromGarminRequest,
    coach: User = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """Share selected Garmin workouts with an athlete."""
    # Verify athlete exists and is linked
    result = await db.execute(
        select(User)
        .options(selectinload(User.garmin_credentials))
        .where(
            User.id == data.athlete_id,
            User.role == UserRole.ATHLETE,
        )
    )
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise HTTPException(status_code=404, detail="Athlete not found")

    shared_count = 0
    errors = []
    for gw_id in data.garmin_workout_ids:
        # Find workout in DB
        w_result = await db.execute(
            select(Workout).where(
                Workout.garmin_workout_id == gw_id,
                Workout.coach_id == coach.id,
            )
        )
        workout = w_result.scalar_one_or_none()
        if not workout:
            errors.append(f"Workout {gw_id} not found. Refresh your workout list first.")
            continue

        # Check if already shared
        existing = await db.execute(
            select(SharedWorkout).where(
                SharedWorkout.workout_id == workout.id,
                SharedWorkout.athlete_id == data.athlete_id,
                SharedWorkout.status.in_(["pending", "imported"]),
            )
        )
        if existing.scalar_one_or_none():
            errors.append(f"Workout '{workout.workout_name}' already shared with this athlete")
            continue

        shared = SharedWorkout(
            workout_id=workout.id,
            coach_id=coach.id,
            athlete_id=data.athlete_id,
            status="pending",
        )
        db.add(shared)
        shared_count += 1

    await db.flush()

    return {
        "status": "ok",
        "shared_count": shared_count,
        "errors": errors,
        "message": f"Successfully shared {shared_count} workout(s) with {athlete.full_name}",
    }


@router.get("/shared-workouts", response_model=SharedWorkoutListResponse)
async def list_shared_workouts(
    athlete_id: Optional[int] = None,
    coach: User = Depends(get_current_coach),
    db: AsyncSession = Depends(get_db),
):
    """List all workouts shared by this coach."""
    query = (
        select(SharedWorkout)
        .options(selectinload(SharedWorkout.workout), selectinload(SharedWorkout.athlete))
        .where(SharedWorkout.coach_id == coach.id)
        .order_by(SharedWorkout.shared_at.desc())
    )
    if athlete_id:
        query = query.where(SharedWorkout.athlete_id == athlete_id)

    result = await db.execute(query)
    shared = result.scalars().all()

    return SharedWorkoutListResponse(
        workouts=[
            SharedWorkoutResponse(
                id=s.id,
                workout_name=s.workout.workout_name,
                workout_type=s.workout.workout_type,
                description=s.workout.description,
                coach_name=coach.full_name,
                status=s.status,
                shared_at=s.shared_at,
                imported_at=s.imported_at,
                import_error=s.import_error,
            )
            for s in shared
        ],
        total=len(shared),
    )
