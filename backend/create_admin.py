#!/usr/bin/env python3
"""
Create admin account script for Windows development.
This script creates the first admin account manually to avoid bcrypt startup issues.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import async_session
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from sqlalchemy import select


# Simple password hash to avoid bcrypt issues
def simple_password_hash(password: str) -> str:
    import hashlib
    return hashlib.sha256(password.encode()).hexdigest()


async def create_admin_account():
    """Create the first admin account."""
    async with async_session() as session:
        # Check if admin already exists
        from sqlalchemy import select
        result = await session.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print(f"Admin account already exists: {existing_admin.email}")
            return existing_admin
        
        # Create new admin account
        password = "FFester1!"  # Simple password
        admin_user = User(
            email="admin",
            hashed_password=simple_password_hash(password),
            full_name="Administrator",
            role=UserRole.ADMIN,
        )
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        print(f"Created admin account: {admin_user.email}")
        print("Login credentials:")
        print("  Email: admin")
        print(f"  Password: {password}")
        print()
        print("You can now log in to the application at:")
        print("  Frontend: http://localhost:3000")
        print("  API Docs: http://localhost:8000/api/v1/docs")
        
        return admin_user


async def main():
    """Main function."""
    print("=== Creating Admin Account ===")
    print()
    
    try:
        await create_admin_account()
        print("\n✅ Admin account created successfully!")
        
    except Exception as e:
        print(f"\n❌ Error creating admin account: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
