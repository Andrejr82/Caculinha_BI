"""
Script to initialize SQL Server database.
Creates the database if it doesn't exist.
"""

import os
import sys
import pyodbc
from dotenv import load_dotenv

# Add parent dir to path to import settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config.settings import get_settings

def create_database():
    load_dotenv()
    settings = get_settings()
    
    # Parse connection string to get server and credentials
    # Assuming PYODBC_CONNECTION_STRING is set or we construct it
    conn_str = settings.PYODBC_CONNECTION_STRING
    
    # We need to connect to 'master' database to create a new database
    # Replace 'DATABASE=agentbi' with 'DATABASE=master'
    if "DATABASE=agentbi" in conn_str:
        master_conn_str = conn_str.replace("DATABASE=agentbi", "DATABASE=master")
    else:
        # Fallback if string format is different
        master_conn_str = conn_str + ";DATABASE=master"
        
    print(f"Connecting to master database...")
    
    try:
        conn = pyodbc.connect(master_conn_str, autocommit=True)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT name FROM sys.databases WHERE name = 'agentbi'")
        if cursor.fetchone():
            print("Database 'agentbi' already exists.")
        else:
            print("Creating database 'agentbi'...")
            cursor.execute("CREATE DATABASE agentbi")
            print("Database 'agentbi' created successfully.")
            
        conn.close()
        
    except Exception as e:
        print(f"Error creating database: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_database()
