import pytest
from datetime import timedelta
import os
from api.auth import (
    hash_password,
    verify_password,
    needs_password_migration,
    create_access_token,
    verify_token
)
from jose import jwt

# Ensure SECRET_KEY is set for tests
os.environ["SECRET_KEY"] = "test_super_secret_key_that_is_long_enough"

def test_hash_password():
    """Test that password hashing uses bcrypt and returns a valid hash."""
    pwd = "MySuperSecretPassword123"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert hashed.startswith("$2")  # bcrypt identifier

def test_verify_password_bcrypt():
    """Test verification of a valid bcrypt hash."""
    pwd = "MySuperSecretPassword123"
    hashed = hash_password(pwd)
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_verify_password_legacy_sha256():
    """Test fallback verification of a legacy SHA-256 hash."""
    import hashlib
    pwd = "LegacyPassword123"
    legacy_hash = hashlib.sha256(pwd.encode()).hexdigest()
    assert verify_password(pwd, legacy_hash) is True
    assert verify_password("wrongpassword", legacy_hash) is False

def test_needs_password_migration():
    """Test migration check logic."""
    import hashlib
    legacy_hash = hashlib.sha256(b"LegacyPassword123").hexdigest()
    bcrypt_hash = hash_password("NewPassword123")
    
    assert needs_password_migration(legacy_hash) is True
    assert needs_password_migration(bcrypt_hash) is False

def test_create_and_verify_token():
    """Test JWT creation and verification cycle."""
    email = "test@example.com"
    user_id = 1
    
    token = create_access_token(email, user_id)
    assert isinstance(token, str)
    
    token_data = verify_token(token)
    assert token_data is not None
    assert token_data.email == email

def test_verify_token_expired():
    """Test that expired tokens are rejected."""
    email = "test@example.com"
    user_id = 1
    # Create a token that expired 1 minute ago
    token = create_access_token(email, user_id, expires_delta=timedelta(minutes=-1))
    
    token_data = verify_token(token)
    assert token_data is None

def test_verify_token_invalid():
    """Test that garbage tokens return None."""
    assert verify_token("this.is.not.a.real.token") is None
    assert verify_token("") is None
