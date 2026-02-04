bs_mapper = {
    0: "Trần Thị Thu Hiền", # Thu 2
    1: "Trần Thị Thu Hiền", # Thu 3
    2: "Trần Thị Thu Hiền", # Thu 4
    3: "Trần Thị Thu Hiền", # Thu 5
    4: "Trần Thị Thu Hiền", # Thu 6
    5: "Trần Thị Thu Hiền", # Thu 7
    6: "Bùi Tá Việt Trị" # CN
}

bs_mapper_new = {
    0: "Trần Thị Diệu Hoà", # Thu 2
    1: "Trần Thị Diệu Hoà", # Thu 3
    2: "Trần Thị Diệu Hoà", # Thu 4
    3: "Trần Thị Diệu Hoà", # Thu 5
    4: "Trần Thị Diệu Hoà", # Thu 6
    5: "Trần Thị Diệu Hoà", # Thu 7
    6: "Bùi Tá Việt Trị" # CN
}

thu_thuat_dur_mapper = {
    "điện": 30,
    # "thuỷ": 30,
    "thủy": 30,
    "xoa": 30,
    "kéo": 20,
    "giác": 20,
    "cứu": 20,
}
thu_thuat_ability_mapper = {
    "điện": "ys",
    # "thuỷ": 'bs',
    "thủy": "bs",
    "xoa": "ys",
    "kéo": "bs",
    "giác": "ys",
    "cứu": "ys",
}

# Auto-scheduling time slots.
# Provide times as "HH:MM". By default these are "Ngay CD" times.
# If you supply "Ngay BD TH" times instead, set AUTO_SCHEDULE_TIME_SLOTS_KIND = "BD_TH".
AUTO_SCHEDULE_TIME_SLOTS_KIND = "CD"
AUTO_SCHEDULE_TIME_SLOTS = [
    # "07:00",
]

DICH_VU_THU_THUAT = [
    (700,152),
    (700,172),
    (700,193),
    (700,215)
]

# ===== Coordinate Configuration =====
# Load coordinates from database, with hardcoded defaults as fallback

def load_coordinates_from_db():
    """Load coordinates from database. Returns dict with coordinate names as keys and (x, y) tuples as values."""
    try:
        from database import get_all_coordinates, get_default_coordinates
        
        coords = get_all_coordinates()
        
        # If no coordinates in database, use defaults
        if not coords:
            default_coords = get_default_coordinates()
            # Convert from (x, y, description) to (x, y)
            return {name: (x, y) for name, (x, y, desc) in default_coords.items()}
        
        # Convert from (x, y, description) to (x, y)
        return {name: (x, y) for name, (x, y, desc) in coords.items()}
    except Exception as e:
        print(f"Error loading coordinates from database: {e}")
        # Fallback to hardcoded defaults
        return {
            'ID_BOX': (78, 191),
            'LUU': (537, 966),
            'TIEP': (464, 964),
            'SUA': (670, 966),
            'PATIENT_ROW': (181, 249),
            'BSCD_NGUOI_DAU_TIEN': (1595, 348),
            'CCHN_NGUOI_DAU_TIEN': (1624, 444),
            'CCHN': (1820, 344),
            'NGAY_KQ': (1820, 322),
            'NGAY_BDTH': (1820, 299),
            'NGAY_CD': (1820, 278),
            'BSCD': (1820, 256),
            'NGAY_KET_THUC': (275, 151),
            'NGAY_BAT_DAU': (153, 151),
            'CHO_THUC_HIEN': (126, 133),
            'DA_THUC_HIEN': (250, 133),
            'RELOAD': (390, 141),
        }

# Load coordinates
_coords = load_coordinates_from_db()

# Export as module-level constants for backward compatibility
ID_BOX = _coords.get('ID_BOX', (78, 191))
LUU = _coords.get('LUU', (537, 966))
TIEP = _coords.get('TIEP', (464, 964))
SUA = _coords.get('SUA', (670, 966))
PATIENT_ROW = _coords.get('PATIENT_ROW', (181, 249))
BSCD_NGUOI_DAU_TIEN = _coords.get('BSCD_NGUOI_DAU_TIEN', (1595, 348))
CCHN_NGUOI_DAU_TIEN = _coords.get('CCHN_NGUOI_DAU_TIEN', (1624, 444))
CCHN = _coords.get('CCHN', (1820, 344))
NGAY_KQ = _coords.get('NGAY_KQ', (1820, 322))
NGAY_BDTH = _coords.get('NGAY_BDTH', (1820, 299))
NGAY_CD = _coords.get('NGAY_CD', (1820, 278))
BSCD = _coords.get('BSCD', (1820, 256))
NGAY_KET_THUC = _coords.get('NGAY_KET_THUC', (275, 151))
NGAY_BAT_DAU = _coords.get('NGAY_BAT_DAU', (153, 151))
CHO_THUC_HIEN = _coords.get('CHO_THUC_HIEN', (126, 133))
DA_THUC_HIEN = _coords.get('DA_THUC_HIEN', (250, 133))
RELOAD = _coords.get('RELOAD', (390, 141))

def reload_coordinates():
    """Reload coordinates from database. Call this after coordinates are updated."""
    global ID_BOX, LUU, TIEP, SUA, PATIENT_ROW, BSCD_NGUOI_DAU_TIEN, CCHN_NGUOI_DAU_TIEN
    global CCHN, NGAY_KQ, NGAY_BDTH, NGAY_CD, BSCD, NGAY_KET_THUC, NGAY_BAT_DAU
    global CHO_THUC_HIEN, DA_THUC_HIEN, RELOAD, _coords
    
    _coords = load_coordinates_from_db()
    
    ID_BOX = _coords.get('ID_BOX', (78, 191))
    LUU = _coords.get('LUU', (537, 966))
    TIEP = _coords.get('TIEP', (464, 964))
    SUA = _coords.get('SUA', (670, 966))
    PATIENT_ROW = _coords.get('PATIENT_ROW', (181, 249))
    BSCD_NGUOI_DAU_TIEN = _coords.get('BSCD_NGUOI_DAU_TIEN', (1595, 348))
    CCHN_NGUOI_DAU_TIEN = _coords.get('CCHN_NGUOI_DAU_TIEN', (1624, 444))
    CCHN = _coords.get('CCHN', (1820, 344))
    NGAY_KQ = _coords.get('NGAY_KQ', (1820, 322))
    NGAY_BDTH = _coords.get('NGAY_BDTH', (1820, 299))
    NGAY_CD = _coords.get('NGAY_CD', (1820, 278))
    BSCD = _coords.get('BSCD', (1820, 256))
    NGAY_KET_THUC = _coords.get('NGAY_KET_THUC', (275, 151))
    NGAY_BAT_DAU = _coords.get('NGAY_BAT_DAU', (153, 151))
    CHO_THUC_HIEN = _coords.get('CHO_THUC_HIEN', (126, 133))
    DA_THUC_HIEN = _coords.get('DA_THUC_HIEN', (250, 133))
    RELOAD = _coords.get('RELOAD', (390, 141))



import json
import os

def load_staff_config(filename):
    """Load staff configuration from JSON file (deprecated - kept for fallback)."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, filename)
        if os.path.exists(file_path):
            # Try multiple encodings
            for enc in ['utf-8', 'utf-8-sig', 'cp1252', 'cp1258']:
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        return json.load(f)
                except UnicodeDecodeError:
                    continue
                except json.JSONDecodeError:
                    continue
            
            # If we get here, no encoding worked or file is not valid JSON
            print(f"Warning: Could not decode {filename} with any standard encoding.")
            return {}
            
        return {}
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return {}

def load_staff_from_database():
    """Load staff configuration from database."""
    try:
        from database import get_staff_by_group
        
        staff_p1_p3 = get_staff_by_group(1)
        staff_p2 = get_staff_by_group(2)
        
        # If database is empty, try loading from JSON files as fallback
        if not staff_p1_p3 and not staff_p2:
            print("Database empty, loading staff from JSON files as fallback")
            staff_p1_p3 = load_staff_config("staff_group_1.json")
            staff_p2 = load_staff_config("staff_group_2.json")
        
        return staff_p1_p3, staff_p2
    except Exception as e:
        print(f"Error loading staff from database: {e}")
        # Fallback to JSON files
        staff_p1_p3 = load_staff_config("staff_group_1.json")
        staff_p2 = load_staff_config("staff_group_2.json")
        return staff_p1_p3, staff_p2

# Load staff groups from database
staff_p1_p3, staff_p2 = load_staff_from_database()

# Create merged map for backward compatibility
map_ys_bs = {**staff_p1_p3, **staff_p2}

# If loading failed completely, use hardcoded defaults (fail-safe)
# IMPORTANT: Keep groups SEPARATE to avoid duplication in UI
if not staff_p1_p3:
    staff_p1_p3 = {
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

if not staff_p2:
    staff_p2 = {
        "hiền": "Trần Thị Thu Hiền",
        "hoà": "Trần Thị Diệu Hoà",
        "anh": "Nguyễn Duy Anh",
        "trị": "Bùi Tá Việt Trị",
    }

# Rebuild merged map if fallback was used
if not map_ys_bs:
    map_ys_bs = {**staff_p1_p3, **staff_p2}

def reload_staff():
    """Reload staff from database. Call this after staff changes."""
    global staff_p1_p3, staff_p2, map_ys_bs
    
    staff_p1_p3, staff_p2 = load_staff_from_database()
    map_ys_bs = {**staff_p1_p3, **staff_p2}
    
    return staff_p1_p3, staff_p2, map_ys_bs

# # List of disabled/excluded staff members (lowercase short names as keys in map_ys_bs)
# # Staff in this list will not appear in manual entry and will cause errors during automation
# disabled_staff = ["diệu"]
