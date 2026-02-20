import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.api import admin, athlete, auth, coach, garmin, messaging, public
from app.core.config import settings
from app.core.database import get_db, init_db, async_session
from app.core.security import get_password_hash
from app.models.user import User, UserRole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Transformation Coaching API...")
    await init_db()
    await create_first_admin()  # Bcrypt issue resolved - re-enabled
    await seed_default_users()
    yield
    logger.info("Shutting down Transformation Coaching API...")


async def create_first_admin():
    """Create the first admin account if it doesn't exist."""
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        if not result.scalar_one_or_none():
            admin_user = User(
                email=settings.FIRST_ADMIN_EMAIL,
                hashed_password=get_password_hash(settings.FIRST_ADMIN_PASSWORD),
                full_name="Administrator",
                role=UserRole.ADMIN,
            )
            session.add(admin_user)
            await session.commit()
            logger.info(f"Created first admin account: {settings.FIRST_ADMIN_EMAIL}")


async def seed_default_users():
    """Seed default coach and athlete if they don't exist."""
    async with async_session() as session:
        # Create coach: Bill Coach
        coach_result = await session.execute(
            select(User).where(User.email == "wjeiv4@gmail.com")
        )
        coach = coach_result.scalar_one_or_none()
        if not coach:
            coach = User(
                email="wjeiv4@gmail.com",
                hashed_password=get_password_hash("FFester1!"),
                full_name="Bill Coach",
                role=UserRole.COACH,
            )
            session.add(coach)
            await session.flush()
            logger.info("Created default coach: Bill Coach (wjeiv4@gmail.com)")

        # Create athlete: Gretchen Hickey linked to Bill Coach
        athlete_result = await session.execute(
            select(User).where(User.email == "gretchenhickey6399@gmail.com")
        )
        athlete = athlete_result.scalar_one_or_none()
        if not athlete:
            athlete = User(
                email="gretchenhickey6399@gmail.com",
                hashed_password=get_password_hash("FFester1!"),
                full_name="Gretchen Hickey",
                role=UserRole.ATHLETE,
                coach_id=coach.id,
            )
            session.add(athlete)
            logger.info("Created default athlete: Gretchen Hickey linked to Bill Coach")

        await session.commit()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred"},
    )


# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(admin.router, prefix=settings.API_V1_STR)
app.include_router(coach.router, prefix=settings.API_V1_STR)
app.include_router(athlete.router, prefix=settings.API_V1_STR)
app.include_router(garmin.router, prefix=settings.API_V1_STR)
app.include_router(messaging.router, prefix=settings.API_V1_STR)
app.include_router(public.router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.PROJECT_NAME}
