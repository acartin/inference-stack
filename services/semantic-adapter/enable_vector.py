
import psycopg2
import os

# Use the credentials I extracted
CONN_STR = "postgresql://acartin:Toyota_15@192.168.0.31:5432/agentic"

def enable_extension():
    try:
        conn = psycopg2.connect(CONN_STR)
        conn.autocommit = True
        cur = conn.cursor()
        
        print("Checking/Enabling vector extension...")
        try:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            print("Extension 'vector' assured.")
        except Exception as e:
            print(f"Error creating extension: {e}")

        # Check types
        cur.execute("SELECT typname FROM pg_type WHERE typname = 'vector'")
        row = cur.fetchone()
        if row:
            print("Type 'vector' found in pg_type.")
        else:
            print("Type 'vector' NOT FOUND in pg_type!")

        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    enable_extension()
