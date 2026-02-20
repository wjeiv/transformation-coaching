#!/usr/bin/env python3
"""
End-to-end test of the fixed Garmin workout import functionality.
This will test the complete flow with real data.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_import_flow():
    """Test the complete workout import flow."""
    print("=== End-to-End Garmin Workout Import Test ===\n")
    
    try:
        from app.core.database import get_db
        from app.models.user import SharedWorkout, User, GarminCredentials
        from app.services.garmin_service import GarminService
        from app.core.security import decrypt_value
        
        # Get database session
        async for db in get_db():
            # 1. Find users with Garmin credentials
            print("1. Finding users with Garmin credentials...")
            result = await db.execute(
                "SELECT u.id, u.email, u.full_name, u.role, gc.is_connected "
                "FROM users u "
                "JOIN garmin_credentials gc ON u.id = gc.user_id "
                "WHERE gc.is_connected = true "
                "LIMIT 1"
            )
            user = result.fetchone()
            
            if not user:
                print("   No users with connected Garmin accounts found")
                return
            
            print(f"   Found user: {user.full_name} ({user.email})")
            
            # 2. Find pending shared workouts
            print("\n2. Finding pending shared workouts...")
            result = await db.execute(
                "SELECT sw.id, sw.shared_at, w.workout_name, w.workout_data, "
                "u_coach.full_name as coach_name "
                "FROM shared_workouts sw "
                "JOIN workouts w ON sw.workout_id = w.id "
                "JOIN users u_coach ON sw.coach_id = u_coach.id "
                "WHERE sw.athlete_id = :user_id AND sw.status = 'pending' "
                "ORDER BY sw.shared_at DESC "
                "LIMIT 1",
                {"user_id": user.id}
            )
            pending_workout = result.fetchone()
            
            if not pending_workout:
                print("   No pending workouts found")
                return
            
            print(f"   Found pending workout: {pending_workout.workout_name}")
            print(f"   Shared by: {pending_workout.coach_name}")
            print(f"   Shared on: {pending_workout.shared_at}")
            
            # 3. Get Garmin credentials
            print("\n3. Retrieving Garmin credentials...")
            result = await db.execute(
                "SELECT garmin_email_encrypted, garmin_password_encrypted "
                "FROM garmin_credentials WHERE user_id = :user_id",
                {"user_id": user.id}
            )
            creds = result.fetchone()
            
            if not creds:
                print("   No Garmin credentials found")
                return
            
            print("   Garmin credentials retrieved")
            
            # 4. Test Garmin connection
            print("\n4. Testing Garmin connection...")
            success, message = await GarminService.test_connection(
                creds.garmin_email_encrypted,
                creds.garmin_password_encrypted
            )
            
            if not success:
                print(f"   ❌ Connection failed: {message}")
                return
            
            print(f"   ✅ Connection successful: {message}")
            
            # 5. Parse workout data
            print("\n5. Parsing workout data...")
            try:
                workout_data = json.loads(pending_workout.workout_data)
                print(f"   Workout data parsed successfully")
                print(f"   Workout keys: {list(workout_data.keys())}")
            except json.JSONDecodeError as e:
                print(f"   ❌ Failed to parse workout data: {e}")
                return
            
            # 6. Test workout import
            print("\n6. Testing workout import...")
            try:
                success, message, garmin_id = await GarminService.import_workout(
                    creds.garmin_email_encrypted,
                    creds.garmin_password_encrypted,
                    workout_data
                )
                
                if success:
                    print(f"   ✅ Import successful: {message}")
                    print(f"   New Garmin workout ID: {garmin_id}")
                    
                    # 7. Update database record
                    print("\n7. Updating database record...")
                    await db.execute(
                        "UPDATE shared_workouts "
                        "SET status = 'imported', garmin_import_id = :garmin_id, imported_at = :now "
                        "WHERE id = :sw_id",
                        {
                            "garmin_id": garmin_id,
                            "now": datetime.now(timezone.utc),
                            "sw_id": pending_workout.id
                        }
                    )
                    await db.flush()
                    print("   ✅ Database updated")
                    
                else:
                    print(f"   ❌ Import failed: {message}")
                    
            except Exception as e:
                print(f"   ❌ Import error: {e}")
                logger.exception("Workout import failed")
            
            print("\n=== Test Complete ===")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.exception("End-to-end test failed")

if __name__ == "__main__":
    asyncio.run(test_complete_import_flow())
