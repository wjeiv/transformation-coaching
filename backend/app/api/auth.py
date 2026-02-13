from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.schemas import (
    GoogleAuthCallback,
    LoginRequest,
    RegisterRequest,
    Token,
    TokenRefresh,
    UserResponse,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.models.user import ActivityLog, User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Register a new athlete account."""
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
        role=UserRole.ATHLETE,
        last_login=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.flush()

    log = ActivityLog(
        user_id=user.id,
        action="register",
        details="New athlete account created",
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    await db.flush()

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=Token)
async def login(
    data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate with email and password."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    user.last_login = datetime.now(timezone.utc)
    log = ActivityLog(
        user_id=user.id,
        action="login",
        details="Email/password login",
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    await db.flush()

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return Token(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    data: TokenRefresh,
    db: AsyncSession = Depends(get_db),
):
    """Refresh an access token."""
    try:
        payload = decode_token(data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
            )
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )

    access_token = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)
    return Token(access_token=access_token, refresh_token=new_refresh)


@router.get("/google/url")
async def google_auth_url():
    """Get the Google OAuth authorization URL."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured",
        )
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    base = "https://accounts.google.com/o/oauth2/v2/auth"
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return {"url": f"{base}?{query}"}


@router.post("/google/callback", response_model=Token)
async def google_callback(
    data: GoogleAuthCallback,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback."""
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google OAuth is not configured",
        )

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": data.code,
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange Google auth code",
            )
        tokens = token_resp.json()

        # Get user info
        userinfo_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get Google user info",
            )
        userinfo = userinfo_resp.json()

    google_id = userinfo["id"]
    email = userinfo["email"]
    name = userinfo.get("name", email)
    avatar = userinfo.get("picture")

    # Check if user exists by google_id or email
    result = await db.execute(
        select(User).where((User.google_id == google_id) | (User.email == email))
    )
    user = result.scalar_one_or_none()

    if user:
        if not user.google_id:
            user.google_id = google_id
        if avatar:
            user.avatar_url = avatar
        user.last_login = datetime.now(timezone.utc)
    else:
        user = User(
            email=email,
            full_name=name,
            google_id=google_id,
            avatar_url=avatar,
            role=UserRole.ATHLETE,
            last_login=datetime.now(timezone.utc),
        )
        db.add(user)
        await db.flush()

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )

    log = ActivityLog(
        user_id=user.id,
        action="login",
        details="Google OAuth login",
        ip_address=request.client.host if request.client else None,
    )
    db.add(log)
    await db.flush()

    access_token = create_access_token(user.id)
    refresh_token_val = create_refresh_token(user.id)
    return Token(access_token=access_token, refresh_token=refresh_token_val)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile."""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
        avatar_url=current_user.avatar_url,
        coach_id=current_user.coach_id,
        created_at=current_user.created_at,
        last_login=current_user.last_login,
        garmin_connected=current_user.garmin_credentials is not None
        and current_user.garmin_credentials.is_connected,
    )
