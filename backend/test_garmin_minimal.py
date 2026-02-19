#!/usr/bin/env python3
"""Minimal Garmin Connect test with domain-specific certificates."""

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
print("MINIMAL GARMIN TEST WITH DOMAIN CERTIFICATES")
print("=" * 60)

# Set up domain-specific certificate handling
import requests
from requests.adapters import HTTPAdapter

class DomainCertAdapter(HTTPAdapter):
    def send(self, request, **kwargs):
        parsed = urlparse(request.url)
        domain = parsed.netloc.lower()
        
        if 'amazonaws.com' in domain:
            kwargs['verify'] = certifi_path
        else:
            kwargs['verify'] = cert_path
        
        return super().send(request, **kwargs)

# Monkey patch requests before importing garminconnect
original_session = requests.Session

def patched_session_init(self, *args, **kwargs):
    original_session.__init__(self, *args, **kwargs)
    adapter = DomainCertAdapter()
    self.mount('https://', adapter)
    self.mount('http://', adapter)

requests.Session.__init__ = patched_session_init

# Now import Garmin
from garminconnect import Garmin

def test_minimal_garmin():
    """Test minimal Garmin connection."""
    email = "wjeiv4@gmail.com"
    password = "SdfRfv1!"
    
    print(f"Email: {email}")
    print(f"Using corporate cert for Garmin domains")
    print(f"Using certifi for AWS domains")
    print()
    
    try:
        print("Creating Garmin client...")
        client = Garmin(email, password)
        
        print("Logging in...")
        client.login()
        
        print("✅ Login successful!")
        
        # Try to get basic data without profile
        print("\nTesting basic API calls...")
        
        # Get activities
        today = date.today().isoformat()
        activities = client.get_activities_by_date(today, today)
        print(f"✅ Got activities: {len(activities)} for today")
        
        # Get stats
        from datetime import timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        stats = client.get_stats(start_date.isoformat(), end_date.isoformat())
        if stats:
            print(f"✅ Got stats for last 7 days")
            print(f"   Days with data: {len(stats)}")
        
        # Get heart rate
        hr_data = client.get_heart_rates(today, today)
        if hr_data:
            print(f"✅ Got heart rate data for today")
        
        print("\n🎉 Garmin Connect is working in WSL!")
        print("\nThe domain-specific certificate approach successfully:")
        print("- Uses corporate certificate for Garmin domains")
        print("- Uses standard CAs for Amazon S3 domains")
        print("- Works within the corporate network")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
        # Check specific errors
        error_str = str(e)
        if "profile" in error_str.lower():
            print("\nNote: Profile fetch failed, but login might have succeeded.")
            print("This is a known issue in some corporate environments.")
        
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_minimal_garmin()
    
    print("\n" + "=" * 60)
    print("CONCLUSION")
    print("=" * 60)
    
    if success:
        print("✅ SUCCESS! Garmin Connect works in WSL with domain-specific certificates.")
        print("\nTo use in your main application:")
        print("1. Apply the DomainCertAdapter patch before importing garminconnect")
        print("2. The adapter will automatically handle certificates per domain")
        print("3. No need for VPN or leaving corporate network")
    else:
        print("\nIf still having issues, consider:")
        print("1. The certificate might need Windows line ending conversion:")
        print(f"   dos2unix {cert_path}")
        print("\n2. Try running directly in Windows instead of WSL")
        print("3. Use a VPN to bypass corporate SSL inspection")
