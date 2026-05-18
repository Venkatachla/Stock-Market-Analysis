"""
Authentication module for JWT token generation, password hashing, and user verification.
"""
from datetime import datetime, timedelta
from typing import Optional
import os

from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    email: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    tier: str
    is_admin: bool


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hash - support both SHA256 and bcrypt"""
    import hashlib
    
    # Try bcrypt first (modern format)
    if hashed_password.startswith("$2"):
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            pass
        return False
    
    # Try SHA256 (legacy format)
    sha256_hash = hashlib.sha256(plain_password.encode()).hexdigest()
    if sha256_hash == hashed_password:
        return True
    
    return False


def needs_password_migration(hashed_password: str) -> bool:
    """Check if password needs to be migrated to the latest hashing scheme"""
    if not hashed_password.startswith("$2"):
        return True
    return pwd_context.needs_update(hashed_password)


def create_access_token(email: str, user_id: int, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "email": email,
        "user_id": user_id,
        "exp": expire,
        "iat": datetime.utcnow()
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verify JWT token and extract email"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        if email is None:
            return None
        return TokenData(email=email)
    except JWTError:
        return None
