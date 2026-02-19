#!/usr/bin/env python3
"""Diagnose certificate chain issues."""

import ssl
import socket
import certifi
from OpenSSL import crypto

cert_path = "/home/belliott/transformation-coaching/backend/certs/full-chain.pem"
certifi_path = certifi.where()

print("=" * 60)
print("CERTIFICATE DIAGNOSTIC")
print("=" * 60)

def load_cert_chain(path):
    """Load certificate chain from file."""
    with open(path, 'r') as f:
        cert_data = f.read()
    
    certs = []
    cert_strs = cert_data.split('-----END CERTIFICATE-----')
    
    for cert_str in cert_strs:
        cert_str = cert_str.strip()
        if cert_str and '-----BEGIN CERTIFICATE-----' in cert_str:
            cert_str += '-----END CERTIFICATE-----'
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, cert_str)
            certs.append(cert)
    
    return certs

def verify_cert_chain(hostname, port, ca_cert_path):
    """Verify certificate chain for a host."""
    print(f"\nVerifying {hostname}:{port}...")
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        context.load_verify_locations(ca_cert_path)
        
        # Connect and verify
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                print(f"✅ Verification successful")
                print(f"   Subject: {dict(x[0] for x in cert['subject'])}")
                print(f"   Issuer: {dict(x[0] for x in cert['issuer'])}")
                return True
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

# Load and analyze corporate certificate
print("\nAnalyzing corporate certificate chain...")
try:
    certs = load_cert_chain(cert_path)
    print(f"Found {len(certs)} certificates in chain")
    
    for i, cert in enumerate(certs):
        subject = cert.get_subject()
        issuer = cert.get_issuer()
        print(f"\nCert {i+1}:")
        print(f"   Subject: {subject.CN}")
        print(f"   Issuer: {issuer.CN}")
        print(f"   Valid: {cert.get_notBefore()} to {cert.get_notAfter()}")
        
except Exception as e:
    print(f"Error loading corporate cert: {e}")

# Test verification for different domains
print("\n" + "=" * 60)
print("TESTING DOMAIN VERIFICATION")
print("=" * 60)

# Test Garmin domain with corporate cert
verify_cert_chain('sso.garmin.com', 443, cert_path)

# Test S3 domain with corporate cert
verify_cert_chain('thegarth.s3.amazonaws.com', 443, cert_path)

# Test S3 domain with certifi
verify_cert_chain('thegarth.s3.amazonaws.com', 443, certifi_path)

# Check what certificates are actually being presented
print("\n" + "=" * 60)
print("CHECKING SERVER CERTIFICATES")
print("=" * 60)

def get_server_cert(hostname, port):
    """Get certificate presented by server."""
    try:
        with socket.create_connection((hostname, port)) as sock:
            with ssl.wrap_socket(sock) as ssock:
                cert_der = ssock.getpeercert(binary_form=True)
                cert = crypto.load_certificate(crypto.FILETYPE_ASN1, cert_der)
                
                print(f"\n{hostname} presents:")
                print(f"   Subject: {cert.get_subject().CN}")
                print(f"   Issuer: {cert.get_issuer().CN}")
                
                # Check if issuer is in our chain
                issuer_name = cert.get_issuer().CN
                print(f"   Issuer in corporate chain: {any(c.get_subject().CN == issuer_name for c in certs)}")
                
    except Exception as e:
        print(f"Error getting cert from {hostname}: {e}")

get_server_cert('sso.garmin.com', 443)
get_server_cert('thegarth.s3.amazonaws.com', 443)

print("\n" + "=" * 60)
print("RECOMMENDATIONS")
print("=" * 60)
print("""
1. If corporate cert works for Garmin but not S3:
   - The corporate SSL inspection only intercepts certain domains
   - S3 traffic might bypass inspection, causing a mismatch

2. Solutions:
   a) Use VPN to route all traffic through corporate network
   b) Get certificate that includes Amazon root CAs
   c) Disable SSL inspection for this application
   d) Work from non-corporate network

3. WSL-specific:
   - WSL uses Windows networking stack
   - Certificate handling might differ from native Linux
   - Consider running directly in Windows
""")
