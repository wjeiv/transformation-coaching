import base64
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from cryptography.fernet import Fernet
from jose import jwt
import bcrypt

from app.core.config import settings

ALGORITHM = "HS256"


def _get_fernet() -> Fernet:
    key = settings.GARMIN_ENCRYPTION_KEY
    # Ensure key is valid Fernet key (32 url-safe base64-encoded bytes)
    padded = base64.urlsafe_b64encode(key.encode()[:32].ljust(32, b"\0"))
    return Fernet(padded)


def encrypt_value(plain: str) -> str:
    f = _get_fernet()
    return f.encrypt(plain.encode()).decode()


def decrypt_value(token: str) -> str:
    f = _get_fernet()
    return f.decrypt(token.encode()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    try:
        # Check if it's a bcrypt hash
        if hashed_password.startswith('$2b$') or hashed_password.startswith('$2a$'):
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        else:
            # Fallback to SHA256 for backward compatibility
            return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Generate a password hash using bcrypt."""
    try:
        # Generate salt and hash with bcrypt
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    except Exception:
        # Fallback to SHA256 if bcrypt fails
        return hashlib.sha256(password.encode()).hexdigest()


def create_access_token(subject: Any, expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(subject: Any) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
