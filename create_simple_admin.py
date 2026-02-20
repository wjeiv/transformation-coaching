#!/usr/bin/env python3
"""
Simple admin creation without foreign key issues
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import select, delete
from app.core.database import async_session, init_db
from app.core.security import get_password_hash
from app.models.user import User, UserRole

async def create_simple_admin():
    await init_db()
    async with async_session() as session:
        # Delete all existing admin users first
        await session.execute(
            delete(User).where(User.role == UserRole.ADMIN)
        )
        await session.commit()
        
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
        
        print(f"✅ Created admin account:")
        print(f"   Email: {admin_user.email}")
        print(f"   Password: {password}")
        print(f"   Role: {admin_user.role}")
        print(f"   Active: {admin_user.is_active}")

if __name__ == "__main__":
    asyncio.run(create_simple_admin())
