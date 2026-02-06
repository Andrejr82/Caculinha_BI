"""
Create users.parquet file with test admin user for authentication fallback
"""
import polars as pl
import bcrypt
from pathlib import Path
import uuid
from datetime import datetime
import json

def create_users_parquet():
    """Create users.parquet with admin user"""

    # Create password hash
    password = "admin123"
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)

    # Create user data
    users_data = {
        "id": [str(uuid.uuid4())],
        "username": ["admin"],
        "email": ["admin@agentbi.com"],
        "hashed_password": [hashed.decode('utf-8')],
        "full_name": ["Administrator"],
        "role": ["admin"],
        "is_active": [True],
        "allowed_segments": [json.dumps(["*"])],
        "created_at": [datetime.utcnow().isoformat()],
        "updated_at": [datetime.utcnow().isoformat()]
    }

    # Create DataFrame
    df = pl.DataFrame(users_data)

    # Save to parquet
    parquet_path = Path(__file__).parent.parent / "data" / "parquet" / "users.parquet"
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    df.write_parquet(parquet_path)

    print(f"Created users.parquet at: {parquet_path}")
    print(f"\nTest user credentials:")
    print(f"  Username: admin")
    print(f"  Password: admin123")
    print(f"  Role: admin")
    print(f"\nAuthentication will now use Parquet fallback if Supabase fails.")

if __name__ == "__main__":
    create_users_parquet()
