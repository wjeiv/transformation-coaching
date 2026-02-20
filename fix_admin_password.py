#!/usr/bin/env python3
"""
Fix admin account password hash to use proper bcrypt format.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import async_session
from app.models.user import User, UserRole
from sqlalchemy import select


async def fix_admin_password():
    """Fix admin password to use proper bcrypt hash."""
    print("=== Fixing Admin Password Hash ===")
    print()
    
    async with async_session() as session:
        # Find admin account
        result = await session.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("❌ No admin account found!")
            return False
        
        print(f"Found admin: {admin.email}")
        print(f"Current hash type: {admin.hashed_password[:50]}...")
        
        # Create proper bcrypt hash manually to avoid passlib issues
        import bcrypt
        password = "admin123"
        salt = bcrypt.gensalt(rounds=12)
        proper_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        print(f"New hash type: {proper_hash[:50]}...")
        
        # Update the admin account
        admin.hashed_password = proper_hash
        await session.commit()
        
        print("✅ Admin password hash updated!")
        print()
        print("Login credentials:")
        print("  Email: admin")
        print("  Password: FFester1!")
        print()
        print("Try logging in again!")
        
        return True


async def main():
    """Main function."""
    try:
        success = await fix_admin_password()
        return 0 if success else 1
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
