#!/usr/bin/env python3
"""
Create default coach users including wjeiv4@gmail.com
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from sqlalchemy import select
from app.core.database import async_session, init_db
from app.core.security import get_password_hash
from app.models.user import User, UserRole

async def create_coach_users():
    await init_db()
    async with async_session() as session:
        # Create Bill Elliott (wjeiv4@gmail.com)
        bill_user = User(
            email="wjeiv4@gmail.com",
            hashed_password=get_password_hash("FFester1!"),
            full_name="Bill Elliott",
            role=UserRole.COACH,
            is_active=True,
        )
        session.add(bill_user)
        
        # Create Heather Gladwin
        heather_user = User(
            email="transformation.coaching26.2@gmail.com",
            hashed_password=get_password_hash("FFester1!"),
            full_name="Heather Gladwin",
            role=UserRole.COACH,
            is_active=True,
        )
        session.add(heather_user)
        
        # Create Gretchen Hickey (athlete)
        gretchen_user = User(
            email="gretchen.hickey@example.com",
            hashed_password=get_password_hash("FFester1!"),
            full_name="Gretchen Hickey",
            role=UserRole.ATHLETE,
            is_active=True,
        )
        session.add(gretchen_user)
        
        await session.commit()
        
        print("✅ Created default users:")
        print(f"  - Coach: wjeiv4@gmail.com (Bill Elliott)")
        print(f"  - Coach: transformation.coaching26.2@gmail.com (Heather Gladwin)")
        print(f"  - Athlete: gretchen.hickey@example.com (Gretchen Hickey)")
        print(f"\n🔑 Login credentials for wjeiv4@gmail.com:")
        print(f"   Email: wjeiv4@gmail.com")
        print(f"   Password: FFester1!")

if __name__ == "__main__":
    asyncio.run(create_coach_users())
