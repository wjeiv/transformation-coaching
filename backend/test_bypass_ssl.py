#!/usr/bin/env python3
"""Test Garmin Connect with SSL bypass as workaround."""

import os
import sys
import ssl
import warnings

# Disable SSL warnings
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# Create unverified context
ssl._create_default_https_context = ssl._create_unverified_context

# Add the backend directory to Python path
sys.path.insert(0, '/home/belliott/transformation-coaching/backend')

from garminconnect import Garmin

def test_garmin_bypass_ssl():
    """Test Garmin Connect with SSL verification disabled."""
    print("=" * 60)
    print("GARMIN CONNECT TEST - SSL VERIFICATION DISABLED")
    print("=" * 60)
    print("⚠️  WARNING: This is insecure for testing only!")
    print()
    
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
        
        print("\n🎉 Garmin Connect is working with SSL verification disabled!")
        print("\n⚠️  IMPORTANT:")
        print("- This configuration is insecure and should NOT be used in production")
        print("- The certificate you provided works for Garmin but not Amazon S3")
        print("- For production use, you need a certificate that includes Amazon's root CA")
        print("- Or connect from a network that doesn't intercept SSL traffic")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_garmin_bypass_ssl()
