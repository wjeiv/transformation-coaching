#!/usr/bin/env python3
"""
Update existing admin user email from 'admin' to 'admin@transformationcoaching.com'
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import select
from app.core.database import async_session, init_db
from app.models.user import User

async def update_admin_email():
    await init_db()
    async with async_session() as session:
        # Find admin user with email "admin"
        result = await session.execute(
            select(User).where(User.email == "admin")
        )
        admin_user = result.scalar_one_or_none()
        
        if admin_user:
            # Update email to admin@transformationcoaching.com
            admin_user.email = "admin@transformationcoaching.com"
            await session.commit()
            print(f"✅ Updated admin email: {admin_user.email}")
        else:
            print("❌ No admin user found with email 'admin'")
            
        # Check if admin with correct email already exists
        result = await session.execute(
            select(User).where(User.email == "admin@transformationcoaching.com")
        )
        admin_user = result.scalar_one_or_none()
        
        if admin_user:
            print(f"✅ Admin account confirmed: {admin_user.email}")
            print(f"   Role: {admin_user.role}")
            print(f"   Active: {admin_user.is_active}")
        else:
            print("❌ No admin user found with email 'admin@transformationcoaching.com'")

if __name__ == "__main__":
    asyncio.run(update_admin_email())
