# Create test_complete.py
import requests

BASE_URL = "http://51.112.111.180:5000/api"

print("🧪 Testing GhostSwitch API...\n")

# Test health
print("1. Testing Health Check...")
response = requests.get(f"{BASE_URL}/health")
print("Health:", response.json())
print()

# Test registration with proper password
print("2. Testing Registration...")
response = requests.post(f"{BASE_URL}/register", json={
    "username": "realuser2",
    "password": "RealPass123!"  # Has special character
})
print("Register:", response.json())
print()

# Test login
print("3. Testing Login...")
response = requests.post(f"{BASE_URL}/login", json={
    "username": "realuser2", 
    "password": "RealPass123!"
})
print("Login:", response.json())

if response.status_code == 200:
    token = response.json()['token']
    print(f"🔑 Token: {token[:50]}...")
    print()
    
    # Test VPN config generation
    print("4. Testing VPN Config Generation...")
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.post(f"{BASE_URL}/vpn/generate-config", 
                           headers=headers)
    
    config_result = response.json()
    print("VPN Config Result:", {
        'success': config_result.get('success'),
        'client_ip': config_result.get('client_ip'),
        'message': config_result.get('message'),
        'config_length': len(config_result.get('config', '')) if config_result.get('config') else 0
    })
    
    if config_result.get('success') and config_result.get('config'):
        print("\n📄 Generated WireGuard Config Preview:")
        print("=" * 50)
        config_lines = config_result['config'].split('\n')[:10]  # First 10 lines
        for line in config_lines:
            print(line)
        print("=" * 50)
        print("✅ Real VPN configuration generated successfully!")
    
    print()
    
    # Test VPN connection logging
    print("5. Testing VPN Connection Logging...")
    response = requests.post(f"{BASE_URL}/vpn/connect", 
                           headers=headers,
                           json={"server_endpoint": "51.112.111.180:51820"})
    print("Connection Log:", response.json())
    
    # Test VPN disconnection logging
    print("6. Testing VPN Disconnection Logging...")
    response = requests.post(f"{BASE_URL}/vpn/disconnect", 
                           headers=headers)
    print("Disconnection Log:", response.json())

else:
    print("❌ Login failed, cannot test VPN functions")

# New code block for testing /servers endpoint
print("\n🧪 Testing Servers API...\n")

# Test servers endpoint
print("Testing /servers endpoint...")
try:
    response = requests.get(f"{BASE_URL}/servers", timeout=10)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("Response:", data)
        
        if data.get('success'):
            servers = data.get('servers', [])
            print(f"\n✅ Found {len(servers)} servers:")
            for server in servers:
                print(f"  - ID: {server['id']}")
                print(f"    Name: {server['name']}")
                print(f"    Location: {server['location']}")
                print(f"    Endpoint: {server['endpoint']}")
                print(f"    Flag: {server['flag']}")
                print()
        else:
            print("❌ API returned success=false:", data.get('message'))
    else:
        print("❌ HTTP Error:", response.status_code)
        print("Response:", response.text)
        
except requests.exceptions.RequestException as e:
    print(f"❌ Connection Error: {e}")
    print("\n💡 Make sure your backend server is running:")
    print("   cd GhostSwitch/Server")
    print("   python databaseAPI.py")

print("\n🎯 API Testing Complete!")