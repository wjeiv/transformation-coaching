#!/usr/bin/env python3
"""Simple Garmin Connect test following standard approach."""

import os
import sys

# Add the backend directory to Python path
sys.path.insert(0, '/home/belliott/transformation-coaching/backend')

from garminconnect import Garmin

def test_garmin_standard():
    """Test Garmin Connect with standard approach."""
    print("=" * 60)
    print("GARMIN CONNECT STANDARD TEST")
    print("=" * 60)
    
    # Your credentials
    email = "wjeiv4@gmail.com"
    password = "SdfRfv1!"
    
    print(f"Email: {email}")
    print()
    
    try:
        print("Creating Garmin client...")
        client = Garmin(email, password)
        
        print("Attempting login...")
        client.login()
        
        print("✅ SUCCESS: Logged in to Garmin Connect!")
        
        # Get user info
        print("\nGetting user profile...")
        full_name = client.get_full_name()
        print(f"   User: {full_name}")
        
        # Get unit system
        unit_system = client.get_unit_system()
        print(f"   Unit System: {unit_system}")
        
        # Get today's activities
        from datetime import date
        today = date.today().isoformat()
        
        print(f"\nGetting activities for {today}...")
        activities = client.get_activities_by_date(today, today)
        
        if activities:
            print(f"   Found {len(activities)} activities today:")
            for activity in activities[:3]:
                act_name = activity.get('activityName', 'Unnamed')
                act_type = activity.get('activityType', {}).get('typeKey', 'Unknown')
                print(f"   - {act_name} ({act_type})")
        else:
            print("   No activities found for today")
        
        # Get workouts
        print("\nGetting workouts...")
        workouts = client.get_workouts()
        print(f"   Found {len(workouts)} workouts in total")
        
        if workouts:
            print("   Recent workouts:")
            for workout in workouts[:3]:
                name = workout.get('workoutName', 'Unnamed')
                sport = workout.get('sportType', {}).get('sportTypeKey', 'Unknown')
                print(f"   - {name} ({sport})")
        
        print("\n🎉 Garmin Connect is working successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
        if "SSL" in str(e) or "certificate" in str(e).lower():
            print("\nThis appears to be an SSL/certificate issue.")
            print("In a corporate environment, you may need to:")
            print("1. Use a VPN to bypass corporate SSL inspection")
            print("2. Try from a different network (home, mobile)")
            print("3. Configure corporate certificates properly")
        
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_garmin_standard()
