from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


# --- Auth Schemas ---
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class GoogleAuthCallback(BaseModel):
    code: str


# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str
    is_active: bool = True


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    role: str = Field(pattern="^(admin|coach|athlete)$")


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = Field(None, pattern="^(admin|coach|athlete)$")
    coach_id: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    avatar_url: Optional[str] = None
    coach_id: Optional[int] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    garmin_connected: bool = False

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: List[UserResponse]
    total: int


class CoachResponse(BaseModel):
    id: int
    full_name: str
    email: str
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


# --- Garmin Schemas ---
class GarminCredentialsInput(BaseModel):
    garmin_email: EmailStr
    garmin_password: str = Field(min_length=1)


class GarminConnectionStatus(BaseModel):
    is_connected: bool
    last_sync: Optional[datetime] = None
    error_message: Optional[str] = None
    garmin_email: Optional[str] = None


class GarminWorkoutResponse(BaseModel):
    garmin_workout_id: str
    workout_name: str
    workout_type: str
    description: Optional[str] = None


class GarminWorkoutListResponse(BaseModel):
    workouts: List[GarminWorkoutResponse]
    total: int


# --- Workout Sharing Schemas ---
class ShareWorkoutRequest(BaseModel):
    workout_ids: List[int]
    athlete_id: int


class ShareWorkoutFromGarminRequest(BaseModel):
    garmin_workout_ids: List[str]
    athlete_id: int


class SharedWorkoutResponse(BaseModel):
    id: int
    workout_name: str
    workout_type: str
    description: Optional[str] = None
    coach_name: str
    status: str
    shared_at: datetime
    imported_at: Optional[datetime] = None
    import_error: Optional[str] = None

    class Config:
        from_attributes = True


class SharedWorkoutListResponse(BaseModel):
    workouts: List[SharedWorkoutResponse]
    total: int


class ImportWorkoutRequest(BaseModel):
    shared_workout_ids: List[int]


class ImportWorkoutResult(BaseModel):
    shared_workout_id: int
    success: bool
    message: str
    garmin_import_id: Optional[str] = None


class AthleteConnectionCheck(BaseModel):
    athlete_id: int
    is_connected: bool
    athlete_name: str
    garmin_email: Optional[str] = None
    error_message: Optional[str] = None
    recommendations: List[str] = []


# --- Contact Schemas ---
class ContactRequestInput(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)
    message: str = Field(min_length=10, max_length=5000)


class ContactRequestResponse(BaseModel):
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    message: str
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Activity Log Schemas ---
class ActivityLogResponse(BaseModel):
    id: int
    user_id: int
    action: str
    details: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Dashboard Schemas ---
class AdminStats(BaseModel):
    total_users: int
    total_coaches: int
    total_athletes: int
    total_workouts_shared: int
    total_contact_requests: int
    recent_logins: List[UserResponse]
