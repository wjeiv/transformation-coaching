import requests

# Test login with production domain origin
headers = {
    "Origin": "https://transformationcoaching262.com",
    "Content-Type": "application/json"
}

# Try with the default coach account
data = {
    "email": "wjeiv4@gmail.com",
    "password": "FFester1!"
}

response = requests.post(
    "http://localhost:8000/api/v1/auth/login",
    headers=headers,
    json=data
)

print(f"Status Code: {response.status_code}")
print(f"Headers: {dict(response.headers)}")
print(f"Response: {response.text}")
