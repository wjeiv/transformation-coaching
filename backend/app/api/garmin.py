from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.schemas import GarminConnectionStatus, GarminCredentialsInput
from app.core.database import get_db
from app.core.security import decrypt_value, encrypt_value
from app.models.user import GarminCredentials, User
from app.services.garmin_service import GarminService

router = APIRouter(prefix="/garmin", tags=["garmin"])


@router.post("/connect")
async def connect_garmin_account(
    data: GarminCredentialsInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Connect a Garmin Connect account by providing credentials.

    The credentials are encrypted at rest and used to authenticate with
    Garmin Connect when syncing workouts. This is required because Garmin
    does not provide a public OAuth API for third-party workout management.

    Steps:
    1. Enter your Garmin Connect email and password
    2. We will verify connectivity immediately
    3. Your credentials are encrypted and stored securely
    4. You can disconnect at any time
    """
    encrypted_email = encrypt_value(data.garmin_email)
    encrypted_password = encrypt_value(data.garmin_password)

    # Test connection first
    success, message = await GarminService.test_connection(encrypted_email, encrypted_password)

    result = await db.execute(
        select(GarminCredentials).where(GarminCredentials.user_id == current_user.id)
    )
    creds = result.scalar_one_or_none()

    if creds:
        creds.garmin_email_encrypted = encrypted_email
        creds.garmin_password_encrypted = encrypted_password
        creds.is_connected = success
        creds.connection_error = None if success else message
        creds.last_sync = datetime.now(timezone.utc) if success else None
    else:
        creds = GarminCredentials(
            user_id=current_user.id,
            garmin_email_encrypted=encrypted_email,
            garmin_password_encrypted=encrypted_password,
            is_connected=success,
            connection_error=None if success else message,
            last_sync=datetime.now(timezone.utc) if success else None,
        )
        db.add(creds)

    await db.flush()

    if not success:
        raise HTTPException(
            status_code=400,
            detail={
                "message": message,
                "help": [
                    "Double-check your Garmin Connect email address",
                    "Double-check your Garmin Connect password",
                    "Make sure you can log in at https://connect.garmin.com",
                    "If you have two-factor authentication enabled, you may need to use an app-specific password",
                ],
            },
        )

    return {
        "status": "connected",
        "message": message,
        "help": "Your Garmin account is now connected. Your coach can share workouts with you.",
    }


@router.get("/status", response_model=GarminConnectionStatus)
async def get_garmin_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current Garmin Connect connection status."""
    result = await db.execute(
        select(GarminCredentials).where(GarminCredentials.user_id == current_user.id)
    )
    creds = result.scalar_one_or_none()

    if not creds:
        return GarminConnectionStatus(
            is_connected=False,
            error_message="No Garmin account connected. Go to Settings > Garmin Connect to connect.",
        )

    garmin_email = None
    try:
        garmin_email = decrypt_value(creds.garmin_email_encrypted)
    except Exception:
        pass

    return GarminConnectionStatus(
        is_connected=creds.is_connected,
        last_sync=creds.last_sync,
        error_message=creds.connection_error,
        garmin_email=garmin_email,
    )


@router.post("/test")
async def test_garmin_connection(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test the current Garmin Connect connection."""
    result = await db.execute(
        select(GarminCredentials).where(GarminCredentials.user_id == current_user.id)
    )
    creds = result.scalar_one_or_none()

    if not creds:
        raise HTTPException(
            status_code=400,
            detail="No Garmin account connected. Please connect first.",
        )

    success, message = await GarminService.test_connection(
        creds.garmin_email_encrypted, creds.garmin_password_encrypted
    )

    creds.is_connected = success
    creds.connection_error = None if success else message
    if success:
        creds.last_sync = datetime.now(timezone.utc)
    await db.flush()

    return {"is_connected": success, "message": message}


@router.delete("/disconnect")
async def disconnect_garmin(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Disconnect the Garmin Connect account and remove stored credentials."""
    result = await db.execute(
        select(GarminCredentials).where(GarminCredentials.user_id == current_user.id)
    )
    creds = result.scalar_one_or_none()

    if not creds:
        raise HTTPException(status_code=400, detail="No Garmin account connected")

    await db.delete(creds)
    await db.flush()
    return {"status": "disconnected", "message": "Garmin account disconnected and credentials removed"}
