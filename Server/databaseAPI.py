from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
import hashlib
import secrets
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for client requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'test-database.cnccs0uoe80h.me-central-1.rds.amazonaws.com',
    'user': 'root',
    'password': 'TX6vmO24miWp48mfgk0u',
    'database': 'ghostswitch',
    'charset': 'utf8mb4',
    'autocommit': True
}

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
                "status": "healthy",
                "database": "connected",
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "status": "unhealthy",
                "database": "disconnected",
                "timestamp": datetime.now().isoformat()
            }), 500
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Username and password are required"
            }), 400
        
        # Validate username
        username_valid, username_msg = validate_username(username)
        if not username_valid:
            return jsonify({
                "success": False,
                "message": username_msg
            }), 400
        
        # Validate password
        password_valid, password_msg = validate_password(password)
        if not password_valid:
            return jsonify({
                "success": False,
                "message": password_msg
            }), 400
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500
        
        cursor = conn.cursor()
        
        try:
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({
                    "success": False,
                    "message": "Username already exists"
                }), 409
            
            # Generate salt and hash password
            salt = generate_salt()
            password_hash = hash_password(password, salt)
            
            # Insert new user
            insert_query = """
                INSERT INTO users (username, password_hash, salt, created_at) 
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (username, password_hash, salt, datetime.now()))
            
            user_id = cursor.lastrowid
            
            logger.info(f"New user registered: {username} (ID: {user_id})")
            
            return jsonify({
                "success": True,
                "message": "User registered successfully",
                "user_id": user_id
            }), 201
            
        except Error as e:
            logger.error(f"Database error during registration: {e}")
            return jsonify({
                "success": False,
                "message": "Registration failed due to database error"
            }), 500
        
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate user login"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        # Validate input
        if not username or not password:
            return jsonify({
                "success": False,
                "message": "Username and password are required"
            }), 400
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({
                "success": False,
                "message": "Database connection failed"
            }), 500
        
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get user data
            cursor.execute(
                "SELECT id, username, password_hash, salt FROM users WHERE username = %s", 
                (username,)
            )
            user = cursor.fetchone()
            
            if not user:
                logger.warning(f"Login attempt with non-existent username: {username}")
                return jsonify({
                    "success": False,
                    "message": "Invalid username or password"
                }), 401
            
            # Verify password
            password_hash = hash_password(password, user['salt'])
            
            if password_hash == user['password_hash']:
                # Update last login
                cursor.execute(
                    "UPDATE users SET last_login = %s WHERE id = %s",
                    (datetime.now(), user['id'])
                )
                
                logger.info(f"Successful login: {username} (ID: {user['id']})")
                
                return jsonify({
                    "success": True,
                    "message": "Login successful",
                    "user": {
                        "id": user['id'],
                        "username": user['username']
                    }
                }), 200
            else:
                logger.warning(f"Invalid password for user: {username}")
                return jsonify({
                    "success": False,
                    "message": "Invalid username or password"
                }), 401
                
        except Error as e:
            logger.error(f"Database error during login: {e}")
            return jsonify({
                "success": False,
                "message": "Login failed due to database error"
            }), 500
        
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@app.route('/api/check-username', methods=['POST'])
def check_username():
    """Check if username is available"""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({
                "available": False,
                "message": "Username is required"
            }), 400
        
        # Validate username format
        username_valid, username_msg = validate_username(username)
        if not username_valid:
            return jsonify({
                "available": False,
                "message": username_msg
            }), 400
        
        # Connect to database
        conn = get_db_connection()
        if not conn:
            return jsonify({
                "available": False,
                "message": "Database connection failed"
            }), 500
        
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            user_exists = cursor.fetchone() is not None
            
            return jsonify({
                "available": not user_exists,
                "message": "Username already taken" if user_exists else "Username available"
            }), 200
            
        except Error as e:
            logger.error(f"Database error checking username: {e}")
            return jsonify({
                "available": False,
                "message": "Error checking username availability"
            }), 500
        
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Username check error: {e}")
        return jsonify({
            "available": False,
            "message": "Internal server error"
        }), 500

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