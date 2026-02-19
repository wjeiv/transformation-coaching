#!/usr/bin/env python3
"""Test Garmin Connect in WSL with certificate configuration."""

import os
import sys
import ssl
import certifi
import traceback
from datetime import date

# Add the backend directory to Python path
sys.path.insert(0, '/home/belliott/transformation-coaching/backend')

# Set up certificates BEFORE importing garminconnect
cert_path = "/home/belliott/transformation-coaching/backend/certs/full-chain.pem"
certifi_path = certifi.where()

print("=" * 60)
print("GARMIN CONNECT TEST IN WSL")
print("=" * 60)

# Create combined certificate
combined_path = "/home/belliott/transformation-coaching/backend/certs/combined.pem"
try:
    print("Creating combined certificate file...")
    with open(cert_path, 'r') as f1:
        corporate_cert = f1.read()
    
    with open(certifi_path, 'r') as f2:
        certifi_cert = f2.read()
    
    with open(combined_path, 'w') as f_out:
        f_out.write(corporate_cert)
        f_out.write("\n")
        f_out.write(certifi_cert)
    
    print(f"✅ Created combined certificate: {combined_path}")
except Exception as e:
    print(f"❌ Error creating combined cert: {e}")
    combined_path = None

# Set environment variables
os.environ['REQUESTS_CA_BUNDLE'] = combined_path if combined_path else cert_path
os.environ['CURL_CA_BUNDLE'] = combined_path if combined_path else cert_path
os.environ['SSL_CERT_FILE'] = combined_path if combined_path else cert_path

print(f"Using certificate: {combined_path if combined_path else cert_path}")
print()

# Now import garminconnect
from garminconnect import Garmin

def test_garmin_connection():
    """Test Garmin Connect connection."""
    email = "wjeiv4@gmail.com"
    password = "SdfRfv1!"
    
    print(f"Email: {email}")
    print(f"Python: {sys.version}")
    print(f"SSL version: {ssl.OPENSSL_VERSION}")
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
        
        error_str = str(e)
        if "thegarth.s3.amazonaws.com" in error_str or "S3" in error_str:
            print("\n🔍 This is the Amazon S3 certificate issue.")
            print("The corporate certificate works for Garmin but not for Amazon S3.")
        elif "SSL" in error_str or "certificate" in error_str.lower():
            print("\n🔍 This is an SSL certificate issue.")
        
        print("\nFull error details:")
        traceback.print_exc()
        
        return False

def test_direct_requests():
    """Test direct HTTPS requests to diagnose the issue."""
    print("\n" + "=" * 60)
    print("TESTING DIRECT HTTPS REQUESTS")
    print("=" * 60)
    
    import requests
    
    # Test Garmin domain
    print("Testing Garmin domain...")
    try:
        response = requests.get('https://connect.garmin.com', verify=combined_path if combined_path else cert_path)
        print(f"✅ Garmin: {response.status_code}")
    except Exception as e:
        print(f"❌ Garmin: {e}")
    
    # Test S3 domain
    print("\nTesting Amazon S3 domain...")
    try:
        response = requests.get('https://thegarth.s3.amazonaws.com', verify=combined_path if combined_path else cert_path)
        print(f"✅ S3: {response.status_code}")
    except Exception as e:
        print(f"❌ S3: {e}")
    
    # Test with certifi only
    print("\nTesting S3 with certifi only...")
    try:
        response = requests.get('https://thegarth.s3.amazonaws.com', verify=certifi_path)
        print(f"✅ S3 with certifi: {response.status_code}")
    except Exception as e:
        print(f"❌ S3 with certifi: {e}")

if __name__ == "__main__":
    # Test the connection
    success = test_garmin_connection()
    
    # Test direct requests
    test_direct_requests()
    
    print("\n" + "=" * 60)
    print("WSL SPECIFIC TROUBLESHOOTING")
    print("=" * 60)
    
    if not success:
        print("\nWSL-specific issues to check:")
        print("1. Convert Windows line endings in certificate:")
        print(f"   dos2unix {cert_path}")
        print("\n2. Check certificate permissions:")
        print(f"   ls -la {cert_path}")
        print("\n3. Test network connectivity:")
        print("   ping connect.garmin.com")
        print("   ping thegarth.s3.amazonaws.com")
        print("\n4. The issue might be that WSL is using Windows networking stack")
        print("   which has different certificate handling.")
        print("\n5. Try running from Windows PowerShell instead of WSL.")
