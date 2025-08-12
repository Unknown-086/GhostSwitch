import requests
import json

# API base URL (update with your server IP)
BASE_URL = "http://51.112.111.180:5000/api"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_register():
    """Test user registration"""
    print("Testing user registration...")
    data = {
        "username": "testuser123",
        "password": "TestPass123!"
    }
    response = requests.post(f"{BASE_URL}/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_login():
    """Test user login"""
    print("Testing user login...")
    data = {
        "username": "testuser123",
        "password": "TestPass123!"
    }
    response = requests.post(f"{BASE_URL}/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_check_username():
    """Test username availability"""
    print("Testing username check...")
    data = {
        "username": "testuser123"
    }
    response = requests.post(f"{BASE_URL}/check-username", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

if __name__ == "__main__":
    test_health()
    test_register()
    test_login()
    test_check_username()