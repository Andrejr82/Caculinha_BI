
import duckdb

db_path = r"C:\Projetos_BI\BI_Solution\backend\data\catalog_v1.duckdb"

def hardcore_cleanup():
    with duckdb.connect(db_path) as con:
        # 1. Get all table names
        tables = con.execute("SHOW TABLES").df()['name'].tolist()
        print(f"Existing tables: {tables}")
        
        # 2. Drop everything with fts_ prefix
        for t in tables:
            if t.startswith('fts_'):
                print(f"Dropping FTS table: {t}")
                con.execute(f"DROP TABLE IF EXISTS {t}")
        
        # 3. Try to drop the main index via FTS
        try:
            con.execute("LOAD fts;")
            con.execute("CALL drop_fts_index('products_canonical')")
            print("Dropped FTS index via CALL.")
        except Exception as e:
            print(f"Could not drop FTS index via CALL: {e}")

if __name__ == "__main__":
    hardcore_cleanup()
