#!/usr/bin/env python3
"""Test with the certificate using a different approach."""

import os
import sys
import ssl

# Add the backend directory to Python path
sys.path.insert(0, '/home/belliott/transformation-coaching/backend')

# Load the certificate
cert_path = "/home/belliott/transformation-coaching/backend/certs/full-chain.pem"

# Set environment variables FIRST
os.environ['SSL_CERT_FILE'] = cert_path
os.environ['REQUESTS_CA_BUNDLE'] = cert_path
os.environ['CURL_CA_BUNDLE'] = cert_path

# Patch ssl.create_default_context to always use our cert
original_create_default = ssl.create_default_context

def patched_create_default_context(*args, **kwargs):
    context = original_create_default(*args, **kwargs)
    context.load_verify_locations(cert_path)
    return context

ssl.create_default_context = patched_create_default_context

# Also set the default https context
ssl._create_default_https_context = patched_create_default_context

print(f"Using certificate: {cert_path}")
print(f"SSL_CERT_FILE: {os.environ.get('SSL_CERT_FILE')}")
print()

# Now test
from garminconnect import Garmin

def test_with_patched_ssl():
    """Test with patched SSL context."""
    print("=" * 60)
    print("GARMIN CONNECT TEST - PATCHED SSL CONTEXT")
    print("=" * 60)
    
    email = "wjeiv4@gmail.com"
    password = "SdfRfv1!"
    
    try:
        print("Creating Garmin client...")
        client = Garmin(email, password)
        
        print("Attempting login...")
        client.login()
        
        print("✅ SUCCESS: Logged in to Garmin Connect!")
        
        # Get user info
        full_name = client.get_full_name()
        print(f"   User: {full_name}")
        
        # Get workouts
        workouts = client.get_workouts()
        print(f"   Found {len(workouts)} workouts")
        
        print("\n🎉 Garmin Connect is working!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_with_patched_ssl()
