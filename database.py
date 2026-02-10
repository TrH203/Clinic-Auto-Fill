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
    
    # Staff table for managing staff members
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_name TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            group_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    
    # Initialize default coordinates if table is empty
    initialize_default_coordinates()
    
    # Initialize default staff if table is empty  
    initialize_default_staff()



# ===== Manual Entries Functions =====

def save_manual_entry_to_db(patient_id, procedures, staff, appointment_date, appointment_time, notes=""):
    """Saves a manual entry to the database."""
    ensure_tables_exist()
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
    ensure_tables_exist()
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


def delete_old_manual_entries(days=30):
    """
    Deletes manual entries older than the specified number of days based on created_at timestamp.
    Default is 30 days.
    Returns the number of deleted entries.
    """
    from datetime import datetime, timedelta
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Calculate the cutoff datetime
    cutoff_datetime = datetime.now() - timedelta(days=days)
    cutoff_str = cutoff_datetime.strftime("%Y-%m-%d %H:%M:%S")
    
    # Delete entries older than cutoff based on created_at
    cursor.execute("""
        DELETE FROM manual_entries 
        WHERE created_at < ?
    """, (cutoff_str,))
    
    deleted_count = cursor.rowcount
    
    conn.commit()
    conn.close()
    
    return deleted_count


# ===== Staff Management Functions =====

def initialize_default_staff():
    """Initialize staff table with default values from JSON files if empty."""
    import json
    import os
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Check if table has any data
    cursor.execute("SELECT COUNT(*) FROM staff")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Load default staff from JSON files
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Group 1 staff
        group1_file = os.path.join(current_dir, "staff_group_1.json")
        if os.path.exists(group1_file):
            try:
                with open(group1_file, 'r', encoding='utf-8') as f:
                    group1_data = json.load(f)
                    for short_name, full_name in group1_data.items():
                        cursor.execute("""
                            INSERT INTO staff (short_name, full_name, group_id)
                            VALUES (?, ?, ?)
                        """, (short_name, full_name, 1))
            except Exception as e:
                print(f"Error loading Group 1 staff: {e}")
        
        # Group 2 staff
        group2_file = os.path.join(current_dir, "staff_group_2.json")
        if os.path.exists(group2_file):
            try:
                with open(group2_file, 'r', encoding='utf-8') as f:
                    group2_data = json.load(f)
                    for short_name, full_name in group2_data.items():
                        cursor.execute("""
                            INSERT INTO staff (short_name, full_name, group_id)
                            VALUES (?, ?, ?)
                        """, (short_name, full_name, 2))
            except Exception as e:
                print(f"Error loading Group 2 staff: {e}")
        
        # If JSON files don't exist, use hardcoded defaults
        if cursor.execute("SELECT COUNT(*) FROM staff").fetchone()[0] == 0:
            default_staff_1 = {
                "duy": "Nguyễn Văn Duy",
                "lya": "H' Lya Niê",
                "quân": "Lê Văn Quân",
                "khoái": "Nguyễn Công Khoái",
                "thịnh": "Nguyễn Văn Thịnh",
                "hạnh": "Nguyễn Hữu Hạnh",
                "diệu": "Nguyễn Thị Diệu",
                "lực": "Lê Đức Lực",
                "thơ": "Lê Thị Ngọc Thơ",
                "nhẹ": "H' Nhẹ Niê",
                "trúc": "Lê Ngọc Trúc",
            }
            
            default_staff_2 = {
                "hiền": "Trần Thị Thu Hiền",
                "hoà": "Trần Thị Diệu Hoà",
                "anh": "Nguyễn Duy Anh",
                "trị": "Bùi Tá Việt Trị",
            }
            
            for short_name, full_name in default_staff_1.items():
                cursor.execute("""
                    INSERT INTO staff (short_name, full_name, group_id)
                    VALUES (?, ?, ?)
                """, (short_name, full_name, 1))
            
            for short_name, full_name in default_staff_2.items():
                cursor.execute("""
                    INSERT INTO staff (short_name, full_name, group_id)
                    VALUES (?, ?, ?)
                """, (short_name, full_name, 2))
        
        conn.commit()
    
    conn.close()


def get_all_staff():
    """Get all staff members grouped by group_id."""
    ensure_tables_exist()
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT short_name, full_name, group_id
        FROM staff
        ORDER BY group_id, short_name
    """)
    rows = cursor.fetchall()
    conn.close()
    
    staff = []
    for row in rows:
        staff.append({
            'short_name': row[0],
            'full_name': row[1],
            'group_id': row[2]
        })
    return staff


def get_staff_by_group(group_id):
    """Get staff members for a specific group."""
    ensure_tables_exist()
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT short_name, full_name
        FROM staff
        WHERE group_id = ?
        ORDER BY short_name
    """, (group_id,))
    rows = cursor.fetchall()
    conn.close()
    
    # Return as dictionary {short_name: full_name}
    return {row[0]: row[1] for row in rows}


def add_staff(short_name, full_name, group_id):
    """Add a new staff member."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO staff (short_name, full_name, group_id)
            VALUES (?, ?, ?)
        """, (short_name.strip().lower(), full_name.strip(), group_id))
        conn.commit()
        staff_id = cursor.lastrowid
        conn.close()
        return staff_id
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError(f"Staff member with short name '{short_name}' already exists")


def delete_staff(short_name):
    """Delete a staff member by short_name."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM staff WHERE short_name = ?", (short_name.lower(),))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted > 0


def get_staff_dict():
    """Get all staff as a merged dictionary for backward compatibility."""
    staff_1 = get_staff_by_group(1)
    staff_2 = get_staff_by_group(2)
    return {**staff_1, **staff_2}


# ===== App Settings Functions =====

def ensure_tables_exist():
    """Ensure all required tables exist. Call this before any database operation."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Create app_settings table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # Create doctor_leaves table if not exists
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
    
    # Create coordinates table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS coordinates (
            name TEXT PRIMARY KEY,
            x INTEGER NOT NULL,
            y INTEGER NOT NULL,
            description TEXT
        )
    """)
    
    # Create staff table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_name TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            group_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create manual_entries table if not exists
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
    
    # Create weekly_leaves table if not exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            staff_short_name TEXT NOT NULL,
            day_of_week INTEGER NOT NULL,
            session TEXT NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()


def get_disabled_staff():
    """Get list of disabled staff from database."""
    ensure_tables_exist()
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
    ensure_tables_exist()
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
    return True

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



def get_last_used_procedures():
    """Get the last used procedures from database."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM app_settings WHERE key = 'last_used_procedures'")
    row = cursor.fetchone()
    conn.close()
    
    if row:
        import json
        return json.loads(row[0])
    return []  # Return empty list if no previous procedures


def set_last_used_procedures(procedures_list):
    """Save the last used procedures to database.
    
    Args:
        procedures_list: List of procedure names (e.g., ["điện", "thuỷ", "laser", "kim"])
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    import json
    value = json.dumps(procedures_list, ensure_ascii=False)
    
    cursor.execute("""
        INSERT OR REPLACE INTO app_settings (key, value)
        VALUES ('last_used_procedures', ?)
    """, (value,))
    
    conn.commit()
    conn.close()


# ===== Doctor Leave Functions =====


def add_doctor_leave(staff_short_name, leave_date, session, reason=""):
    """Add a doctor leave record."""
    ensure_tables_exist()
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
    ensure_tables_exist()
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
    Checks both specific date leaves and weekly recurring leaves.
    Returns (is_available, reason)
    """
    ensure_tables_exist()
    from datetime import datetime
    
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
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Check specific date leaves
    cursor.execute("""
        SELECT session FROM doctor_leaves
        WHERE staff_short_name = ? AND trim(leave_date) = ?
    """, (staff_short_name, date_str.strip()))
    
    result = cursor.fetchone()
    
    if result:
        leave_session = result[0]
        if leave_session == "full_day":
            conn.close()
            return (False, "Nghỉ cả ngày")
        elif leave_session == appt_session:
            session_vn = "Nghỉ sáng" if appt_session == "morning" else "Nghỉ chiều"
            conn.close()
            return (False, session_vn)
    
    # Check weekly recurring leaves
    try:
        # Parse date to get day of week (Monday=0, Sunday=6)
        if '-' in date_str and len(date_str.split('-')[0]) == 4:
            # Format: YYYY-MM-DD
            date_obj = datetime.strptime(date_str.strip(), "%Y-%m-%d")
        else:
            # Format: DD-MM-YYYY
            date_obj = datetime.strptime(date_str.strip(), "%d-%m-%Y")
        
        day_of_week = date_obj.weekday()  # Monday=0, Sunday=6
        
        cursor.execute("""
            SELECT session FROM weekly_leaves
            WHERE staff_short_name = ? AND day_of_week = ?
        """, (staff_short_name, day_of_week))
        
        weekly_result = cursor.fetchone()
        
        if weekly_result:
            weekly_session = weekly_result[0]
            day_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]
            day_name = day_names[day_of_week]
            
            if weekly_session == "full_day":
                conn.close()
                return (False, f"Nghỉ {day_name} hằng tuần")
            elif weekly_session == appt_session:
                session_vn = "sáng" if appt_session == "morning" else "chiều"
                conn.close()
                return (False, f"Nghỉ {day_name} {session_vn} hằng tuần")
    except:
        pass
    
    conn.close()
    return (True, "")


# ===== Weekly Leave Functions =====

def add_weekly_leave(staff_short_name, day_of_week, session, reason=""):
    """Add a weekly recurring leave record.
    
    Args:
        staff_short_name: Staff identifier
        day_of_week: 0=Monday, 1=Tuesday, ..., 6=Sunday
        session: 'morning', 'afternoon', or 'full_day'
        reason: Optional reason text
    """
    ensure_tables_exist()
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO weekly_leaves (staff_short_name, day_of_week, session, reason)
        VALUES (?, ?, ?, ?)
    """, (staff_short_name, day_of_week, session, reason))
    conn.commit()
    leave_id = cursor.lastrowid
    conn.close()
    return leave_id


def get_all_weekly_leaves():
    """Get all weekly leave records."""
    ensure_tables_exist()
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, staff_short_name, day_of_week, session, reason
        FROM weekly_leaves
        ORDER BY staff_short_name, day_of_week
    """)
    rows = cursor.fetchall()
    conn.close()
    
    leaves = []
    for row in rows:
        leaves.append({
            'id': row[0],
            'staff_short_name': row[1],
            'day_of_week': row[2],
            'session': row[3],
            'reason': row[4] if row[4] else ""
        })
    return leaves


def delete_weekly_leave(leave_id):
    """Delete a weekly leave record."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM weekly_leaves WHERE id = ?", (leave_id,))
    conn.commit()
    conn.close()


def get_weekly_leaves_for_staff(staff_short_name):
    """Get weekly leaves for a specific staff member."""
    ensure_tables_exist()
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT day_of_week, session FROM weekly_leaves
        WHERE staff_short_name = ?
    """, (staff_short_name,))
    rows = cursor.fetchall()
    conn.close()
    return rows  # List of (day_of_week, session) tuples


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
    ensure_tables_exist()
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
