import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_athlete, get_current_user
from app.api.schemas import (
    CoachResponse,
    ImportWorkoutRequest,
    ImportWorkoutResult,
    SharedWorkoutListResponse,
    SharedWorkoutResponse,
    UserUpdate,
)
from app.core.database import get_db
from app.models.user import GarminCredentials, SharedWorkout, User, UserRole
from app.services.garmin_service import GarminService

router = APIRouter(prefix="/athlete", tags=["athlete"])


@router.get("/coaches", response_model=list[CoachResponse])
async def list_available_coaches(
    db: AsyncSession = Depends(get_db),
):
    """List all available coaches (public endpoint for athlete registration flow)."""
    result = await db.execute(
        select(User).where(User.role == UserRole.COACH, User.is_active == True).order_by(User.full_name)
    )
    coaches = result.scalars().all()
    return [
        CoachResponse(
            id=c.id,
            full_name=c.full_name,
            email=c.email,
            avatar_url=c.avatar_url,
            venmo_link=c.venmo_link,
        )
        for c in coaches
    ]


@router.post("/select-coach/{coach_id}")
async def select_coach(
    coach_id: int,
    current_user: User = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Select a coach for the current athlete."""
    result = await db.execute(
        select(User).where(User.id == coach_id, User.role == UserRole.COACH, User.is_active == True)
    )
    coach = result.scalar_one_or_none()
    if not coach:
        raise HTTPException(status_code=404, detail="Coach not found")

    current_user.coach_id = coach.id
    await db.flush()
    return {"status": "ok", "message": f"You are now linked to coach {coach.full_name}"}


@router.get("/workouts", response_model=SharedWorkoutListResponse)
async def get_my_shared_workouts(
    current_user: User = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Get all workouts shared with this athlete."""
    result = await db.execute(
        select(SharedWorkout)
        .options(
            selectinload(SharedWorkout.workout),
            selectinload(SharedWorkout.coach),
        )
        .where(
            SharedWorkout.athlete_id == current_user.id,
            SharedWorkout.status.in_(["pending", "imported", "failed"]),
        )
        .order_by(SharedWorkout.shared_at.desc())
    )
    shared = result.scalars().all()

    return SharedWorkoutListResponse(
        workouts=[
            SharedWorkoutResponse(
                id=s.id,
                workout_name=s.workout.workout_name,
                workout_type=s.workout.workout_type,
                description=s.workout.description,
                coach_name=s.coach.full_name,
                status=s.status,
                shared_at=s.shared_at,
                imported_at=s.imported_at,
                import_error=s.import_error,
            )
            for s in shared
        ],
        total=len(shared),
    )


@router.post("/workouts/import", response_model=list[ImportWorkoutResult])
async def import_workouts(
    data: ImportWorkoutRequest,
    current_user: User = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Import shared workouts into the athlete's Garmin Connect account."""
    # Check Garmin credentials
    creds_result = await db.execute(
        select(GarminCredentials).where(GarminCredentials.user_id == current_user.id)
    )
    creds = creds_result.scalar_one_or_none()
    if not creds or not creds.is_connected:
        raise HTTPException(
            status_code=400,
            detail="Please connect your Garmin account first (Settings > Garmin Connect)",
        )

    results = []
    for sw_id in data.shared_workout_ids:
        sw_result = await db.execute(
            select(SharedWorkout)
            .options(selectinload(SharedWorkout.workout))
            .where(
                SharedWorkout.id == sw_id,
                SharedWorkout.athlete_id == current_user.id,
            )
        )
        shared = sw_result.scalar_one_or_none()
        if not shared:
            results.append(ImportWorkoutResult(
                shared_workout_id=sw_id,
                success=False,
                message="Shared workout not found or does not belong to you",
            ))
            continue

        if shared.status == "imported":
            results.append(ImportWorkoutResult(
                shared_workout_id=sw_id,
                success=False,
                message="This workout has already been imported",
            ))
            continue

        # Parse workout data and import
        try:
            workout_data = json.loads(shared.workout.workout_data)
        except json.JSONDecodeError:
            results.append(ImportWorkoutResult(
                shared_workout_id=sw_id,
                success=False,
                message="Workout data is corrupted. Ask your coach to re-share this workout.",
            ))
            shared.status = "failed"
            shared.import_error = "Corrupted workout data"
            continue

        success, message, garmin_id = await GarminService.import_workout(
            creds.garmin_email_encrypted,
            creds.garmin_password_encrypted,
            workout_data,
        )

        if success:
            shared.status = "imported"
            shared.imported_at = datetime.now(timezone.utc)
            shared.garmin_import_id = garmin_id
            results.append(ImportWorkoutResult(
                shared_workout_id=sw_id,
                success=True,
                message=f"'{shared.workout.workout_name}' imported successfully to your Garmin account",
                garmin_import_id=garmin_id,
            ))
        else:
            shared.status = "failed"
            shared.import_error = message
            results.append(ImportWorkoutResult(
                shared_workout_id=sw_id,
                success=False,
                message=message,
            ))

    await db.flush()
    return results


@router.delete("/workouts/{shared_workout_id}")
async def remove_shared_workout(
    shared_workout_id: int,
    current_user: User = Depends(get_current_athlete),
    db: AsyncSession = Depends(get_db),
):
    """Remove a shared workout from the athlete's list."""
    result = await db.execute(
        select(SharedWorkout).where(
            SharedWorkout.id == shared_workout_id,
            SharedWorkout.athlete_id == current_user.id,
        )
    )
    shared = result.scalar_one_or_none()
    if not shared:
        raise HTTPException(status_code=404, detail="Shared workout not found")

    shared.status = "removed"
    await db.flush()
    return {"status": "ok", "message": "Workout removed from your list"}
