import requests

# Test admin login with production domain origin
headers = {
    "Origin": "https://transformationcoaching262.com",
    "Content-Type": "application/json"
}

# Try admin login
data = {
    "email": "admin@transformationcoaching.com",
    "password": "FFester1!"
}

response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    headers=headers,
    json=data
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

# Also test if user exists by checking auth/me with a working token
if response.status_code == 200:
    token = response.json().get("access_token")
    auth_headers = {
        "Authorization": f"Bearer {token}",
        "Origin": "https://transformationcoaching262.com"
    }
    
    me_response = requests.get(
        "http://localhost:8000/api/v1/auth/me",
        headers=auth_headers
    )
    print(f"\nUser Info: {me_response.text}")
