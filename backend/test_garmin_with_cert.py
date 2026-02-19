#!/usr/bin/env python3
"""Test Garmin Connect with certificate chain in WSL."""

import os
import sys
import ssl
import certifi
import traceback
from datetime import date

# Add the backend directory to Python path
sys.path.insert(0, '/home/belliott/transformation-coaching/backend')

from garminconnect import Garmin

def test_with_certificate():
    """Test Garmin Connect with explicit certificate chain."""
    print("=" * 60)
    print("GARMIN CONNECT TEST WITH CERTIFICATE (WSL)")
    print("=" * 60)
    
    # Your credentials
    email = "wjeiv4@gmail.com"
    password = "SdfRfv1!"
    
    print(f"Email: {email}")
    print(f"Python: {sys.version}")
    print(f"SSL version: {ssl.OPENSSL_VERSION}")
    print()
    
    # Path to certificates
    cert_path = "/home/belliott/transformation-coaching/backend/certs/full-chain.pem"
    certifi_path = certifi.where()
    
    print(f"Corporate cert: {cert_path}")
    print(f"Certifi path: {certifi_path}")
    print(f"Corporate cert exists: {os.path.exists(cert_path)}")
    print()
    
    # Create SSL context with both certificates
    try:
        print("Creating SSL context with certificates...")
        context = ssl.create_default_context()
        
        # Load corporate certificate
        context.load_verify_locations(cert_path)
        print("✅ Loaded corporate certificate")
        
        # Also load certifi for standard CAs (including Amazon)
        context.load_verify_locations(certifi_path)
        print("✅ Loaded certifi CA bundle")
        
        # Set up environment for requests
        os.environ['REQUESTS_CA_BUNDLE'] = cert_path
        os.environ['CURL_CA_BUNDLE'] = cert_path
        print("✅ Set environment variables")
        
    except Exception as e:
        print(f"❌ Error setting up SSL context: {e}")
        traceback.print_exc()
        return False
    
    try:
        print("\nAttempting Garmin login...")
        
        # Try with custom session
        import requests
        session = requests.Session()
        session.verify = cert_path  # Use corporate cert
        
        client = Garmin(email, password, session=session)
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
        print(f"❌ Error during login: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        
        # Check if it's the S3 certificate issue
        if "thegarth.s3.amazonaws.com" in str(e) or "S3" in str(e):
            print("\n🔍 This appears to be the Amazon S3 certificate issue.")
            print("The corporate certificate works for Garmin but not for Amazon S3.")
            print("\nSuggestions:")
            print("1. Try from a non-corporate network (home/mobile)")
            print("2. Use a VPN that bypasses corporate SSL inspection")
            print("3. Ask IT for a certificate chain that includes Amazon root CAs")
        
        return False

def test_combined_cert():
    """Test with combined certificate file."""
    print("\n" + "=" * 60)
    print("TESTING WITH COMBINED CERTIFICATE")
    print("=" * 60)
    
    # Create combined certificate file
    cert_path = "/home/belliott/transformation-coaching/backend/certs/full-chain.pem"
    certifi_path = certifi.where()
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
        
        # Test with combined certificate
        os.environ['REQUESTS_CA_BUNDLE'] = combined_path
        os.environ['SSL_CERT_FILE'] = combined_path
        
        email = "wjeiv4@gmail.com"
        password = "SdfRfv1!"
        
        print("\nTesting with combined certificate...")
        client = Garmin(email, password)
        client.login()
        
        print("✅ SUCCESS with combined certificate!")
        return True
        
    except Exception as e:
        print(f"❌ Combined certificate failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Garmin Connect in WSL environment...\n")
    
    # Test 1: With certificate setup
    success1 = test_with_certificate()
    
    # Test 2: With combined certificate
    success2 = test_combined_cert()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Test 1 (Corporate + Certifi): {'✅ PASSED' if success1 else '❌ FAILED'}")
    print(f"Test 2 (Combined Cert): {'✅ PASSED' if success2 else '❌ FAILED'}")
    
    if not success1 and not success2:
        print("\n🔧 Troubleshooting suggestions:")
        print("1. Check if WSL can access the certificate file:")
        print(f"   ls -la {cert_path}")
        print("\n2. Try converting certificate line endings:")
        print("   dos2unix /home/belliott/transformation-coaching/backend/certs/full-chain.pem")
        print("\n3. Check WSL network connectivity:")
        print("   ping connect.garmin.com")
        print("   ping thegarth.s3.amazonaws.com")
        print("\n4. The issue might be WSL-specific SSL handling.")
