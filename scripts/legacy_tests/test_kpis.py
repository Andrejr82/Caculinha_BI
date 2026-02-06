#!/usr/bin/env python3
import requests
import json
import sys

# Login to get token
login_url = "http://127.0.0.1:8000/api/v1/auth/login"
login_data = {
    "username": "admin",
    "password": "Admin@2024"
}

try:
    response = requests.post(login_url, json=login_data)
    print(f"Login status: {response.status_code}")

    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get("access_token")

        # Test business-kpis endpoint
        kpis_url = "http://127.0.0.1:8000/api/v1/metrics/business-kpis"
        headers = {"Authorization": f"Bearer {access_token}"}

        kpis_response = requests.get(kpis_url, headers=headers)
        print(f"\nKPIs status: {kpis_response.status_code}")
        print(f"KPIs response: {json.dumps(kpis_response.json(), indent=2)}")
    else:
        print(f"Login failed: {response.text}")
        sys.exit(1)

except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
