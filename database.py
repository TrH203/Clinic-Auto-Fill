import sqlite3
import os

DATABASE_FILE = "app_data.db"

def initialize_database():
    """Initializes the database and creates the version table if it doesn't exist."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS version (
            id INTEGER PRIMARY KEY,
            version_string TEXT NOT NULL
        )
    """)
    # Check if a version is already seeded
    cursor.execute("SELECT COUNT(*) FROM version")
    count = cursor.fetchone()[0]

    # Seed the initial version if the table is empty
    if count == 0:
        try:
            with open("VERSION", "r") as f:
                initial_version = f.read().strip()
        except FileNotFoundError:
            initial_version = "1.0.0" # Fallback version

        cursor.execute("INSERT INTO version (id, version_string) VALUES (?, ?)", (1, initial_version))

    conn.commit()
    conn.close()

def get_current_version_from_db():
    """Retrieves the current version from the database."""
    if not os.path.exists(DATABASE_FILE):
        initialize_database()

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT version_string FROM version WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    return row[0] if row else None

def update_version_in_db(new_version):
    """Updates the version in the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE version SET version_string = ? WHERE id = 1", (new_version,))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    # Example usage
    initialize_database()
    print(f"Current version from DB: {get_current_version_from_db()}")

    # To test the update
    # update_version_in_db("1.1.0")
    # print(f"Updated version from DB: {get_current_version_from_db()}")
