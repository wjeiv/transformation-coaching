#!/usr/bin/env python3
"""Final Garmin Connect test for WSL with proper certificate handling."""

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
print("GARMIN CONNECT WSL - FINAL TEST")
print("=" * 60)

# Set environment for AWS domains
os.environ['AWS_CA_BUNDLE'] = certifi_path

# Create a custom session class
import requests
from requests.adapters import HTTPAdapter

class SmartCertSession(requests.Session):
    def __init__(self):
        super().__init__()
        adapter = SmartCertAdapter()
        self.mount('https://', adapter)
        self.mount('http://', adapter)

class SmartCertAdapter(HTTPAdapter):
    def send(self, request, **kwargs):
        parsed = urlparse(request.url)
        domain = parsed.netloc.lower()
        
        if 'amazonaws.com' in domain:
            kwargs['verify'] = certifi_path
        else:
            kwargs['verify'] = cert_path
        
        return super().send(request, **kwargs)

# Patch garth to use our session
import garth

# Store original session
OriginalGarthSession = garth.http.Session

def create_smart_session():
    return SmartCertSession()

# Replace garth's session with ours
garth.http.Session = create_smart_session

# Now import Garmin
from garminconnect import Garmin

def test_garmin_wsl():
    """Test Garmin Connect in WSL environment."""
    email = "wjeiv4@gmail.com"
    password = "SdfRfv1!"
    
    print(f"Email: {email}")
    print(f"Python: {sys.version.split()[0]}")
    print(f"SSL: {ssl.OPENSSL_VERSION}")
    print(f"Corporate cert: {os.path.exists(cert_path)}")
    print()
    
    try:
        print("Initializing Garmin client...")
        client = Garmin(email, password)
        
        print("Logging in...")
        client.login()
        
        print("✅ Successfully logged in!")
        
        # Get user info
        print("\nFetching profile...")
        try:
            full_name = client.get_full_name()
            print(f"   User: {full_name}")
        except:
            print("   Profile fetch failed (expected in some corp networks)")
        
        # Get activities
        print("\nFetching activities...")
        today = date.today().isoformat()
        activities = client.get_activities_by_date(today, today)
        print(f"   Activities today: {len(activities)}")
        
        # Get stats for last week
        from datetime import timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=7)
        
        stats = client.get_stats(start_date.isoformat(), end_date.isoformat())
        if stats:
            print(f"   Stats available for {len(stats)} days")
        
        print("\n🎉 SUCCESS! Garmin Connect works in WSL!")
        print("\nKey achievements:")
        print("✅ Corporate certificate for Garmin domains")
        print("✅ Standard CAs for Amazon S3 domains")
        print("✅ Automatic domain-based certificate selection")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
        error_str = str(e).lower()
        if 's3' in error_str or 'amazon' in error_str:
            print("\nThis is an S3 certificate issue.")
        elif 'ssl' in error_str or 'certificate' in error_str:
            print("\nThis is an SSL certificate issue.")
        
        print("\nDebugging info:")
        traceback.print_exc()
        
        return False

if __name__ == "__main__":
    success = test_garmin_wsl()
    
    print("\n" + "=" * 60)
    print("IMPLEMENTATION GUIDE")
    print("=" * 60)
    
    if success:
        print("\nTo integrate this into your application:")
        print("\n1. Add this code before importing garminconnect:")
        print("""
import os
import requests
from urllib.parse import urlparse
import certifi

# Smart certificate handling
cert_path = "/path/to/your/corporate.pem"
certifi_path = certifi.where()

class SmartCertAdapter(requests.adapters.HTTPAdapter):
    def send(self, request, **kwargs):
        if 'amazonaws.com' in urlparse(request.url).netloc:
            kwargs['verify'] = certifi_path
        else:
            kwargs['verify'] = cert_path
        return super().send(request, **kwargs)

# Apply to requests session
class SmartSession(requests.Session):
    def __init__(self):
        super().__init__()
        self.mount('https://', SmartCertAdapter())

# Patch garth
import garth
garth.http.Session = SmartSession
""")
        print("\n2. Then import and use Garmin normally")
    else:
        print("\nAlternative solutions:")
        print("1. Convert certificate line endings: dos2unix cert.pem")
        print("2. Try from Windows PowerShell instead of WSL")
        print("3. Use VPN to bypass corporate SSL inspection")
        print("4. Work from non-corporate network")
