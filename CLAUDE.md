# Clinic Auto-Fill - Project Guide

## Overview

Desktop automation tool for a medical clinic. Users input patient appointment data (via CSV import or manual entry), the app parses it into a standardized format, then automates data entry into a target clinic application using mouse/keyboard control (pyautogui + pywinauto).

## Architecture

```
interface.py          # Main GUI (Tkinter) - entry point, AutomationGUI class
├── handle_data.py    # Data parsing: CSV → standardized dict, manual input → dict, validation
├── tool.py           # Automation engine: mouse clicks, keyboard input, OCR text extraction
├── config.py         # Coordinates, staff mappings, procedure configs (loads from DB)
├── database.py       # SQLite (app_data.db): manual entries, staff, coordinates, settings, leaves
├── manual_entry.py   # ManualEntryDialog - GUI for manual patient data input
├── config_dialog.py  # ConfigDialog - staff management, leave scheduling, disabled staff
├── coordinate_config_dialog.py  # UI coordinate configuration with capture
├── updater.py        # Auto-update via GitHub releases
└── export_manual_entries.py     # Export DB entries to CSV
```

## Data Flow

1. **Input**: CSV file (`;` delimited) or manual entry dialog
2. **Parse** (`handle_data.py`):
   - CSV: `read_data()` → groups rows by patient, calculates procedure times, maps staff
   - Manual: `create_data_from_manual_input()` → same output format
3. **Standardized format** (list of dicts):
   ```python
   {
     "id": "patient_id",
     "isFirst": True/False,  # first visit or follow-up
     "ngay": "DD-MM-YYYY",
     "thu_thuats": [          # list of procedures
       {
         "Ten": "procedure_name",
         "BS CD": "doctor_name",
         "Ngay CD": "DD-MM-YYYY{SPACE}HH:MM",
         "Ngay BD TH": "DD-MM-YYYY{SPACE}HH:MM",
         "Ngay KQ": "DD-MM-YYYY{SPACE}HH:MM",
         "Nguoi Thuc Hien": "staff_full_name"
       }
     ]
   }
   ```
4. **Automation** (`tool.py` + `interface.py:run_automation()`):
   - Connects to target window via `pywinauto`
   - For each patient: clicks coordinates, types dates/IDs, fills procedure data
   - Uses OCR (`pytesseract`) to read on-screen text for procedure matching
   - Supports pause, resume, emergency stop (F12)

## Key Concepts

### Staff Groups
- **Group 1** (`staff_p1_p3`): Technicians/nurses - positions 1 & 3 in staff assignment
- **Group 2** (`staff_p2`): Doctors - position 2 in staff assignment
- Staff stored in `staff` table in SQLite, with JSON fallback (`staff_group_1.json`, `staff_group_2.json`)

### Procedures (Thu Thuat)
- Types: `dien` (electrical), `thuy` (hydro), `xoa` (massage), `keo` (traction), `giac` (cupping), `cuu` (moxibustion)
- Each has a duration (`thu_thuat_dur_mapper`) and ability type (`thu_thuat_ability_mapper`: "ys" or "bs")
- "bs" procedures assigned to Group 2 staff, "ys" to Group 1

### Coordinates
- UI element positions stored in DB table `coordinates`
- Configurable via `coordinate_config_dialog.py` with mouse capture
- Used by `tool.py` for click targets (buttons, input fields, dropdowns)

### Date Handling
- Arrow mode: types date parts separated by arrow keys (for date picker controls)
- Normal mode: types full date string with Ctrl+A replacement
- Format: `DD-MM-YYYY{SPACE}HH:MM` (the `{SPACE}` is literal for pywinauto send_keys)

## Tech Stack

- **Python 3.10** with Tkinter GUI
- **pywinauto** + **pyautogui**: Window automation, mouse/keyboard control
- **pytesseract** + **opencv-python**: OCR for reading screen text
- **pandas**: CSV parsing
- **SQLite**: Local database (`app_data.db`)
- **PyInstaller**: Builds single `.exe` via `ClinicAutoTool.spec`

## Build & Run

```bash
# Development
pip install -r requirements.txt
python interface.py

# Build executable
pyinstaller ClinicAutoTool.spec
# Output: dist/ClinicAutoTool.exe
```

## Database Schema (app_data.db)

- `manual_entries`: patient_id, procedures, staff, appointment_date/time, notes
- `staff`: short_name, full_name, group_id (1 or 2)
- `coordinates`: name, x, y, description
- `doctor_leaves`: staff_short_name, leave_date, session
- `weekly_leaves`: staff_short_name, day_of_week, session
- `app_settings`: key-value store (window_title, arrow_mode, disabled_staff, etc.)

## Important Notes

- The `ai/` directory is a separate feature (auto-scheduling) - not part of the core app flow
- Vietnamese text is used throughout (staff names, procedure names, UI labels)
- `bs_mapper` / `bs_mapper_new` selects diagnosing doctor based on day-of-week and year (>= 2026 uses new mapper)
- Validation (`validate_all_data`) checks for time conflicts among Group 1 staff
- Auto-save/load: data persisted to `auto_save.csv` on close, reloaded on startup
- GitHub Actions CI runs tests on `staging` branch pushes
