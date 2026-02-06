"""
Test SQL Server Connection - Windows Auth
Tests connection using Trusted_Connection=yes
"""
import pyodbc

def test_windows_auth():
    instances = [
        ("localhost", "Default Instance"),
        ("localhost\\SQLEXPRESS", "SQLEXPRESS Instance"),
        (".\\SQLEXPRESS", "SQLEXPRESS (dot)")
    ]
    
    print(f"Testing Windows Authentication...")
    
    for server, name in instances:
        print(f"\nTesting {name} ({server})...")
        conn_str = (
            "DRIVER={ODBC Driver 17 for SQL Server};"
            f"SERVER={server};"
            "DATABASE=master;"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
            "Connection Timeout=5;"
        )
        
        try:
            conn = pyodbc.connect(conn_str)
            print(f"✅ SUCCESS! Connected to {name} using Windows Auth")
            
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sys.databases")
            rows = cursor.fetchall()
            print("   Databases found:")
            found_agentbi = False
            for row in rows:
                print(f"    - {row[0]}")
                if row[0] == 'agentbi':
                    found_agentbi = True
            
            if found_agentbi:
                print("   ✅ 'agentbi' database exists!")
            else:
                print("   ❌ 'agentbi' database NOT found!")

            conn.close()
            # Se achou o agentbi, retorna esse server como o correto
            if found_agentbi:
                return server
            
        except Exception as e:
            print(f"❌ FAILED: {e}")

    return None

if __name__ == "__main__":
    test_windows_auth()
