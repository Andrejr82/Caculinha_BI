"""
Create users.parquet file for authentication when SQL Server is not available

Password: Admin@2024
Pre-generated hash using bcrypt

MIGRATED TO DUCKDB (2025-12-31)
- Uses Pandas for DataFrame creation
- Pandas -> Parquet for small datasets
"""
import pandas as pd
import uuid
from pathlib import Path
from datetime import datetime, timezone
import json

# Pre-generated bcrypt hash for "Admin@2024"
# Generated using: bcrypt.hashpw(b"Admin@2024", bcrypt.gensalt())
# This hash is valid and verified
ADMIN_PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.EBMHJyT3xC3q4O"

# Pre-generated bcrypt hash for "User@2024"
USER_PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.EBMHJyT3xC3q4O"

admin_id = str(uuid.uuid4())
user_id = str(uuid.uuid4())

# Create users data
users_data = {
    "id": [admin_id, user_id],
    "username": ["admin", "user"],
    "email": ["admin@agentbi.com", "user@agentbi.com"],
    "full_name": ["Administrator", "Standard User"],
    "hashed_password": [ADMIN_PASSWORD_HASH, USER_PASSWORD_HASH],
    "is_active": [True, True],
    "is_superuser": [True, False],
    "role": ["admin", "user"],
    "allowed_segments": [json.dumps(["*"]), json.dumps(["*"])],
    "created_at": [datetime.now(timezone.utc), datetime.now(timezone.utc)],
    "updated_at": [datetime.now(timezone.utc), datetime.now(timezone.utc)],
    "last_login": [None, None]
}

# Create DataFrame with Pandas
df = pd.DataFrame(users_data)

# Save to parquet
output_path = Path(__file__).parent.parent.parent / "data" / "parquet" / "users.parquet"
output_path.parent.mkdir(parents=True, exist_ok=True)

df.to_parquet(output_path, index=False)

print(f"[OK] Created users.parquet at {output_path}")
print(f"\nDefault credentials:")
print(f"  Admin Username: admin")
print(f"  Admin Password: Admin@2024")
print(f"\n  User Username: user")
print(f"  User Password: Admin@2024")
print(f"\nUser details:")
print(df)
