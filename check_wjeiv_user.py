#!/usr/bin/env python3
"""
Check if wjeiv4@gmail.com user exists and debug login issues
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import select
from app.core.database import async_session, init_db
from app.models.user import User

async def check_user():
    await init_db()
    async with async_session() as session:
        # Check if wjeiv4@gmail.com exists
        result = await session.execute(
            select(User).where(User.email == "wjeiv4@gmail.com")
        )
        user = result.scalar_one_or_none()
        
        if user:
            print(f"✅ User found: {user.email}")
            print(f"   Role: {user.role}")
            print(f"   Active: {user.is_active}")
            print(f"   ID: {user.id}")
            print(f"   Full Name: {user.full_name}")
        else:
            print("❌ User wjeiv4@gmail.com not found in database")
            
        # Check all users in database
        print("\n📋 All users in database:")
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        for user in users:
            print(f"  - {user.email} ({user.role}, Active: {user.is_active})")

if __name__ == "__main__":
    asyncio.run(check_user())
