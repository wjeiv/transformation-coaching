#!/usr/bin/env python3
"""
Delete and recreate admin account with correct email and password
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import select, delete
from app.core.database import async_session, init_db
from app.core.security import get_password_hash
from app.models.user import User, UserRole

async def recreate_admin():
    await init_db()
    async with async_session() as session:
        # Delete existing admin users
        await session.execute(
            delete(User).where(User.email.in_(["admin", "admin@transformationcoaching.com"]))
        )
        await session.commit()
        print("✅ Deleted existing admin users")
        
        # Create new admin account
        password = "FFester1!"
        admin_user = User(
            email="admin@transformationcoaching.com",
            hashed_password=get_password_hash(password),
            full_name="Administrator",
            role=UserRole.ADMIN,
            is_active=True,
        )
        session.add(admin_user)
        await session.commit()
        await session.refresh(admin_user)
        
        print(f"✅ Created new admin account:")
        print(f"   Email: {admin_user.email}")
        print(f"   Password: {password}")
        print(f"   Role: {admin_user.role}")
        print(f"   Active: {admin_user.is_active}")

if __name__ == "__main__":
    asyncio.run(recreate_admin())
