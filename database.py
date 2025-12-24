import sqlite3
import os

DATABASE_FILE = "app_data.db"

def initialize_database():
    """Initializes the database and creates all required tables."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
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
    
    # App settings table for storing configuration
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # Doctor leaves table for managing staff leave schedules
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS doctor_leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_short_name TEXT NOT NULL,
            leave_date TEXT NOT NULL,
            session TEXT NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

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


# ===== App Settings Functions =====

def get_disabled_staff():
    """Get list of disabled staff from database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_settings WHERE key = 'disabled_staff'")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        import json
        return json.loads(row[0])
    return []


def set_disabled_staff(disabled_list):
    """Save list of disabled staff to database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    import json
    value = json.dumps(disabled_list)
    
    cursor.execute("""
        INSERT OR REPLACE INTO app_settings (key, value)
        VALUES ('disabled_staff', ?)
    """, (value,))
    
    conn.commit()
    conn.close()


# ===== Doctor Leave Functions =====

def add_doctor_leave(staff_short_name, leave_date, session, reason=""):
    """Add a doctor leave record."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO doctor_leaves (staff_short_name, leave_date, session, reason)
        VALUES (?, ?, ?, ?)
    """, (staff_short_name, leave_date, session, reason))
    conn.commit()
    leave_id = cursor.lastrowid
    conn.close()
    return leave_id


def get_all_doctor_leaves():
    """Get all doctor leave records."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, staff_short_name, leave_date, session, reason
        FROM doctor_leaves
        ORDER BY leave_date DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    leaves = []
    for row in rows:
        leaves.append({
            'id': row[0],
            'staff_short_name': row[1],
            'leave_date': row[2],
            'session': row[3],
            'reason': row[4] if row[4] else ""
        })
    return leaves


def delete_doctor_leave(leave_id):
    """Delete a doctor leave record."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM doctor_leaves WHERE id = ?", (leave_id,))
    conn.commit()
    conn.close()


def check_staff_available(staff_short_name, date_str, time_str):
    """
    Check if staff is available at the given date and time.
    Returns (is_available, reason)
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT session FROM doctor_leaves
        WHERE staff_short_name = ? AND trim(leave_date) = ?
    """, (staff_short_name, date_str.strip()))
    
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        return (True, "")
    
    leave_session = result[0]
    
    # Determine appointment session from time
    try:
        hour = int(time_str.split(':')[0])
        if 7 <= hour < 13:
            appt_session = "morning"
        elif 13 <= hour < 18:
            appt_session = "afternoon"
        else:
            appt_session = "unknown"
    except:
        return (True, "")
    
    # Check if leave conflicts with appointment
    if leave_session == "full_day":
        return (False, "Cả ngày")
    elif leave_session == appt_session:
        session_vn = "Sáng" if appt_session == "morning" else "Chiều"
        return (False, session_vn)
    
    return (True, "")


if __name__ == "__main__":
    # Initialize database
    initialize_database()
    print("Database initialized successfully")
