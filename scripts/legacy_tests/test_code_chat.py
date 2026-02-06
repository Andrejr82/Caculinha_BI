#!/usr/bin/env python3
import requests
import json

# Login as admin
login_url = "http://127.0.0.1:8000/api/v1/auth/login"
login_data = {"username": "admin", "password": "Admin@2024"}

response = requests.post(login_url, json=login_data)
print(f"Login status: {response.status_code}")

if response.status_code == 200:
    token = response.json()["access_token"]

    # Test code-chat stats endpoint
    stats_url = "http://127.0.0.1:8000/api/v1/code-chat/stats"
    headers = {"Authorization": f"Bearer {token}"}

    stats_response = requests.get(stats_url, headers=headers)
    print(f"\nCode Chat Stats status: {stats_response.status_code}")
    print(f"Response: {json.dumps(stats_response.json(), indent=2)}")
else:
    print(f"Login failed: {response.text}")
