import os
import hashlib
import random

def generate_key(username):
    """Generate a 10-digit numeric license key."""
    # Use the username to seed the random number generator for consistency
    seed = int(hashlib.sha256(username.encode()).hexdigest(), 16)
    random.seed(seed)
    key = ''.join([str(random.randint(0, 9)) for _ in range(10)])
    return key

def validate_key(username, key):
    """Validate a 10-digit numeric license key."""
    expected_key = generate_key(username)
    return key == expected_key

if __name__ == '__main__':
    # Example usage
    username = "testuser"
    license_key = generate_key(username)
    print(f"Username: {username}")
    print(f"License key: {license_key}")
    print(f"Is the key valid? {validate_key(username, license_key)}")

    username2 = "anotheruser"
    license_key2 = generate_key(username2)
    print(f"\nUsername: {username2}")
    print(f"License key: {license_key2}")
    print(f"Is the key valid? {validate_key(username2, license_key2)}")

    # Test with an invalid key
    print(f"\nIs key '0000000000' valid for '{username}'? {validate_key(username, '0000000000')}")