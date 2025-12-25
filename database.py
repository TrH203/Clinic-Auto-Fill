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
    
    # Coordinates table for storing UI element positions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coordinates (
            name TEXT PRIMARY KEY,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            description TEXT
        )
    """)

    conn.commit()
    conn.close()
    
    # Initialize default coordinates if table is empty
    initialize_default_coordinates()


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


def get_window_title():
    """Get the target application window title."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_settings WHERE key = 'window_title'")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0]
    return "User: Trần Thị Thu Hiền"  # Default value


def set_window_title(title):
    """Save the target application window title."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO app_settings (key, value)
        VALUES ('window_title', ?)
    """, (title,))
    
    conn.commit()
    conn.close()


def get_arrow_mode_setting():
    """Get arrow mode setting (True/False)."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_settings WHERE key = 'arrow_mode'")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return row[0] == '1'
    return False

def set_arrow_mode_setting(enabled):
    """Save arrow mode setting."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    value = '1' if enabled else '0'
    
    cursor.execute("""
        INSERT OR REPLACE INTO app_settings (key, value)
        VALUES ('arrow_mode', ?)
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


# ===== Coordinates Management Functions =====

def get_default_coordinates():
    """Returns the default coordinate mappings."""
    return {
        'ID_BOX': (78, 191, 'Patient ID input box'),
        'LUU': (537, 966, 'Save button'),
        'TIEP': (464, 964, 'Next button'),
        'SUA': (670, 966, 'Edit button'),
        'PATIENT_ROW': (181, 249, 'First patient row in list'),
        'BSCD_NGUOI_DAU_TIEN': (1595, 348, 'First doctor in dropdown'),
        'CCHN_NGUOI_DAU_TIEN': (1624, 444, 'First diagnosis in dropdown'),
        'CCHN': (1820, 344, 'Diagnosis field'),
        'NGAY_KQ': (1820, 322, 'Result date field'),
        'NGAY_BDTH': (1820, 299, 'Start implementation date field'),
        'NGAY_CD': (1820, 278, 'Diagnosis date field'),
        'BSCD': (1820, 256, 'Diagnosing doctor field'),
        'NGAY_KET_THUC': (275, 151, 'End date field'),
        'NGAY_BAT_DAU': (153, 151, 'Start date field'),
        'CHO_THUC_HIEN': (126, 133, 'Pending execution tab'),
        'DA_THUC_HIEN': (250, 133, 'Completed execution tab'),
        'RELOAD': (390, 141, 'Reload button'),
    }


def initialize_default_coordinates():
    """Initialize coordinates table with default values if empty."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Check if table has any data
    cursor.execute("SELECT COUNT(*) FROM coordinates")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Insert default coordinates
        default_coords = get_default_coordinates()
        for name, (x, y, description) in default_coords.items():
            cursor.execute("""
                INSERT INTO coordinates (name, x, y, description)
                VALUES (?, ?, ?, ?)
            """, (name, x, y, description))
        
        conn.commit()
    
    conn.close()


def get_coordinate(name):
    """Get a specific coordinate by name. Returns tuple (x, y) or None."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT x, y FROM coordinates WHERE name = ?", (name,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return (row[0], row[1])
    return None


def get_all_coordinates():
    """Get all coordinates. Returns dict with name as key and (x, y, description) as value."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, x, y, description FROM coordinates ORDER BY name")
    rows = cursor.fetchall()
    conn.close()
    
    coords = {}
    for row in rows:
        coords[row[0]] = (row[1], row[2], row[3] if row[3] else "")
    return coords


def save_coordinate(name, x, y, description=""):
    """Save or update a coordinate."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO coordinates (name, x, y, description)
        VALUES (?, ?, ?, ?)
    """, (name, x, y, description))
    conn.commit()
    conn.close()


def save_all_coordinates(coords_dict):
    """Save multiple coordinates at once. coords_dict format: {name: (x, y, description)}"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    for name, (x, y, description) in coords_dict.items():
        cursor.execute("""
            INSERT OR REPLACE INTO coordinates (name, x, y, description)
            VALUES (?, ?, ?, ?)
        """, (name, x, y, description))
    
    conn.commit()
    conn.close()


def restore_default_coordinates():
    """Restore all coordinates to default values."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Delete all existing coordinates
    cursor.execute("DELETE FROM coordinates")
    
    # Insert default coordinates
    default_coords = get_default_coordinates()
    for name, (x, y, description) in default_coords.items():
        cursor.execute("""
            INSERT INTO coordinates (name, x, y, description)
            VALUES (?, ?, ?, ?)
        """, (name, x, y, description))
    
    conn.commit()
    conn.close()


if __name__ == "__main__":
    # Initialize database
    initialize_database()
    print("Database initialized successfully")
