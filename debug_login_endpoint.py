import sys
import os
sys.path.append(os.path.join(os.getcwd(), "backend"))

# Set env before importing settings
os.environ["DATABASE_URL"] = "postgresql://postgres:raim100100@localhost:5432/schedulesys"

from fastapi.testclient import TestClient
from app.main import app

def debug_login_endpoint():
    client = TestClient(app)
    print("Testing login via TestClient...")
    
    data = {
        "username": "990101000001",
        "password": "admin123"
    }
    
    # OAuth2PasswordRequestForm expects data in application/x-www-form-urlencoded
    response = client.post("/api/auth/token", data=data)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 500:
        print("INTERNAL SERVER ERROR DETECTED!")
        # TestClient doesn't show the server-side traceback directly unless configured, 
        # but the local execution should crash if I call it without catching.
    else:
        print(f"Response: {response.json()}")

if __name__ == "__main__":
    debug_login_endpoint()
