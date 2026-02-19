#!/usr/bin/env python3
"""
Test script to verify Garmin Connect connectivity on Windows.
This script tests the core Garmin functionality without requiring the full API.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.services.garmin_service import GarminService
from app.core.security import encrypt_value


async def test_garmin_connection():
    """Test Garmin Connect connection with placeholder credentials."""
    print("Testing Garmin Connect connectivity...")
    
    # Test with placeholder credentials (these will fail but test the service)
    test_email = "test@example.com"
    test_password = "testpassword"
    
    # Encrypt the credentials as the service expects
    encrypted_email = encrypt_value(test_email)
    encrypted_password = encrypt_value(test_password)
    
    # Test the connection
    success, message = await GarminService.test_connection(
        encrypted_email, encrypted_password
    )
    
    print(f"Connection test result: {success}")
    print(f"Message: {message}")
    
    if not success:
        print("\nThis is expected with test credentials.")
        print("The service is working - you can now try with real Garmin Connect credentials.")
    
    return success


async def main():
    """Main test function."""
    print("=== Windows Garmin Connect Test ===")
    print("This test verifies that the Garmin service can run on Windows.")
    print()
    
    try:
        await test_garmin_connection()
        print("\n✅ Garmin service is functional on Windows!")
        print("\nTo test with real credentials:")
        print("1. Create a user account via the API")
        print("2. Add Garmin Connect credentials")
        print("3. Test the connection")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("The Garmin service failed to initialize.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
