#!/usr/bin/env python3
"""
Debug script to inspect users and debug authentication issues.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import async_session
from app.models.user import User, UserRole
from sqlalchemy import select


async def debug_users():
    """Debug user accounts and authentication."""
    print("=== User Account Debug ===")
    print()
    
    async with async_session() as session:
        # Get all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print(f"Total users in database: {len(users)}")
        print()
        
        for user in users:
            print(f"User: {user.email}")
            print(f"  ID: {user.id}")
            print(f"  Role: {user.role}")
            print(f"  Full Name: {user.full_name}")
            print(f"  Is Active: {user.is_active}")
            print(f"  Created: {user.created_at}")
            print(f"  Password Hash (first 50 chars): {user.hashed_password[:50]}...")
            print()
        
        if not users:
            print("No users found in database!")
            print("You may need to create an admin account first.")
        
        return users


async def debug_admin():
    """Specifically debug admin account."""
    print("=== Admin Account Debug ===")
    print()
    
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        admin = result.scalar_one_or_none()
        
        if admin:
            print("✅ Admin account found:")
            print(f"  Email: {admin.email}")
            print(f"  Role: {admin.role}")
            print(f"  Is Active: {admin.is_active}")
            print(f"  Created: {admin.created_at}")
            print()
            print("Login credentials should be:")
            print(f"  Email: {admin.email}")
            print("  Password: admin123 (if created with debug script)")
        else:
            print("❌ No admin account found!")
            print("Run: python create_admin.py")


async def main():
    """Main debug function."""
    try:
        await debug_users()
        await debug_admin()
        
        print("\n=== Authentication Debug Tips ===")
        print("1. Check backend logs for API request errors")
        print("2. Check browser console for JavaScript errors")
        print("3. Check network tab for HTTP status codes")
        print("4. Verify CORS origins in dev.env")
        print("5. Test login via API docs: http://localhost:8000/api/v1/docs")
        
    except Exception as e:
        print(f"❌ Debug error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
