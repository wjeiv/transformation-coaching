#!/usr/bin/env python3
"""Test Garmin Connect with the provided certificate."""

import os
import sys
import ssl

# Add the backend directory to Python path
sys.path.insert(0, '/home/belliott/transformation-coaching/backend')

# Set up SSL with the certificate
cert_path = "/home/belliott/transformation-coaching/backend/certs/full-chain.pem"

# Create SSL context and load the certificate
context = ssl.create_default_context()
context.load_verify_locations(cert_path)

# Make it the default context
ssl._create_default_https_context = lambda: context

# Also set environment variables
os.environ['SSL_CERT_FILE'] = cert_path
os.environ['REQUESTS_CA_BUNDLE'] = cert_path
os.environ['CURL_CA_BUNDLE'] = cert_path

print(f"Loaded SSL certificate from: {cert_path}")
print()

# Now test Garmin Connect
from garminconnect import Garmin

def test_garmin_with_cert():
    """Test Garmin Connect with the certificate."""
    print("=" * 60)
    print("GARMIN CONNECT TEST WITH CERTIFICATE")
    print("=" * 60)
    
    # Your credentials
    email = "wjeiv4@gmail.com"
    password = "SdfRfv1!"
    
    print(f"Email: {email}")
    print(f"Certificate: {cert_path}")
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
        print("\nTo use this in your application:")
        print("1. Set SSL_CERT_FILE environment variable")
        print("2. Or load the certificate in your code before importing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
        if "SSL" in str(e) or "certificate" in str(e).lower():
            print("\nStill getting SSL errors.")
            print("The certificate might not include all necessary root certificates.")
        
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_garmin_with_cert()
