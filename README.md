# Clinic Auto-Fill Tool

A desktop automation application for medical clinic appointment data entry with auto-update capabilities.

## Features

### Core Features
- 🤖 **Automated Data Entry** - Automatically fills medical appointment forms
- 📊 **CSV Import** - Load patient data from CSV files
- ✏️ **Manual Entry** - Input data directly through intuitive dialog
- 🔄 **Auto-Update** - Automatic updates via GitHub releases
- 💾 **Database Storage** - Persistent storage for manual entries

### Version Management
- ✅ Semantic versioning with proper comparison
- 📝 Changelog display before updates
- 💾 Automatic backup before updates
- 🔙 Automatic rollback on failure
- 📜 Update history tracking

### User Experience
- 🎯 Easy-to-use GUI built with Tkinter
- 🛑 Emergency stop with F12 hotkey
- ⏸️ Pause/Resume automation
- 📋 Real-time activity logging
- 🔔 Progress tracking

## Getting Started

### Installation

1. Download the latest release from [GitHub Releases](https://github.com/TrH203/Clinic-Auto-Fill/releases)
2. Run `ClinicAutoTool.exe`
3. The application will auto-update when new versions are available
4. Install https://github.com/UB-Mannheim/tesseract/wiki


### Usage

1. **Load Data:**
   - Click "Browse CSV" to import data from CSV file, OR
   - Click "Manual Entry" to input data directly

2. **Connect to Application:**
   - Click "Connect to Application"
   - Ensure the target application is running

3. **Run Automation:**
   - Click "Start Automation"
   - Monitor progress in Activity Log
   - Use F12 for emergency stop if needed

## Documentation

- [User Guide](USER_GUIDE.md) - How to use the application
- [Version Management](VERSION_MANAGEMENT.md) - How to release updates and manage versions
- [Implementation Plan](/.gemini/antigravity/brain/*/implementation_plan.md) - Technical details

## Development

### Requirements

```bash
pip install -r requirements.txt
```

### Building

**Using spec file (Recommended):**
```bash
pyinstaller ClinicAutoTool.spec
```

**Or direct command:**
```bash
pyinstaller --onefile --windowed --name="ClinicAutoTool" \
  --hidden-import=pandas._libs.hashtable \
  --hidden-import=packaging.version \
  interface.py
```

The executable will be in the `dist/` folder.

## Version History

Current Version: Stored in database (`app_data.db`)

See [Releases](https://github.com/TrH203/Clinic-Auto-Fill/releases) for version history and changelogs.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## License

© 2024 - All rights reserved
