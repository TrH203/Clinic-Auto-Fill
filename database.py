import sqlite3
import os

DATABASE_FILE = "app_data.db"

def initialize_database():
    """Initializes the database and creates all required tables."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Version table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS version (
            id INTEGER PRIMARY KEY,
            version_string TEXT NOT NULL
        )
    """)
    
    # Manual entries table for user-entered data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manual_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id TEXT NOT NULL,
            procedures TEXT NOT NULL,
            staff TEXT NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        )
    """)
    
    # Update history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS update_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            old_version TEXT NOT NULL,
            new_version TEXT NOT NULL,
            update_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success INTEGER NOT NULL,
            error_message TEXT
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


# ===== Manual Entries Functions =====

def save_manual_entry_to_db(patient_id, procedures, staff, appointment_date, appointment_time, notes=""):
    """Saves a manual entry to the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO manual_entries (patient_id, procedures, staff, appointment_date, appointment_time, notes)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (patient_id, procedures, staff, appointment_date, appointment_time, notes))
    conn.commit()
    entry_id = cursor.lastrowid
    conn.close()
    return entry_id


def load_manual_entries_from_db():
    """Loads all manual entries from the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, patient_id, procedures, staff, appointment_date, appointment_time, created_at, notes
        FROM manual_entries
        ORDER BY created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    entries = []
    for row in rows:
        entries.append({
            'id': row[0],
            'patient_id': row[1],
            'procedures': row[2],
            'staff': row[3],
            'appointment_date': row[4],
            'appointment_time': row[5],
            'created_at': row[6],
            'notes': row[7]
        })
    return entries


def delete_manual_entry_from_db(entry_id):
    """Deletes a manual entry from the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM manual_entries WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()


# ===== Update History Functions =====

def log_update_attempt(old_version, new_version, success, error_message=None):
    """Logs an update attempt to the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO update_history (old_version, new_version, success, error_message)
        VALUES (?, ?, ?, ?)
    """, (old_version, new_version, 1 if success else 0, error_message))
    conn.commit()
    conn.close()


def get_update_history(limit=10):
    """Retrieves the update history from the database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT old_version, new_version, update_date, success, error_message
        FROM update_history
        ORDER BY update_date DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    
    history = []
    for row in rows:
        history.append({
            'old_version': row[0],
            'new_version': row[1],
            'update_date': row[2],
            'success': bool(row[3]),
            'error_message': row[4]
        })
    return history


if __name__ == "__main__":
    # Example usage
    initialize_database()
    print(f"Current version from DB: {get_current_version_from_db()}")

    # To test the update
    # update_version_in_db("1.1.0")
    # print(f"Updated version from DB: {get_current_version_from_db()}")
