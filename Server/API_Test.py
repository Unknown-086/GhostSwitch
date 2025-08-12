# Create test_complete.py
import requests

BASE_URL = "http://51.112.111.180:5000/api"

# Test health
response = requests.get(f"{BASE_URL}/health")
print("Health:", response.json())

# Test registration
response = requests.post(f"{BASE_URL}/register", json={
    "username": "testuser123",
    "password": "testpass123"
})
print("Register:", response.json())

# Test login
response = requests.post(f"{BASE_URL}/login", json={
    "username": "testuser123", 
    "password": "testpass123"
})
print("Login:", response.json())

if response.status_code == 200:
    token = response.json()['token']
    print(f"Token: {token}")
    
    # Test VPN config generation
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(f"{BASE_URL}/vpn/generate-config", 
                           headers=headers)
    print("VPN Config:", response.json())