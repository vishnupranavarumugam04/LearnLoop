import requests
import sys

BASE_URL = "http://localhost:8000/api/auth"

def test_signup(username, password):
    print(f"Attempting Register: {username}")
    res = requests.post(f"{BASE_URL}/register", json={
        "username": username,
        "password": password,
        "full_name": "Test User"
    })
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")
    return res.status_code == 200

def test_login(username, password):
    print(f"Attempting Login: {username}")
    res = requests.post(f"{BASE_URL}/login", data={
        "username": username,
        "password": password
    })
    print(f"Status: {res.status_code}")
    print(f"Response: {res.text}")
    return res.status_code == 200

if __name__ == "__main__":
    email = "test_debug@example.com"
    pwd = "password123"
    
    # 1. Try Register
    test_signup(email, pwd)
    
    # 2. Try Login
    test_login(email, pwd)
