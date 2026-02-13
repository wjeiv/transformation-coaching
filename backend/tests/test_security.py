import pytest

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    encrypt_value,
    decrypt_value,
    get_password_hash,
    verify_password,
)


def test_password_hash_and_verify():
    password = "mysecretpassword"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False


def test_access_token_creation_and_decode():
    token = create_access_token(subject=42)
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "access"


def test_refresh_token_creation_and_decode():
    token = create_refresh_token(subject=42)
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["type"] == "refresh"


def test_encrypt_decrypt_roundtrip():
    original = "my-secret-garmin-password"
    encrypted = encrypt_value(original)
    assert encrypted != original
    decrypted = decrypt_value(encrypted)
    assert decrypted == original


def test_encrypt_different_values_produce_different_ciphertexts():
    a = encrypt_value("password1")
    b = encrypt_value("password2")
    assert a != b
