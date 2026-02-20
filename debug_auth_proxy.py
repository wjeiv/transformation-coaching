#!/usr/bin/env python3
"""
Authentication diagnostic script to test login endpoints
and identify issues between local and production access.
"""
import asyncio
import httpx
import json
from datetime import datetime

# Test configurations
LOCAL_BASE = "http://localhost:8000"
PROD_BASES = [
    "https://transformationcoaching262.com",
    "https://transformationcoaching.wjeiv.com"
]

async def test_auth_endpoint(base_url, endpoint_name, path):
    """Test authentication endpoint and return response details."""
    print(f"\n=== Testing {endpoint_name} at {base_url}{path} ===")
    
    async with httpx.AsyncClient() as client:
        try:
            # Test health check first
            health_resp = await client.get(f"{base_url}/health", timeout=10)
            print(f"Health Check: {health_resp.status_code} - {health_resp.json()}")
            
            # Test CORS preflight
            print(f"\n--- CORS Preflight Test ---")
            preflight_resp = await client.options(
                f"{base_url}{path}",
                headers={
                    "Origin": base_url,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type"
                },
                timeout=10
            )
            print(f"CORS Preflight: {preflight_resp.status_code}")
            print(f"CORS Headers: {dict(preflight_resp.headers)}")
            
            # Test actual login request
            print(f"\n--- Login Request Test ---")
            login_data = {
                "email": "admin",
                "password": "FFester1!"
            }
            
            login_resp = await client.post(
                f"{base_url}{path}",
                json=login_data,
                headers={
                    "Origin": base_url,
                    "Content-Type": "application/json"
                },
                timeout=10
            )
            
            print(f"Login Status: {login_resp.status_code}")
            print(f"Login Headers: {dict(login_resp.headers)}")
            
            if login_resp.status_code == 200:
                print(f"Login Success: {login_resp.json()}")
            else:
                print(f"Login Error: {login_resp.text}")
                
            return {
                "status_code": login_resp.status_code,
                "headers": dict(login_resp.headers),
                "response": login_resp.text if login_resp.status_code != 200 else login_resp.json(),
                "cors_headers": dict(preflight_resp.headers)
            }
            
        except httpx.TimeoutException:
            print(f"TIMEOUT: Could not connect to {base_url}")
            return {"error": "timeout"}
        except httpx.ConnectError:
            print(f"CONNECTION ERROR: Could not connect to {base_url}")
            return {"error": "connection_error"}
        except Exception as e:
            print(f"ERROR: {e}")
            return {"error": str(e)}

async def main():
    """Run diagnostic tests."""
    print("🔍 Authentication Diagnostic Tool")
    print("=" * 50)
    print(f"Started at: {datetime.now()}")
    
    # Test local
    local_result = await test_auth_endpoint(
        LOCAL_BASE, 
        "Local Backend", 
        "/api/v1/auth/login"
    )
    
    # Test production domains
    for prod_base in PROD_BASES:
        prod_result = await test_auth_endpoint(
            prod_base, 
            f"Production Backend ({prod_base})", 
            "/api/v1/auth/login"
        )
    
    print(f"\n📊 Summary at {datetime.now()}")
    print("=" * 50)
    
    if "error" not in local_result:
        print(f"✅ Local: {local_result['status_code']}")
        if local_result["status_code"] == 200:
            print("   - Login successful locally")
        else:
            print(f"   - Login failed: {local_result['response']}")
    else:
        print(f"❌ Local: {local_result['error']}")
    
    print(f"\n🔧 Recommendations:")
    print("1. Check CORS origins in backend/app/core/config.py")
    print("2. Verify nginx proxy headers")
    print("3. Check Cloudflare SSL/TLS settings")
    print("4. Review Cloudflare firewall rules")

if __name__ == "__main__":
    asyncio.run(main())
