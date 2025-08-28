#!/usr/bin/env python3

import os
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

jwt_secret = os.environ.get("JWT_SECRET_KEY")
algorithm = os.environ.get("ALGORITHM", "HS256")

if not jwt_secret:
    print("❌ No JWT_SECRET_KEY found")
    exit(1)

# Create a test admin token
payload = {
    "user_id": "d11ba7c1-5f3b-4906-a728-983364e7b12c",  # Real admin user ID
    "email": "n_sivakumar@yahoo.com",
    "is_admin": True,
    "roles": ["admin"],
    "exp": datetime.utcnow() + timedelta(minutes=30)
}

test_token = jwt.encode(payload, jwt_secret, algorithm=algorithm)
print(f"Test admin token:")
print(test_token)