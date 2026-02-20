#!/usr/bin/env python3
"""
Debug script to test Garmin workout import functionality.
This will help identify why imported workouts aren't showing up.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.database import get_db_session
from app.models.user import SharedWorkout, User, GarminCredentials, Workout
from app.services.garmin_service import GarminService
from app.core.security import decrypt_value

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


async def debug_workout_import():
    """Debug the workout import process."""
    print("=== Garmin Workout Import Debug ===\n")
    
    # Get database session
    async with get_db_session() as db:
        # 1. Check for users with Garmin credentials
        print("1. Checking for users with Garmin credentials...")
        result = await db.execute(
            "SELECT u.id, u.email, u.full_name, u.role, gc.is_connected, gc.last_sync "
            "FROM users u "
            "LEFT JOIN garmin_credentials gc ON u.id = gc.user_id "
            "WHERE gc.user_id IS NOT NULL"
        )
        users_with_creds = result.fetchall()
        
        if not users_with_creds:
            print("   No users found with Garmin credentials")
            return
        
        for user in users_with_creds:
            print(f"   User: {user.full_name} ({user.email}) - Role: {user.role}")
            print(f"   Garmin Connected: {user.is_connected}, Last Sync: {user.last_sync}")
        
        # 2. Check for shared workouts
        print("\n2. Checking for shared workouts...")
        result = await db.execute(
            "SELECT sw.id, sw.status, sw.shared_at, sw.import_error, sw.garmin_import_id, "
            "w.workout_name, w.workout_type, "
            "u_coach.full_name as coach_name, u_athlete.full_name as athlete_name "
            "FROM shared_workouts sw "
            "JOIN workouts w ON sw.workout_id = w.id "
            "JOIN users u_coach ON sw.coach_id = u_coach.id "
            "JOIN users u_athlete ON sw.athlete_id = u_athlete.id "
            "ORDER BY sw.shared_at DESC"
        )
        shared_workouts = result.fetchall()
        
        if not shared_workouts:
            print("   No shared workouts found")
            return
        
        print(f"   Found {len(shared_workouts)} shared workouts:")
        for sw in shared_workouts:
            print(f"   - {sw.workout_name} ({sw.workout_type})")
            print(f"     Coach: {sw.coach_name} -> Athlete: {sw.athlete_name}")
            print(f"     Status: {sw.status}, Shared: {sw.shared_at}")
            print(f"     Garmin Import ID: {sw.garmin_import_id}")
            if sw.import_error:
                print(f"     Import Error: {sw.import_error}")
            print()
        
        # 3. Test Garmin connection for a specific user
        print("3. Testing Garmin connection for athletes...")
        for user in users_with_creds:
            if user.role != 'athlete':
                continue
                
            print(f"\n   Testing connection for {user.full_name}...")
            
            # Get Garmin credentials
            creds_result = await db.execute(
                "SELECT garmin_email_encrypted, garmin_password_encrypted "
                "FROM garmin_credentials WHERE user_id = :user_id",
                {"user_id": user.id}
            )
            creds = creds_result.fetchone()
            
            if not creds:
                print(f"   No Garmin credentials found for {user.full_name}")
                continue
            
            try:
                # Test connection
                success, message = await GarminService.test_connection(
                    creds.garmin_email_encrypted,
                    creds.garmin_password_encrypted
                )
                print(f"   Connection test: {'SUCCESS' if success else 'FAILED'}")
                print(f"   Message: {message}")
                
                if success:
                    # Get workouts from Garmin
                    success2, message2, workouts = await GarminService.get_workouts(
                        creds.garmin_email_encrypted,
                        creds.garmin_password_encrypted
                    )
                    print(f"   Workout fetch: {'SUCCESS' if success2 else 'FAILED'}")
                    print(f"   Message: {message2}")
                    if success2:
                        print(f"   Found {len(workouts)} workouts in Garmin Connect")
                        for w in workouts[:3]:  # Show first 3
                            print(f"     - {w['workout_name']} (ID: {w['garmin_workout_id']})")
                
            except Exception as e:
                print(f"   ERROR: {e}")
                logger.exception("Garmin connection test failed")
        
        # 4. Check for pending imports that might be stuck
        print("\n4. Checking for stuck pending workouts...")
        result = await db.execute(
            "SELECT sw.id, sw.shared_at, w.workout_name, u_athlete.full_name "
            "FROM shared_workouts sw "
            "JOIN workouts w ON sw.workout_id = w.id "
            "JOIN users u_athlete ON sw.athlete_id = u_athlete.id "
            "WHERE sw.status = 'pending' "
            "AND sw.shared_at < :cutoff",
            {"cutoff": datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)}
        )
        old_pending = result.fetchall()
        
        if old_pending:
            print(f"   Found {len(old_pending)} workouts stuck in pending status:")
            for sw in old_pending:
                print(f"   - {sw.workout_name} for {sw.full_name} (shared: {sw.shared_at})")
        else:
            print("   No workouts stuck in pending status")


if __name__ == "__main__":
    asyncio.run(debug_workout_import())
