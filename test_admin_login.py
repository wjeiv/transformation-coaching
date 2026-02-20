#!/usr/bin/env python3
"""Test admin login and password verification."""

import asyncio
from sqlalchemy import select
from app.core.database import async_session
from app.models.user import User, UserRole
from app.core.security import verify_password
from app.core.config import settings


async def test_admin_login():
    """Test admin account and password verification."""
    print("=== Testing Admin Login ===")
    print()
    
    async with async_session() as session:
        result = await session.execute(select(User).where(User.role == UserRole.ADMIN))
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("❌ No admin account found!")
            return
            
        print(f"✅ Admin found: {admin.email}")
        print(f"✅ Full name: {admin.full_name}")
        print(f"✅ Role: {admin.role}")
        print(f"✅ Hash starts with: {admin.hashed_password[:50]}...")
        print()
        
        # Test various passwords
        passwords_to_test = [
            "changeme123!",
            settings.FIRST_ADMIN_PASSWORD,
            "admin123",
            "changeme123"
        ]
        
        for password in passwords_to_test:
            is_valid = verify_password(password, admin.hashed_password)
            status = "✅" if is_valid else "❌"
            print(f"{status} Password '{password}': {is_valid}")
        
        print()
        print(f"Config FIRST_ADMIN_PASSWORD: '{settings.FIRST_ADMIN_PASSWORD}'")


if __name__ == "__main__":
    asyncio.run(test_admin_login())
