# Generate secure JWT secret
import secrets
import string

def generate_jwt_secret(length=64):
    """Generate a cryptographically secure random string"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# Generate your secret
secret = generate_jwt_secret()
print(f"Your JWT Secret: {secret}")