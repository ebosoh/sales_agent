
import sqlite3

def create_connection():
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect('sales_agent.db')
        print(f"Successfully connected to SQLite database version: {sqlite3.version}")
    except sqlite3.Error as e:
        print(e)
    return conn

def create_tables(conn):
    """ create tables in the SQLite database """
    try:
        c = conn.cursor()
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
        conn.commit()
        print("Tables created successfully.")
    except sqlite3.Error as e:
        print(e)

if __name__ == '__main__':
    connection = create_connection()
    if connection:
        create_tables(connection)
        connection.close()
