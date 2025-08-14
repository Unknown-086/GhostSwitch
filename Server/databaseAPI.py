from flask import Flask, request, jsonify
from flask_cors import CORS
from mysql.connector import Error
from base64 import b64encode
from datetime import datetime, timedelta
import hashlib
import secrets
import re
import jwt
import subprocess
import logging
import mysql.connector
import os

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

SERVER_PUBLIC_KEY = 'G4MrkLV9bhoLQyjL74auW3xdpjEwOXmphD+ogPhPYV4='
SERVER_ENDPOINT = "3.28.190.141:51820"
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
                token = auth_header.split(' ')[1]  # Bearer <token>
            except IndexError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid authorization header format'
                }), 401
        
        if not token:
            return jsonify({
                'success': False,
                'message': 'Authentication token required'
            }), 401
        
        try:
            # Decode JWT token
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            current_user_id = data['user_id']
            
            # Get user from database
            conn = get_db_connection()
            if not conn:
                return jsonify({
                    'success': False,
                    'message': 'Database connection failed'
                }), 500
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE id = %s", (current_user_id,))
            current_user = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not current_user:
                return jsonify({
                    'success': False,
                    'message': 'User not found'
                }), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({
                'success': False,
                'message': 'Token has expired'
            }), 401
        except jwt.InvalidTokenError:
            return jsonify({
                'success': False,
                'message': 'Invalid token'
            }), 401
        except Exception as e:
            return jsonify({
                'success': False,
                'message': f'Token validation error: {str(e)}'
            }), 401
        
        return f(current_user, *args, **kwargs)
    
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            return jsonify({
                'success': True,
                'message': 'Backend is healthy',
                'database': 'connected',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Database connection failed',
                'database': 'disconnected'
            }), 500
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'message': 'Health check failed',
            'error': str(e)
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
            if cursor.fetchone():
                return jsonify({
                    'success': False,
                    'message': 'Username already exists'
                }), 409
            
            # Generate salt and hash password
            salt = generate_salt()
            password_hash = hash_password(password, salt)
            
            # Insert new user
            cursor.execute("""
                INSERT INTO users (username, password_hash, salt) 
                VALUES (%s, %s, %s)
            """, (username, password_hash, salt))
            
            conn.commit()
            
            logger.info(f"New user registered: {username}")
            
            return jsonify({
                'success': True,
                'message': 'Registration successful'
            }), 201
            
        except Error as e:
            logger.error(f"Registration database error: {e}")
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
            # Get user from database
            cursor.execute("""
                SELECT id, username, password_hash, salt 
                FROM users WHERE username = %s
            """, (username,))
            
            user = cursor.fetchone()
            
            if not user:
                return jsonify({
                    'success': False,
                    'message': 'Invalid credentials'
                }), 401
            
            # Verify password
            expected_hash = hash_password(password, user['salt'])
            if expected_hash != user['password_hash']:
                return jsonify({
                    'success': False,
                    'message': 'Invalid credentials'
                }), 401
            
            # Update last login
            cursor.execute("""
                UPDATE users SET last_login = CURRENT_TIMESTAMP 
                WHERE id = %s
            """, (user['id'],))
            conn.commit()
            
            # Generate JWT token
            token_payload = {
                'user_id': user['id'],
                'username': user['username'],
                'exp': datetime.utcnow() + timedelta(hours=24)
            }
            
            token = jwt.encode(token_payload, JWT_SECRET, algorithm='HS256')
            
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
                
        except Error as e:
            logger.error(f"Login database error: {e}")
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

# VPN Configuration Generation Endpoint
@app.route('/api/vpn/generate-config', methods=['POST'])
@token_required
def generate_vpn_config(current_user):
    """Generate WireGuard configuration for user"""
    try:
        logger.info(f"Generating VPN config for user: {current_user['username']}")
        
        # Check if user already has an active config
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Check for existing active config
        cursor.execute("""
            SELECT * FROM vpn_configs 
            WHERE user_id = %s AND is_active = 1
            ORDER BY created_at DESC LIMIT 1
        """, (current_user['id'],))
        
        existing_config = cursor.fetchone()
        
        if existing_config:
            # If database has preshared key, use it, otherwise config doesn't need it
            psk = existing_config.get('preshared_key', None)
            client_config = create_client_config_with_psk(
                existing_config['client_private_key'], 
                existing_config['assigned_ip'],
                psk
            )
            
            return jsonify({
                'success': True,
                'message': 'Using existing VPN configuration',
                'client_ip': existing_config['assigned_ip'],
                'config': client_config,
                'endpoint': SERVER_ENDPOINT
            }), 200
        
        # Generate new key pair with preshared key
        try:
            client_private, client_public, preshared_key = generate_wireguard_keys()
        except Exception as e:
            logger.error(f"Key generation failed: {e}")
            return jsonify({
                'success': False,
                'message': 'Failed to generate encryption keys'
            }), 500
        
        # Get next available IP
        assigned_ip = get_next_available_ip(cursor)
        
        # Create client config with preshared key
        config_text = create_client_config_with_psk(client_private, assigned_ip, preshared_key)
        
        # Save to database (add preshared_key column if needed)
        try:
            # Check if preshared_key column exists in vpn_configs table
            has_psk_column = False
            try:
                cursor.execute("SHOW COLUMNS FROM vpn_configs LIKE 'preshared_key'")
                has_psk_column = cursor.fetchone() is not None
            except:
                logger.warning("Couldn't check for preshared_key column")
            
            if has_psk_column:
                cursor.execute("""
                    INSERT INTO vpn_configs 
                    (user_id, server_id, client_public_key, client_private_key, preshared_key, assigned_ip, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (current_user['id'], 1, client_public, client_private, preshared_key, assigned_ip, True))
            else:
                cursor.execute("""
                    INSERT INTO vpn_configs 
                    (user_id, server_id, client_public_key, client_private_key, assigned_ip, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (current_user['id'], 1, client_public, client_private, assigned_ip, True))
            
            conn.commit()
            
            # Update server configuration (add peer with preshared key)
            update_server_config(client_public, assigned_ip, preshared_key)
            
            logger.info(f"VPN config generated for {current_user['username']}: {assigned_ip}")
            
            return jsonify({
                'success': True,
                'message': 'VPN configuration generated successfully',
                'client_ip': assigned_ip,
                'config': config_text,
                'endpoint': SERVER_ENDPOINT,
                'server': 'Dubai Server'  # You might want to make this dynamic
            }), 200
            
        except Error as e:
            logger.error(f"Database error saving VPN config: {e}")
            return jsonify({
                'success': False,
                'message': 'Failed to save VPN configuration'
            }), 500
        
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        logger.error(f"VPN config generation error: {e}")
        return jsonify({
            'success': False,
            'message': 'VPN configuration generation failed'
        }), 500

def get_next_available_ip(cursor):
    """Find next available IP in 10.0.0.x range"""
    try:
        cursor.execute("SELECT assigned_ip FROM vpn_configs WHERE is_active = 1")
        used_ips = set([row['assigned_ip'] for row in cursor.fetchall()])
        
        # Start from 10.0.0.2 (10.0.0.1 is server)
        for i in range(5, 255):
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
Address = {client_ip}/24
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = {SERVER_PUBLIC_KEY}
Endpoint = {SERVER_ENDPOINT}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""

def generate_wireguard_keys():
    """Generate proper WireGuard private/public key pair with preshared key"""
    try:
        # Use the proper WireGuard key generation commands
        gen_private = subprocess.run(
            ['wg', 'genkey'],
            capture_output=True, text=True, check=True
        )
        private_key = gen_private.stdout.strip()
        
        # Generate public key from private key
        gen_public = subprocess.run(
            ['wg', 'pubkey'], 
            input=private_key, 
            capture_output=True, text=True, check=True
        )
        public_key = gen_public.stdout.strip()
        
        # Generate preshared key for extra security
        gen_psk = subprocess.run(
            ['wg', 'genpsk'],
            capture_output=True, text=True, check=True
        )
        preshared_key = gen_psk.stdout.strip()
        
        logger.info("Generated WireGuard key pair successfully")
        return private_key, public_key, preshared_key
        
    except Exception as e:
        logger.error(f"WireGuard key generation failed: {e}")
        
        # Fallback to cryptography library if wg command fails
        try:
            from cryptography.hazmat.primitives.asymmetric import x25519
            private_key_obj = x25519.X25519PrivateKey.generate()
            public_key_obj = private_key_obj.public_key()
            
            private_bytes = private_key_obj.private_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PrivateFormat.Raw,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            public_bytes = public_key_obj.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            )
            
            private_key = b64encode(private_bytes).decode('ascii')
            public_key = b64encode(public_bytes).decode('ascii')
            
            # Generate preshared key (32 random bytes, base64 encoded)
            preshared_bytes = os.urandom(32)
            preshared_key = b64encode(preshared_bytes).decode('ascii')
            
            logger.info("Generated WireGuard key pair using cryptography library")
            return private_key, public_key, preshared_key
            
        except Exception as crypto_error:
            logger.error(f"Cryptography key generation error: {crypto_error}")
            raise

def update_server_config(client_public_key, client_ip, preshared_key=None):
    """Add new peer to server WireGuard config"""
    try:
        # Path to server config file
        config_path = '/etc/wireguard/wg0.conf'
        
        # New peer configuration with preshared key if provided
        new_peer = f"""
# Client {client_ip} added {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
[Peer]
PublicKey = {client_public_key}
"""
        
        # Add preshared key if provided
        if preshared_key:
            new_peer += f"PresharedKey = {preshared_key}\n"
            
        new_peer += f"AllowedIPs = {client_ip}/32\n"
        
        # Always use sudo for consistency
        try:
            logger.info(f"Adding new peer with IP {client_ip} to WireGuard config")
            
            # 1. First, backup current config
            subprocess.run([
                'sudo', 'cp', config_path, f'{config_path}.bak'
            ], capture_output=True, text=True, check=True)
            
            # 2. Bring interface down
            logger.info("Bringing WireGuard interface down")
            down_result = subprocess.run([
                'sudo', 'wg-quick', 'down', 'wg0'
            ], capture_output=True, text=True, timeout=30)
            
            if down_result.returncode != 0:
                logger.warning(f"Issue bringing interface down: {down_result.stderr}")
                # Continue anyway - it might not be up
            
            # 3. Append to config file using sudo
            logger.info("Appending peer configuration")
            append_result = subprocess.run([
                'sudo', 'tee', '-a', config_path
            ], input=new_peer, text=True, capture_output=True)
            
            if append_result.returncode != 0:
                logger.error(f"Failed to append config: {append_result.stderr}")
                # Try to restore interface from potential down state
                subprocess.run(['sudo', 'wg-quick', 'up', 'wg0'], 
                              capture_output=True, text=True)
                return False
                
            # 4. Bring interface back up
            logger.info("Bringing WireGuard interface back up")
            up_result = subprocess.run([
                'sudo', 'wg-quick', 'up', 'wg0'
            ], capture_output=True, text=True, timeout=30)
            
            if up_result.returncode != 0:
                logger.error(f"Failed to bring interface up: {up_result.stderr}")
                return False
                
            logger.info(f"Peer with IP {client_ip} successfully added to WireGuard")
            return True
                
        except Exception as cmd_error:
            logger.error(f"Command execution error: {cmd_error}")
            # Attempt to restore interface
            try:
                subprocess.run(['sudo', 'wg-quick', 'up', 'wg0'], 
                              capture_output=True, text=True)
            except Exception:
                pass
            return False
            
    except Exception as e:
        logger.error(f"Failed to update server config: {e}")
        return False

# VPN Connection Logging
@app.route('/api/vpn/connect', methods=['POST'])
@token_required
def log_vpn_connection(current_user):
    """Log VPN connection event"""
    try:
        data = request.get_json()
        server_endpoint = data.get('server_endpoint', SERVER_ENDPOINT)
        
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO connection_logs (user_id, action, server_endpoint)
                VALUES (%s, %s, %s)
            """, (current_user['id'], 'connect', server_endpoint))
            
            conn.commit()
            
            logger.info(f"VPN connection logged for user {current_user['username']}")
            
            return jsonify({
                'success': True,
                'message': 'Connection logged successfully'
            }), 200
            
        except Error as e:
            logger.error(f"Failed to log connection: {e}")
            return jsonify({
                'success': False,
                'message': 'Failed to log connection'
            }), 500
        
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        logger.error(f"Connection logging error: {e}")
        return jsonify({
            'success': False,
            'message': 'Connection logging failed'
        }), 500

@app.route('/api/vpn/disconnect', methods=['POST'])
@token_required
def log_vpn_disconnection(current_user):
    """Log VPN disconnection event"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO connection_logs (user_id, action)
                VALUES (%s, %s)
            """, (current_user['id'], 'disconnect'))
            
            conn.commit()
            
            logger.info(f"VPN disconnection logged for user {current_user['username']}")
            
            return jsonify({
                'success': True,
                'message': 'Disconnection logged successfully'
            }), 200
            
        except Error as e:
            logger.error(f"Failed to log disconnection: {e}")
            return jsonify({
                'success': False,
                'message': 'Failed to log disconnection'
            }), 500
        
        finally:
            cursor.close()
            conn.close()
        
    except Exception as e:
        logger.error(f"Disconnection logging error: {e}")
        return jsonify({
            'success': False,
            'message': 'Disconnection logging failed'
        }), 500

# Get Available VPN Servers
@app.route('/api/servers', methods=['GET'])
def get_servers():
    """Get list of available VPN servers"""
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({
                'success': False,
                'message': 'Database connection failed'
            }), 500
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT id, name, location, public_ip, endpoint, status 
                FROM servers 
                WHERE status = 'active'
                ORDER BY name
            """)
            
            servers = cursor.fetchall()
            
            # Add flag for each server
            for server in servers:
                server['flag'] = get_flag_for_location(server['location'])
            
            logger.info(f"Retrieved {len(servers)} active servers")
            
            return jsonify({
                'success': True,
                'message': f'Found {len(servers)} servers',
                'servers': servers
            }), 200
            
        except Error as e:
            logger.error(f"Failed to retrieve servers: {e}")
            return jsonify({
                'success': False,
                'message': 'Failed to retrieve servers'
            }), 500
        
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Server retrieval error: {e}")
        return jsonify({
            'success': False,
            'message': 'Server retrieval failed'
        }), 500

def get_flag_for_location(location):
    """Get flag emoji for location"""
    location_lower = location.lower()
    if 'dubai' in location_lower or 'uae' in location_lower:
        return '🇦🇪'
    elif 'usa' in location_lower or 'america' in location_lower:
        return '🇺🇸'
    elif 'uk' in location_lower or 'london' in location_lower:
        return '🇬🇧'
    elif 'japan' in location_lower or 'tokyo' in location_lower:
        return '🇯🇵'
    else:
        return '🌍'



def create_client_config_with_psk(private_key, client_ip, preshared_key=None):
    """Create WireGuard client configuration with optional preshared key"""
    config = f"""[Interface]
PrivateKey = {private_key}
Address = {client_ip}/24
DNS = 1.1.1.1, 8.8.8.8

[Peer]
PublicKey = {SERVER_PUBLIC_KEY}
"""
    
    # Add preshared key if provided
    if preshared_key:
        config += f"PresharedKey = {preshared_key}\n"
        
    config += f"""Endpoint = {SERVER_ENDPOINT}
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""
    
    return config

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





