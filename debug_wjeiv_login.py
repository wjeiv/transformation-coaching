#!/usr/bin/env python3
"""
Check existing users and their login status
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import select
from app.core.database import async_session, init_db
from app.models.user import User

async def debug_users():
    await init_db()
    async with async_session() as session:
        # Check all users
        result = await session.execute(select(User))
        users = result.scalars().all()
        
        print("📋 All users in database:")
        for user in users:
            print(f"  - {user.email}")
            print(f"    Role: {user.role}")
            print(f"    Active: {user.is_active}")
            print(f"    ID: {user.id}")
            print(f"    Full Name: {user.full_name}")
            print(f"    Last Login: {user.last_login}")
            print()
            
        # Test wjeiv4@gmail.com password
        result = await session.execute(
            select(User).where(User.email == "wjeiv4@gmail.com")
        )
        wjeiv_user = result.scalar_one_or_none()
        
        if wjeiv_user:
            print("🔑 Testing wjeiv4@gmail.com login:")
            print(f"   User exists: {wjeiv_user.email}")
            print(f"   Password hash: {wjeiv_user.hashed_password}")
            print(f"   Try password: 'FFester1!'")
            
            # Verify password
            from app.core.security import verify_password
            if verify_password("FFester1!", wjeiv_user.hashed_password):
                print("   ✅ Password 'FFester1!' is CORRECT")
            else:
                print("   ❌ Password 'FFester1!' is INCORRECT")
                print("   🔍 This user might have a different password")
        else:
            print("❌ wjeiv4@gmail.com user not found")

if __name__ == "__main__":
    asyncio.run(debug_users())
