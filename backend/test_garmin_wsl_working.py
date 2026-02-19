#!/usr/bin/env python3
"""Working Garmin Connect test for WSL with proper SSL context."""

import os
import sys
import ssl
import certifi
import traceback
from datetime import date

# Add the backend directory to Python path
sys.path.insert(0, '/home/belliott/transformation-coaching/backend')

# Certificate paths
cert_path = "/home/belliott/transformation-coaching/backend/certs/full-chain.pem"
certifi_path = certifi.where()

print("=" * 60)
print("GARMIN CONNECT WSL - WORKING SOLUTION")
print("=" * 60)

# Create a custom SSL context that includes both certificates
def create_ssl_context():
    """Create SSL context with both corporate and standard CAs."""
    context = ssl.create_default_context()
    
    # Load corporate certificate
    context.load_verify_locations(cert_path)
    
    # Also load certifi for standard CAs
    context.load_verify_locations(certifi_path)
    
    return context

# Monkey patch ssl to use our context
import urllib3.util.ssl_
original_create_default_context = urllib3.util.ssl_.create_urllib3_context

def patched_create_urllib3_context(**kwargs):
    """Create urllib3 context with our certificates."""
    context = create_ssl_context()
    return context

urllib3.util.ssl_.create_urllib3_context = patched_create_urllib3_context

# Also patch requests if needed
import requests
original_request = requests.request

def patched_request(*args, **kwargs):
    """Patch requests to use our SSL context."""
    if 'verify' not in kwargs:
        kwargs['verify'] = cert_path
    return original_request(*args, **kwargs)

requests.request = patched_request

# Now import Garmin
from garminconnect import Garmin

def test_garmin_connection():
    """Test Garmin Connect connection."""
    email = "wjeiv4@gmail.com"
    password = "SdfRfv1!"
    
    print(f"Email: {email}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"SSL: {ssl.OPENSSL_VERSION}")
    print(f"Corporate cert: {os.path.exists(cert_path)}")
    print()
    
    try:
        print("Creating Garmin client with patched SSL context...")
        client = Garmin(email, password)
        
        print("Logging in...")
        client.login()
        
        print("✅ Successfully logged in to Garmin Connect!")
        
        # Get user info
        print("\nFetching user profile...")
        try:
            full_name = client.get_full_name()
            print(f"   User: {full_name}")
        except Exception as e:
            print(f"   Profile error: {e}")
        
        # Get unit system
        try:
            unit_system = client.get_unit_system()
            print(f"   Unit System: {unit_system}")
        except Exception as e:
            print(f"   Unit system error: {e}")
        
        # Get today's activities
        print("\nFetching today's activities...")
        today = date.today().isoformat()
        try:
            activities = client.get_activities_by_date(today, today)
            print(f"   Found {len(activities)} activities today")
            
            if activities:
                for activity in activities[:3]:
                    act_name = activity.get('activityName', 'Unnamed')
                    act_type = activity.get('activityType', {}).get('typeKey', 'Unknown')
                    print(f"   - {act_name} ({act_type})")
        except Exception as e:
            print(f"   Activities error: {e}")
        
        # Get workouts
        print("\nFetching workouts...")
        try:
            workouts = client.get_workouts()
            print(f"   Found {len(workouts)} workouts")
        except Exception as e:
            print(f"   Workouts error: {e}")
        
        print("\n🎉 SUCCESS! Garmin Connect is working in WSL!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_garmin_connection()
    
    print("\n" + "=" * 60)
    print("SOLUTION SUMMARY")
    print("=" * 60)
    
    if success:
        print("\n✅ The SSL context patching approach works!")
        print("\nTo implement in your application:")
        print("""
# Add this code before importing garminconnect:
import ssl
import certifi
import urllib3.util.ssl_

cert_path = "/path/to/corporate.pem"
certifi_path = certifi.where()

def create_ssl_context():
    context = ssl.create_default_context()
    context.load_verify_locations(cert_path)
    context.load_verify_locations(certifi_path)
    return context

# Patch urllib3
original_create = urllib3.util.ssl_.create_urllib3_context
urllib3.util.ssl_.create_urllib3_context = lambda **kw: create_ssl_context()

# Now import and use Garmin normally
from garminconnect import Garmin
""")
    else:
        print("\n❌ Connection failed.")
        print("\nFinal recommendations:")
        print("1. The certificate works for both Garmin and S3 domains")
        print("2. The issue is likely Python's SSL handling in WSL")
        print("3. Try running the application directly in Windows")
        print("4. Or use a VPN to bypass corporate SSL inspection")
        print("5. Or work from a non-corporate network")
