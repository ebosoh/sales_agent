
import sqlite3

def create_connection():
    """ create a database connection to the local SQLite database """
    conn = None
    try:
        conn = sqlite3.connect('sales_agent.db')
        print(f"Successfully connected to local SQLite database version: {sqlite3.version}")
    except sqlite3.Error as e:
        print(e)
    return conn

def create_community_connection():
    """ create a database connection to the shared community SQLite database """
    conn = None
    db_path = r'G:\My Drive\Shared Sales Agent\community_fraud.db'
    try:
        conn = sqlite3.connect(db_path)
        print(f"Successfully connected to community SQLite database at {db_path}")
    except sqlite3.Error as e:
        print(f"Error connecting to community database: {e}")
    return conn

def create_tables(conn, is_community=False):
    """ create tables in the SQLite database """
    try:
        c = conn.cursor()
        if is_community:
            c.execute("""
                CREATE TABLE IF NOT EXISTS fraudulent_numbers (
                    id INTEGER PRIMARY KEY,
                    phone_number TEXT NOT NULL UNIQUE,
                    reason TEXT,
                    reported_by TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            c.execute("""
                CREATE TABLE IF NOT EXISTS groups (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS fraudulent_numbers (
                    id INTEGER PRIMARY KEY,
                    phone_number TEXT NOT NULL UNIQUE,
                    reason TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY,
                    group_name TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    message_text TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    picture_blob BLOB,
                    is_reply INTEGER DEFAULT 0,
                    replied_to_text TEXT,
                    replied_to_sender TEXT,
                    UNIQUE(group_name, sender, message_text, timestamp)
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS seller_catalog (
                    id INTEGER PRIMARY KEY,
                    product TEXT NOT NULL,
                    make TEXT,
                    type TEXT,
                    year TEXT,
                    price_ksh INTEGER,
                    other_details TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS call_logs (
                    id INTEGER PRIMARY KEY,
                    customer_name TEXT,
                    phone_number TEXT,
                    notes TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
        db_type = "Community" if is_community else "Local"
        print(f"{db_type} tables created successfully.")
    except sqlite3.Error as e:
        print(e)

if __name__ == '__main__':
    local_connection = create_connection()
    if local_connection:
        create_tables(local_connection)
        local_connection.close()
    
    community_connection = create_community_connection()
    if community_connection:
        create_tables(community_connection, is_community=True)
        community_connection.close()
