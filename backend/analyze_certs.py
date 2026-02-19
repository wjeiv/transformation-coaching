#!/usr/bin/env python3
"""Analyze certificates in full-chain.pem."""

import subprocess
import sys

def analyze_certs():
    """Analyze the certificates in the full-chain.pem file."""
    cert_file = "/home/belliott/transformation-coaching/backend/certs/full-chain.pem"
    
    print("Analyzing certificates in full-chain.pem...")
    print("=" * 60)
    
    # Read and split certificates
    with open(cert_file, 'r') as f:
        content = f.read()
    
    # Split by BEGIN CERTIFICATE
    certs = content.split('-----BEGIN CERTIFICATE-----')
    cert_count = len(certs) - 1  # First split is empty
    print(f"Found {cert_count} certificates in the file")
    print()
    
    # Analyze each certificate
    for i, cert in enumerate(certs[1:], 1):  # Skip first empty split
        cert = '-----BEGIN CERTIFICATE-----' + cert
        cert = cert.strip()
        
        # Write temp cert file
        temp_file = f"/tmp/cert_{i}.pem"
        with open(temp_file, 'w') as f:
            f.write(cert)
        
        # Get certificate info
        try:
            result = subprocess.run(
                ['openssl', 'x509', '-in', temp_file, '-noout', '-subject', '-issuer'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                subject = lines[0] if lines else "Unknown"
                issuer = lines[1] if len(lines) > 1 else "Unknown"
                
                print(f"Certificate {i}:")
                print(f"  {subject}")
                print(f"  {issuer}")
                
                # Check for Amazon
                if "amazon" in subject.lower() or "amazon" in issuer.lower():
                    print(f"  *** AMAZON CERTIFICATE ***")
                print()
        except Exception as e:
            print(f"Error analyzing certificate {i}: {e}")
    
    # Clean up
    subprocess.run(['rm', '-f', '/tmp/cert_*.pem'])
    
    # Test if we can verify thegarth.s3.amazonaws.com with this cert
    print("=" * 60)
    print("Testing certificate against thegarth.s3.amazonaws.com...")
    
    try:
        result = subprocess.run(
            ['openssl', 's_client', '-connect', 'thegarth.s3.amazonaws.com:443', 
             '-CAfile', cert_file, '-verify_return_error'],
            input='', capture_output=True, text=True, timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Certificate chain verifies successfully!")
        else:
            print("❌ Certificate verification failed:")
            print(result.stderr[-500:])  # Last 500 chars of error
    except Exception as e:
        print(f"Error testing verification: {e}")

if __name__ == "__main__":
    analyze_certs()
