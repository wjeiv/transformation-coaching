#!/usr/bin/env python3
"""Domain-specific certificate handling for Garmin Connect."""

import os
import sys
import ssl
import certifi
import traceback
from datetime import date
from urllib.parse import urlparse

# Add the backend directory to Python path
sys.path.insert(0, '/home/belliott/transformation-coaching/backend')

# Certificate paths
cert_path = "/home/belliott/transformation-coaching/backend/certs/full-chain.pem"
certifi_path = certifi.where()

print("=" * 60)
print("DOMAIN-SPECIFIC CERTIFICATE HANDLING")
print("=" * 60)

# Create a custom requests session that handles certificates per domain
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

class DomainCertAdapter(HTTPAdapter):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def init_poolmanager(self, *args, **kwargs):
        # Remove verify from poolmanager kwargs as we'll handle it per request
        kwargs.pop('assert_hostname', None)
        return super().init_poolmanager(*args, **kwargs)
    
    def send(self, request, **kwargs):
        parsed = urlparse(request.url)
        domain = parsed.netloc.lower()
        
        # Choose certificate based on domain
        if 'amazonaws.com' in domain or 's3.amazonaws.com' in domain:
            kwargs['verify'] = certifi_path
            print(f"🔒 Using certifi for {domain}")
        else:
            kwargs['verify'] = cert_path
            print(f"🔒 Using corporate cert for {domain}")
        
        return super().send(request, **kwargs)

# Patch garth to use our custom session
def patch_garth():
    """Patch garth to use domain-specific certificates."""
    import garth
    
    # Store original Client class
    original_client = garth.Client
    
    class PatchedClient(original_client):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            # Mount our custom adapter
            adapter = DomainCertAdapter()
            self.sess.mount('https://', adapter)
            self.sess.mount('http://', adapter)
    
    # Replace the Client class
    garth.Client = PatchedClient

# Apply patch
patch_garth()

# Now import Garmin
from garminconnect import Garmin

def test_garmin_domain():
    """Test Garmin with domain-specific certificates."""
    email = "wjeiv4@gmail.com"
    password = "SdfRfv1!"
    
    print(f"Email: {email}")
    print(f"Python: {sys.version}")
    print(f"SSL version: {ssl.OPENSSL_VERSION}")
    print()
    
    try:
        print("Creating Garmin client with domain-specific certificates...")
        client = Garmin(email, password)
        
        print("\nAttempting login...")
        client.login()
        
        print("\n✅ SUCCESS: Logged in to Garmin Connect!")
        
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
        
        print("\n🎉 Garmin Connect is working with domain-specific certificates!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_garmin_domain()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ SUCCESS! Domain-specific certificates work.")
        print("\nThis solution:")
        print("- Uses corporate certificate for Garmin domains")
        print("- Uses standard CAs for Amazon S3 domains")
        print("- Automatically switches based on the URL")
    else:
        print("❌ Still having issues.")
        print("\nAlternative solutions:")
        print("1. Try from a non-corporate network")
        print("2. Use a VPN to bypass SSL inspection")
        print("3. Run directly in Windows instead of WSL")
