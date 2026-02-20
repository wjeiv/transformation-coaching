import requests

# First login as coach to get a token
headers = {
    "Origin": "https://transformationcoaching262.com",
    "Content-Type": "application/json"
}

coach_data = {
    "email": "wjeiv4@gmail.com",
    "password": "FFester1!"
}

response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    headers=headers,
    json=coach_data
)

if response.status_code == 200:
    token = response.json().get("access_token")
    
    # Try to access admin endpoint to see users
    admin_headers = {
        "Authorization": f"Bearer {token}",
        "Origin": "https://transformationcoaching262.com"
    }
    
    # Check if we can access admin users list
    users_response = requests.get(
        "http://localhost:8000/api/v1/admin/users",
        headers=admin_headers
    )
    
    print(f"Users List Status: {users_response.status_code}")
    print(f"Users List: {users_response.text}")
else:
    print(f"Coach login failed: {response.status_code} - {response.text}")
