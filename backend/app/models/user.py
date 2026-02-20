import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    COACH = "coach"
    ATHLETE = "athlete"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # nullable for Google OAuth users
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.ATHLETE)
    is_active = Column(Boolean, default=True)
    google_id = Column(String(255), unique=True, nullable=True)
    avatar_url = Column(Text, nullable=True)
    venmo_link = Column(String(255), nullable=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    coach = relationship("User", remote_side="User.id", backref="athletes")
    garmin_credentials = relationship("GarminCredentials", back_populates="user", uselist=False, cascade="all, delete-orphan")
    shared_workouts_sent = relationship("SharedWorkout", foreign_keys="SharedWorkout.coach_id", back_populates="coach", cascade="all, delete-orphan")
    shared_workouts_received = relationship("SharedWorkout", foreign_keys="SharedWorkout.athlete_id", back_populates="athlete", cascade="all, delete-orphan")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    messages_sent = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender", cascade="all, delete-orphan")
    messages_received = relationship("Message", foreign_keys="Message.recipient_id", back_populates="recipient", cascade="all, delete-orphan")


class GarminCredentials(Base):
    __tablename__ = "garmin_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    garmin_email_encrypted = Column(Text, nullable=False)
    garmin_password_encrypted = Column(Text, nullable=False)
    oauth_token_encrypted = Column(Text, nullable=True)
    is_connected = Column(Boolean, default=False)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    connection_error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="garmin_credentials")


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    garmin_workout_id = Column(String(100), nullable=False, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    workout_name = Column(String(500), nullable=False)
    workout_type = Column(String(50), nullable=False)  # running, cycling, swimming, strength
    workout_data = Column(Text, nullable=False)  # JSON blob of full workout details
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    coach = relationship("User")
    shared_workouts = relationship("SharedWorkout", back_populates="workout", cascade="all, delete-orphan")


class SharedWorkout(Base):
    __tablename__ = "shared_workouts"

    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id"), nullable=False)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    athlete_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="pending")  # pending, imported, failed, removed
    import_error = Column(Text, nullable=True)
    garmin_import_id = Column(String(100), nullable=True)
    shared_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    imported_at = Column(DateTime(timezone=True), nullable=True)

    workout = relationship("Workout", back_populates="shared_workouts")
    coach = relationship("User", foreign_keys=[coach_id], back_populates="shared_workouts_sent")
    athlete = relationship("User", foreign_keys=[athlete_id], back_populates="shared_workouts_received")


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="activity_logs")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    recipient = relationship("User", foreign_keys=[recipient_id], back_populates="messages_received")


class ContactRequest(Base):
    __tablename__ = "contact_requests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    message = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
