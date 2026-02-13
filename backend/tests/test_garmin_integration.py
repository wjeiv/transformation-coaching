"""
Garmin Connect Integration Tests

These tests require REAL Garmin Connect credentials to verify actual connectivity.
Set the following environment variables before running:

    GARMIN_TEST_EMAIL=your-garmin-email@example.com
    GARMIN_TEST_PASSWORD=your-garmin-password

Run with:
    pytest tests/test_garmin_integration.py -v -s --run-garmin

These tests are SKIPPED by default (they require real credentials and network).
"""

import os

import pytest

from app.core.security import encrypt_value
from app.services.garmin_service import GarminService


def garmin_credentials_available() -> bool:
    return bool(os.getenv("GARMIN_TEST_EMAIL") and os.getenv("GARMIN_TEST_PASSWORD"))


def pytest_configure(config):
    config.addinivalue_line("markers", "garmin: tests requiring real Garmin Connect credentials")


skip_no_garmin = pytest.mark.skipif(
    not garmin_credentials_available(),
    reason="GARMIN_TEST_EMAIL and GARMIN_TEST_PASSWORD env vars not set",
)


@skip_no_garmin
@pytest.mark.asyncio
async def test_garmin_connect_authentication():
    """Test that we can authenticate with Garmin Connect using real credentials."""
    email = os.getenv("GARMIN_TEST_EMAIL", "")
    password = os.getenv("GARMIN_TEST_PASSWORD", "")

    encrypted_email = encrypt_value(email)
    encrypted_password = encrypt_value(password)

    success, message = await GarminService.test_connection(encrypted_email, encrypted_password)

    assert success is True, f"Garmin authentication failed: {message}"
    assert "Successfully connected" in message
    print(f"\n✓ Garmin Connect authentication successful: {message}")


@skip_no_garmin
@pytest.mark.asyncio
async def test_garmin_connect_bad_credentials():
    """Test that bad credentials produce a clear error message."""
    encrypted_email = encrypt_value("fake@example.com")
    encrypted_password = encrypt_value("wrongpassword")

    success, message = await GarminService.test_connection(encrypted_email, encrypted_password)

    assert success is False
    assert "Authentication failed" in message or "invalid" in message.lower()
    print(f"\n✓ Bad credentials correctly rejected: {message}")


@skip_no_garmin
@pytest.mark.asyncio
async def test_garmin_fetch_workouts():
    """Test that we can fetch workouts from a real Garmin Connect account."""
    email = os.getenv("GARMIN_TEST_EMAIL", "")
    password = os.getenv("GARMIN_TEST_PASSWORD", "")

    encrypted_email = encrypt_value(email)
    encrypted_password = encrypt_value(password)

    success, message, workouts = await GarminService.get_workouts(encrypted_email, encrypted_password)

    assert success is True, f"Failed to fetch workouts: {message}"
    assert isinstance(workouts, list)
    print(f"\n✓ Fetched {len(workouts)} workouts from Garmin Connect")

    if workouts:
        w = workouts[0]
        assert "garmin_workout_id" in w
        assert "workout_name" in w
        assert "workout_type" in w
        assert w["workout_type"] in ("running", "cycling", "swimming", "strength", "other")
        print(f"  First workout: {w['workout_name']} ({w['workout_type']})")


@skip_no_garmin
@pytest.mark.asyncio
async def test_garmin_athlete_connection_check():
    """Test the athlete connection check with detailed status reporting."""
    email = os.getenv("GARMIN_TEST_EMAIL", "")
    password = os.getenv("GARMIN_TEST_PASSWORD", "")

    encrypted_email = encrypt_value(email)
    encrypted_password = encrypt_value(password)

    result = await GarminService.check_athlete_connection(encrypted_email, encrypted_password)

    assert result["is_connected"] is True
    assert "Ready for workout sync" in result["message"]
    assert result["recommendations"] == []
    print(f"\n✓ Athlete connection check passed: {result['message']}")


@skip_no_garmin
@pytest.mark.asyncio
async def test_garmin_athlete_connection_check_bad_creds():
    """Test that connection check provides helpful recommendations on failure."""
    encrypted_email = encrypt_value("bad@example.com")
    encrypted_password = encrypt_value("badpassword")

    result = await GarminService.check_athlete_connection(encrypted_email, encrypted_password)

    assert result["is_connected"] is False
    assert len(result["recommendations"]) > 0
    print(f"\n✓ Bad connection check returned {len(result['recommendations'])} recommendations:")
    for r in result["recommendations"]:
        print(f"  - {r}")
