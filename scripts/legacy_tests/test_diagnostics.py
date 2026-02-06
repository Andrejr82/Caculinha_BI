#!/usr/bin/env python3
"""
Test script for SQL Server diagnostics endpoint.
Tests the connection test functionality after the PYODBC_CONNECTION_STRING fix.
"""
import requests
import json

# Login as admin
login_url = "http://127.0.0.1:8000/api/v1/auth/login"
login_data = {"username": "admin", "password": "Admin@2024"}

print("=" * 60)
print("Testing SQL Server Diagnostics Endpoint")
print("=" * 60)

response = requests.post(login_url, json=login_data)
print(f"\n1. Login status: {response.status_code}")

if response.status_code == 200:
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Test DB Status endpoint
    print("\n2. Testing /diagnostics/db-status")
    db_status_url = "http://127.0.0.1:8000/api/v1/diagnostics/db-status"
    db_status_response = requests.get(db_status_url, headers=headers)
    print(f"   Status: {db_status_response.status_code}")
    print(f"   Response: {json.dumps(db_status_response.json(), indent=2)}")

    # Test DB Config endpoint
    print("\n3. Testing /diagnostics/config")
    config_url = "http://127.0.0.1:8000/api/v1/diagnostics/config"
    config_response = requests.get(config_url, headers=headers)
    print(f"   Status: {config_response.status_code}")
    print(f"   Response: {json.dumps(config_response.json(), indent=2)}")

    # Test SQL Connection endpoint
    print("\n4. Testing /diagnostics/test-connection")
    test_conn_url = "http://127.0.0.1:8000/api/v1/diagnostics/test-connection"
    test_conn_response = requests.post(test_conn_url, headers=headers)
    print(f"   Status: {test_conn_response.status_code}")
    print(f"   Response: {json.dumps(test_conn_response.json(), indent=2)}")

    print("\n" + "=" * 60)
    if test_conn_response.status_code == 200:
        result = test_conn_response.json()
        if result.get("success"):
            print("✅ SQL Server connection test PASSED")
        else:
            print("⚠️  SQL Server connection test returned failure:")
            print(f"   Message: {result.get('message')}")
    else:
        print("❌ SQL Server connection test endpoint failed")
    print("=" * 60)
else:
    print(f"❌ Login failed: {response.text}")
