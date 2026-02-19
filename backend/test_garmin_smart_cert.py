#!/usr/bin/env python3
"""Smart certificate handling for Garmin Connect in WSL."""

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
print("SMART CERTIFICATE HANDLING FOR GARMIN CONNECT")
print("=" * 60)

# Monkey patch requests to use different certificates based on domain
import requests.adapters
import urllib3.contrib.pyopenssl

# Create custom HTTPAdapter
class SmartCertAdapter(requests.adapters.HTTPAdapter):
    def __init__(self, corporate_cert=None, standard_cert=None, **kwargs):
        self.corporate_cert = corporate_cert
        self.standard_cert = standard_cert
        super().__init__(**kwargs)
    
    def init_poolmanager(self, *args, **kwargs):
        # Use default SSL context for pool manager
        kwargs['assert_hostname'] = True
        kwargs['cert_reqs'] = 'CERT_REQUIRED'
        return super().init_poolmanager(*args, **kwargs)
    
    def send(self, request, **kwargs):
        # Determine which certificate to use based on the domain
        parsed = urlparse(request.url)
        domain = parsed.netloc.lower()
        
        if 'garmin.com' in domain or 'connect.garmin.com' in domain:
            # Use corporate certificate for Garmin domains
            kwargs['verify'] = self.corporate_cert
        elif 'amazonaws.com' in domain or 's3.amazonaws.com' in domain:
            # Use standard certificates for AWS/S3
            kwargs['verify'] = self.standard_cert
        else:
            # Default to corporate certificate
            kwargs['verify'] = self.corporate_cert
        
        return super().send(request, **kwargs)

# Patch the Garmin session to use our smart adapter
def patch_garmin_session():
    """Patch Garmin to use smart certificate handling."""
    import garminconnect
    
    # Store original init
    original_init = garminconnect.Garmin.__init__
    
    def patched_init(self, email, password, **kwargs):
        # Call original init
        original_init(self, email, password, **kwargs)
        
        # Replace the session adapter with our smart one
        adapter = SmartCertAdapter(
            corporate_cert=cert_path,
            standard_cert=certifi_path
        )
        
        # Mount for both http and https
        self.garth.client.sess.mount('http://', adapter)
        self.garth.client.sess.mount('https://', adapter)
    
    # Apply patch
    garminconnect.Garmin.__init__ = patched_init

# Apply the patch before creating Garmin client
patch_garmin_session()

# Now import and use Garmin
from garminconnect import Garmin

def test_garmin_smart():
    """Test Garmin with smart certificate handling."""
    email = "wjeiv4@gmail.com"
    password = "SdfRfv1!"
    
    print(f"Email: {email}")
    print(f"Python: {sys.version}")
    print(f"SSL version: {ssl.OPENSSL_VERSION}")
    print(f"Corporate cert: {cert_path}")
    print(f"Certifi path: {certifi_path}")
    print()
    
    try:
        print("Creating Garmin client with smart certificate handling...")
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
        
        print("\n🎉 Garmin Connect is working successfully with smart certificates!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_garmin_smart()
    
    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    
    if success:
        print("✅ SUCCESS! The smart certificate approach works.")
        print("\nTo integrate this into your main application:")
        print("1. Import the SmartCertAdapter from this file")
        print("2. Apply the patch before creating Garmin clients")
        print("3. The adapter will automatically use the right certificate")
    else:
        print("❌ Still having issues. Try these alternatives:")
        print("\n1. Use a VPN to bypass corporate SSL inspection")
        print("2. Work from a non-corporate network")
        print("3. Run the application directly in Windows instead of WSL")
        print("4. Ask IT for a certificate that includes Amazon root CAs")
