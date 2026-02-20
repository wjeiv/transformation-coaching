#!/usr/bin/env python3
"""
Test production mobile authentication
"""
import requests
import json

def test_production_mobile_auth():
    """Test mobile authentication on production domain"""
    
    # Test data
    login_data = {
        "email": "admin@transformationcoaching.com",
        "password": "FFester1!"
    }
    
    # Mobile user agents
    mobile_user_agents = {
        "android_chrome": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
        "iphone_chrome": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/91.0.4472.80 Mobile/15E148 Safari/604.1"
    }
    
    base_url = "https://transformationcoaching262.com/api/v1"
    
    print("Testing Production Mobile Authentication...")
    print(f"Base URL: {base_url}")
    
    for device, user_agent in mobile_user_agents.items():
        print(f"\nTesting {device}...")
        
        headers = {
            "Content-Type": "application/json",
            "Origin": "https://transformationcoaching262.com",
            "User-Agent": user_agent
        }
        
        try:
            # Test CORS preflight
            print("  Testing CORS preflight...")
            cors_response = requests.options(
                f"{base_url}/auth/login",
                headers={
                    "Origin": "https://transformationcoaching262.com",
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "Content-Type, Authorization",
                    "User-Agent": user_agent
                }
            )
            print(f"    CORS Status: {cors_response.status_code}")
            
            # Test login
            print("  Testing login...")
            login_response = requests.post(
                f"{base_url}/auth/login",
                headers=headers,
                json=login_data,
                timeout=30
            )
            
            print(f"    Login Status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                print("    Login successful!")
                print(f"    Token received: {'access_token' in token_data}")
                
                # Test protected endpoint
                if 'access_token' in token_data:
                    print("  Testing protected endpoint...")
                    auth_headers = headers.copy()
                    auth_headers["Authorization"] = f"Bearer {token_data['access_token']}"
                    
                    me_response = requests.get(
                        f"{base_url}/auth/me",
                        headers=auth_headers,
                        timeout=30
                    )
                    print(f"    Auth Status: {me_response.status_code}")
                    if me_response.status_code == 200:
                        print("    Protected endpoint accessible!")
                    else:
                        print(f"    Protected endpoint failed: {me_response.text}")
            else:
                print(f"    Login failed: {login_response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"    Request failed: {e}")
    
    print("\n" + "="*80)
    print("PRODUCTION MOBILE AUTHENTICATION TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_production_mobile_auth()
