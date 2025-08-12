from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import hashlib
import secrets
import logging
import re
import jwt
import subprocess
import base64
from datetime import datetime, timedelta

# Cryptography imports for WireGuard key generation
try:
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import x25519
    print("✅ Cryptography library available")
except ImportError:
    print("❌ Install: pip install cryptography PyJWT")

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DB_CONFIG = {
    'host': 'test-database.cnccs0uoe80h.me-central-1.rds.amazonaws.com',
    'user': 'root',
    'password': 'TX6vmO24miWp48mfgk0u',
    'database': 'ghostswitch',
    'charset': 'utf8mb4',
    'autocommit': True
}

SERVER_PUBLIC_KEY = '198Q3PykQ81WMNpy3FuO978z+y4iTk9ssNzi9KzCF3o='
SERVER_ENDPOINT = "51.112.111.180:51820"
JWT_SECRET = "X@4h7HzY0@GB@-L#JC73@G48kI$F7eKokebg5I_P%ILY4+$i!Sn3S@RoAkrMjHBo"

def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        logger.error(f"Error connecting to MySQL: {e}")
        return None


def hash_password(password, salt):
    """Hash password with salt using SHA-256"""
    return hashlib.sha256((password + salt).encode('utf-8')).hexdigest()

def generate_salt():
    """Generate a random salt"""
    return secrets.token_hex(16)

def validate_username(username):
    """Validate username requirements"""
    if len(username) < 8:
        return False, "Username must be at least 8 characters long"
    return True, "Valid"

def validate_password(password):
    """Validate password requirements"""
    import re
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Valid"

def token_required(f):
    """Decorator to require valid JWT token for protected endpoints"""
    def decorated_function(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'success': False, 'message': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401
        
        try:
            # Decode JWT token
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            current_user_id = data['user_id']
            
            # Get user from database
            conn = get_db_connection()
            if not conn:
                return jsonify({'success': False, 'message': 'Database error'}), 500
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id = %s", (current_user_id,))
            current_user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not current_user:
                return jsonify({'success': False, 'message': 'User not found'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Token is invalid'}), 401
        except Exception as e:
            return jsonify({'success': False, 'message': f'Token error: {str(e)}'}), 401
        
        return f(current_user, *args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            return jsonify({
                'success': True,
                'message': 'API and database are healthy',
                'timestamp': datetime.now().isoformat(),
                'server_endpoint': SERVER_ENDPOINT
            }), 200
        else:
            return jsonify({
                'success': False, 
                'message': 'Database connection failed'
            }), 500
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False, 
            'message': f'Health check error: {str(e)}'
        }), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username and password are required'
            }), 400
        
        # Validate username
        username_valid, username_msg = validate_username(username)
        if not username_valid:
            return jsonify({
                'success': False,
                'message': username_msg
            }), 400
        
        # Validate password
        password_valid, password_msg = validate_password(password)
        if not password_valid:
            return jsonify({
                'success': False,
                'message': password_msg
            }), 400
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor()
        
        try:
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            existing_user = cursor.fetchone()
            
            if existing_user:
                return jsonify({
                    'success': False,
                    'message': 'Username already exists'
                }), 409
            
            # Generate salt and hash password
            salt = generate_salt()
            password_hash = hash_password(password, salt)
            
            # Insert new user
            cursor.execute(
                "INSERT INTO users (username, password_hash, salt) VALUES (%s, %s, %s)",
                (username, password_hash, salt)
            )
            
            logger.info(f"New user registered: {username}")
            
            return jsonify({
                'success': True,
                'message': 'User registered successfully'
            }), 201
            
        except Error as e:
            logger.error(f"Database error during registration: {e}")
            return jsonify({
                'success': False,
                'message': 'Registration failed'
            }), 500
        
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate user login"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Username and password are required'
            }), 400
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute(
                "SELECT id, username, password_hash, salt FROM users WHERE username = %s", 
                (username,)
            )
            user = cursor.fetchone()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'Invalid credentials'
                }), 401
            
            # Verify password
            password_hash = hash_password(password, user['salt'])
            
            if password_hash == user['password_hash']:
                # Generate JWT token
                token_payload = {
                    'user_id': user['id'],
                    'username': user['username'],
                    'exp': datetime.utcnow() + timedelta(hours=24)
                }
                token = jwt.encode(token_payload, JWT_SECRET, algorithm='HS256')
                
                # Update last login
                cursor.execute("UPDATE users SET last_login = %s WHERE id = %s", 
                             (datetime.now(), user['id']))
                
                logger.info(f"User logged in: {username}")
                
                return jsonify({
                    'success': True,
                    'message': 'Login successful',
                    'token': token,
                    'user': {
                        'id': user['id'],
                        'username': user['username']
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Invalid credentials'
                }), 401
                
        except Error as e:
            logger.error(f"Database error during login: {e}")
            return jsonify({
                'success': False,
                'message': 'Login failed'
            }), 500
        
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

# NEW: VPN Configuration Generation Endpoint
@app.route('/api/vpn/generate-config', methods=['POST'])
@token_required
def generate_vpn_config(current_user):
    """Generate WireGuard configuration for user"""
    try:
        logger.info(f"Generating VPN config for user: {current_user['username']}")
        
        # Check if user already has an active config
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Database connection failed'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Check for existing active config
        cursor.execute("""
            SELECT * FROM vpn_configs 
            WHERE user_id = %s AND is_active = 1
            ORDER BY created_at DESC LIMIT 1
        """, (current_user['id'],))
        
        existing_config = cursor.fetchone()
        
        if existing_config:
            # Return existing config
            config_text = create_client_config(
                existing_config['client_private_key'],
                existing_config['assigned_ip']
            )
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'config': config_text,
                'client_ip': existing_config['assigned_ip'],
                'message': 'Using existing configuration'
            }), 200
        
        # Generate new key pair
        try:
            private_key = x25519.X25519PrivateKey.generate()
            public_key = private_key.public_key()
            
            # Convert to WireGuard base64 format
            private_key_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
            public_key_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            
            client_private = base64.b64encode(private_key_bytes).decode('utf-8')
            client_public = base64.b64encode(public_key_bytes).decode('utf-8')
            
        except Exception as e:
            logger.error(f"Key generation failed: {e}")
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'message': 'Key generation failed'}), 500
        
        # Get next available IP
        assigned_ip = get_next_available_ip(cursor)
        
        # Create client config
        config_text = create_client_config(client_private, assigned_ip)
        
        # Save to database
        try:
            insert_query = """
                INSERT INTO vpn_configs 
                (user_id, server_id, client_public_key, client_private_key, assigned_ip, is_active) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                current_user['id'], 
                1,  # Default server ID
                client_public, 
                client_private,
                assigned_ip,
                True
            ))
            
            config_id = cursor.lastrowid
            
            # Update server configuration
            success = update_server_config(client_public, assigned_ip)
            if not success:
                logger.warning(f"Failed to update server config for user {current_user['username']}")
            
            logger.info(f"New VPN config created for user {current_user['username']}, IP: {assigned_ip}")
            
            return jsonify({
                'success': True,
                'config': config_text,
                'client_ip': assigned_ip,
                'message': 'VPN configuration generated successfully'
            }), 200
            
        except Error as e:
            logger.error(f"Database error saving VPN config: {e}")
            return jsonify({'success': False, 'message': 'Failed to save configuration'}), 500
        
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        logger.error(f"VPN config generation error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

def get_next_available_ip(cursor):
    """Find next available IP in 10.0.0.x range"""
    try:
        cursor.execute("SELECT assigned_ip FROM vpn_configs WHERE is_active = 1")
        used_ips = set([row['assigned_ip'] for row in cursor.fetchall()])
        
        # Start from 10.0.0.2 (10.0.0.1 is server)
        for i in range(2, 255):
            ip = f"10.0.0.{i}"
            if ip not in used_ips:
                return ip
        
        raise Exception("No available IP addresses in range")
    except Exception as e:
        logger.error(f"IP assignment error: {e}")
        raise

def create_client_config(private_key, client_ip):
    """Create WireGuard client configuration"""
    return f"""[Interface]
PrivateKey = {private_key}
Address = {client_ip}/32
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = {SERVER_PUBLIC_KEY}
Endpoint = {SERVER_ENDPOINT}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""

def update_server_config(client_public_key, client_ip):
    """Add new peer to server WireGuard config"""
    try:
        # Path to server config file
        config_path = '/etc/wireguard/wg0.conf'
        
        # New peer configuration
        new_peer = f"""
# Client {client_ip}
[Peer]
PublicKey = {client_public_key}
AllowedIPs = {client_ip}/32
"""
        
        # Append to server config
        with open(config_path, 'a') as f:
            f.write(new_peer)
        
        # Reload WireGuard configuration
        result = subprocess.run(['systemctl', 'reload', 'wg-quick@wg0'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info(f"Server config updated successfully for IP {client_ip}")
            return True
        else:
            logger.error(f"Failed to reload WireGuard: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to update server config: {e}")
        return False

# NEW: VPN Connection Logging
@app.route('/api/vpn/connect', methods=['POST'])
@token_required
def log_vpn_connection(current_user):
    """Log VPN connection event"""
    try:
        data = request.get_json()
        server_endpoint = data.get('server_endpoint', SERVER_ENDPOINT)
        
        logger.info(f"VPN connection logged for user {current_user['username']} to {server_endpoint}")
        
        return jsonify({
            'success': True,
            'message': 'Connection logged successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Connection logging error: {e}")
        return jsonify({'success': False, 'message': 'Logging failed'}), 500

@app.route('/api/vpn/disconnect', methods=['POST'])
@token_required
def log_vpn_disconnection(current_user):
    """Log VPN disconnection event"""
    try:
        logger.info(f"VPN disconnection logged for user {current_user['username']}")
        
        return jsonify({
            'success': True,
            'message': 'Disconnection logged successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Disconnection logging error: {e}")
        return jsonify({'success': False, 'message': 'Logging failed'}), 500

# Print configuration on startup
print(f"🔑 Server Public Key: {SERVER_PUBLIC_KEY}")
print(f"🌐 Server Endpoint: {SERVER_ENDPOINT}")
print(f"🔐 JWT Secret configured: {'*' * len(JWT_SECRET)}")

if __name__ == '__main__':
    # Test database connection on startup
    print("Testing database connection...")
    test_conn = get_db_connection()
    if test_conn:
        print("✓ Database connection successful")
        test_conn.close()
    else:
        print("✗ Database connection failed")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)