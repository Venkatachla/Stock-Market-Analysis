"""
Tests for api/auth.py — JWT token generation, password hashing, and verification.

Covers:
- SHA256 password hashing (current production format)
- bcrypt password verification (future-proofing path)
- JWT access token creation with correct claims
- JWT token verification (valid, expired, invalid, missing email)
"""
import hashlib
from datetime import timedelta

import pytest
from jose import jwt

from api.auth import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    SECRET_KEY,
    ALGORITHM,
)


class TestHashPassword:
    """Test hash_password() produces bcrypt hashes."""

    def test_produces_bcrypt_hash(self):
        result = hash_password("mypassword")
        assert result.startswith("$2")

    def test_different_passwords_produce_different_hashes(self):
        h1 = hash_password("password1")
        h2 = hash_password("password2")
        assert h1 != h2

    def test_same_password_produces_different_hash_due_to_salt(self):
        # bcrypt is non-deterministic
        assert hash_password("test") != hash_password("test")

    def test_empty_string_hashes(self):
        # Edge case: empty password should still produce a valid hash
        result = hash_password("")
        assert result.startswith("$2")


class TestVerifyPassword:
    """Test verify_password() against SHA256 and bcrypt formats."""

    def test_correct_sha256_password(self):
        import hashlib
        hashed = hashlib.sha256("correctpassword".encode()).hexdigest()
        assert verify_password("correctpassword", hashed) is True

    def test_wrong_sha256_password(self):
        import hashlib
        hashed = hashlib.sha256("correctpassword".encode()).hexdigest()
        assert verify_password("wrongpassword", hashed) is False

    def test_correct_bcrypt_password(self):
        hashed = hash_password("correctpassword")
        assert verify_password("correctpassword", hashed) is True

    def test_bcrypt_format_fallback(self):
        # Test that bcrypt-prefixed hashes trigger the bcrypt path
        # Using a deliberately wrong bcrypt hash to test the fallback returns False
        fake_bcrypt = "$2b$12$invalidhashvaluexxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
        assert verify_password("anything", fake_bcrypt) is False

    def test_non_matching_hash_format(self):
        # Arbitrary hash that doesn't match SHA256 or bcrypt
        assert verify_password("test", "not_a_valid_hash") is False


class TestCreateAccessToken:
    """Test create_access_token() produces valid JWT tokens."""

    def test_creates_valid_jwt(self):
        token = create_access_token("user@test.com", 42)
        # Should decode without error
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["email"] == "user@test.com"
        assert payload["user_id"] == 42

    def test_token_contains_expiry(self):
        token = create_access_token("user@test.com", 1)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "exp" in payload
        assert "iat" in payload

    def test_custom_expiry_delta(self):
        # Short expiry for testing
        token = create_access_token("user@test.com", 1, expires_delta=timedelta(minutes=5))
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert payload["email"] == "user@test.com"

    def test_default_expiry_is_24_hours(self):
        token = create_access_token("user@test.com", 1)
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # iat and exp should differ by ~1440 minutes (24 hours)
        diff = payload["exp"] - payload["iat"]
        assert abs(diff - 86400) < 10  # within 10 seconds tolerance


class TestVerifyToken:
    """Test verify_token() for valid, invalid, and edge-case tokens."""

    def test_valid_token_returns_token_data(self):
        token = create_access_token("user@test.com", 1)
        result = verify_token(token)
        assert result is not None
        assert result.email == "user@test.com"

    def test_invalid_token_returns_none(self):
        result = verify_token("this.is.not.a.valid.jwt")
        assert result is None

    def test_expired_token_returns_none(self):
        # Create a token that expired 1 hour ago
        token = create_access_token("user@test.com", 1, expires_delta=timedelta(hours=-1))
        result = verify_token(token)
        assert result is None

    def test_tampered_token_returns_none(self):
        token = create_access_token("user@test.com", 1)
        # Tamper with the token by changing a character
        tampered = token[:-5] + "XXXXX"
        result = verify_token(tampered)
        assert result is None

    def test_token_without_email_returns_none(self):
        # Manually create a token missing the email claim
        payload = {"user_id": 1, "exp": 9999999999}
        token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        result = verify_token(token)
        assert result is None
