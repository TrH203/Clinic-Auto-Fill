# Clinic Auto-Fill Tool - User Guide

## New Features

### 1. Manual Data Entry

You can now input patient data directly in the application without needing a CSV file!

#### How to Use Manual Entry:

1. **Click "Manual Entry"** button in the Data File section
2. **Fill in the form:**
   - Patient ID (required)
   - Appointment Date (use calendar picker)
   - Appointment Time (hours and minutes)
   - Select Procedures (check one or more)
   - Select Staff Members (choose 1-3 staff in order)
   - Add optional notes
3. **Click "Save & Add to Queue"**
4. The entry is now added to your automation queue!

#### Benefits:
- ✅ No need to create CSV files for single entries
- ✅ Data validation ensures correctness
- ✅ Saved to database for future reference
- ✅ Works alongside CSV imports

### 2. Enhanced Auto-Update System

The app now has improved update management:

#### Features:
- **Semantic Version Comparison** - Properly handles version numbers
- **Changelog Display** - See what's new before updating
- **Automatic Backup** - Your current version is backed up before updating
- **Rollback on Failure** - Automatically restores if update fails
- **Update History** - Track all update attempts

#### How It Works:
1. App checks for updates on startup
2. If update available, you'll see "Update Available!" button
3. Click to view release notes and changelog
4. Choose to update or skip
5. If you update, your current version is backed up
6. New version downloads and installs automatically
7. App relaunches with new version

---

## Using Both CSV and Manual Data

The application supports using both CSV files and manual entries together:

1. **Load CSV file** - Click "Browse CSV" and select your file
2. **Add manual entries** - Click "Manual Entry" to add individual appointments
3. **View combined data** - The log shows total: CSV + Manual
4. **Run automation** - Processes all data in order

---

## Data Storage

### CSV Data
- Loaded from file each time
- Not stored permanently in the app

### Manual Entries
- Saved to SQLite database (`app_data.db`)
- Persists between app sessions
- Can be loaded and reused

---

## Tips & Best Practices

### Manual Data Entry

✅ **DO:**
- Double-check Patient ID before saving
- Verify appointment date and time
- Select staff in the correct order
- Use notes for special instructions

❌ **DON'T:**
- Leave required fields empty
- Use invalid date formats
- Select procedures without selecting staff

### Updates

✅ **DO:**
- Read release notes before updating
- Update during off-peak hours
- Keep backups of important data

❌ **DON'T:**
- Update during active automation
- Ignore update notifications indefinitely
- Delete backup files manually

---

## Troubleshooting

### Manual Entry Issues

**Problem:** "Unknown procedure" error
- **Solution:** Check spelling of procedure name
- Make sure procedure is in the config

**Problem:** "Unknown staff member" error
- **Solution:** Check spelling of staff name
- Staff name must be in the config

**Problem:** Dialog doesn't open
- **Solution:** Check error log
- Ensure `tkcalendar` library is installed

### Update Issues

**Problem:** Update check fails
- **Solution:** Check internet connection
- Verify firewall isn't blocking requests
- GitHub API may have rate limits

**Problem:** Update download fails
- **Solution:** Check available disk space
- Ensure antivirus isn't blocking download
- Try manual download from GitHub releases

**Problem:** App won't start after update
- **Solution:** Look for backup file (`.backup_v*`)
- Rename backup to original filename
- Contact support if issue persists

---

## Keyboard Shortcuts

- **F12** - Emergency Stop (during automation)
- **Escape** - Emergency Stop (alternative)

---

## File Locations

- **Database:** `app_data.db` (same folder as executable)
- **Manual Data:** Stored in database
- **Backups:** `*.backup_v<version>` (same folder as executable)
- **Logs:** Displayed in Activity Log panel

---

## Support

For issues or questions:
1. Check the Activity Log for error messages
2. Review this documentation
3. Check VERSION_MANAGEMENT.md for update issues
4. Contact the development team
5. Report bugs on GitHub

---

## What's Next?

Stay tuned for future updates:
- Import manual entries from database
- Edit existing manual entries
- Export combined data to CSV
- Batch import from Excel
- Update scheduling

Happy automating! 🚀
