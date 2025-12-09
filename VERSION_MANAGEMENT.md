```

### Features

- **Semantic Version Comparison** - Properly compares versions like 1.10.0 vs 1.9.0
- **Changelog Display** - Shows release notes before updating
- **Automatic Backup** - Creates backup before replacing executable
- **Rollback on Failure** - Restores from backup if update fails
- **Update History** - Logs all update attempts in database
- **Backup Cleanup** - Keeps only last 3 backups to save space

---

## Releasing a New Version

### Step 1: Prepare the Release

1. **Update Version Number**
   
   Create or update the `VERSION` file in the project root:
   ```
   1.2.0
   ```
   
   Use [Semantic Versioning](https://semver.org/):
   - **MAJOR** (1.x.x): Breaking changes
   - **MINOR** (x.1.x): New features, backward compatible
   - **PATCH** (x.x.1): Bug fixes, backward compatible

2. **Test Thoroughly**
   - Test all features on a clean machine
   - Verify CSV import works
   - Test manual data entry
   - Test automation flow
   - Check update mechanism (optional - test with a dummy release)

### Step 2: Build the Executable

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Build with PyInstaller:**
   ```bash
   pyinstaller --onefile --windowed --name="ClinicAutoTool" interface.py
   ```

3. **Test the executable:**
   - Copy to a clean directory
   - Run the exe
   - Verify it initializes database correctly
   - Test basic functionality

### Step 3: Create GitHub Release

1. **Commit and tag:**
   ```bash
   git add .
   git commit -m "Release version 1.2.0"
   git tag v1.2.0
   git push origin main
   git push origin v1.2.0
   ```

2. **Create Release on GitHub:**
   - Go to https://github.com/TrH203/Clinic-Auto-Fill/releases
   - Click "Draft a new release"
   - Select the tag you just created (v1.2.0)
   - Set release title: "Version 1.2.0"
   
3. **Write Release Notes:**
   ```markdown
   ## What's New
   
   ### Features
   - ✨ Added manual data entry dialog
   - 🔄 Improved auto-update with changelog display
   - 💾 Enhanced data persistence with database storage
   
   ### Improvements
   - ⚡ Better version comparison logic
   - 🛡️ Automatic backup before updates
   - 📊 Merge CSV and manual data seamlessly
   
   ### Bug Fixes
   - 🐛 Fixed date parsing issue
   - 🔧 Improved error handling
   
   ## Installation
   
   Download the executable below and run it. The app will auto-update on next startup.
   ```

4. **Upload the Executable:**
   - Drag and drop `ClinicAutoTool.exe` from `dist/` folder
   - Ensure the filename is clear (e.g., `ClinicAutoTool-v1.2.0.exe`)

5. **Publish Release:**
   - Click "Publish release"
   - The update will now be available to all users on next app startup

---

## Best Practices

### Version Numbering

✅ **DO:**
- Use semantic versioning (MAJOR.MINOR.PATCH)
- Increment MAJOR for breaking changes
- Increment MINOR for new features
- Increment PATCH for bug fixes
- Always use 3 numbers (e.g., 1.0.0, not 1.0)

❌ **DON'T:**
- Skip versions
- Use dates as versions (e.g., 2024.12.8)
- Use text in versions (e.g., 1.0-beta)

### Release Notes

✅ **DO:**
- Be clear and concise
- Group changes by category (Features, Improvements, Bug Fixes)
- Use emojis for visual appeal
- Mention breaking changes prominently
- Include installation instructions

❌ **DON'T:**
- Use technical jargon
- Leave release notes empty
- List every single commit
- Forget to mention breaking changes

### Testing

✅ **DO:**
- Test on a clean machine (no development environment)
- Verify auto-update works (test with a dummy release)
- Check database migrations
- Test with real data
- Keep backups of production data

❌ **DON'T:**
- Release without testing
- Test only on development machine
- Skip database migration testing
- Rush releases

### Deployment Timing

✅ **DO:**
- Release during off-peak hours
- Inform users of upcoming updates
- Keep old versions available for rollback
- Monitor for issues after release
- Have a rollback plan

❌ **DON'T:**
- Release during critical business hours
- Force updates immediately
- Delete old releases
- Ignore user feedback after release

---

## Troubleshooting

### Users Not Seeing Updates

**Possible causes:**
1. GitHub API rate limit reached (60 req/hour for unauthenticated)
2. No internet connection
3. GitHub is down
4. Firewall blocking requests

**Solutions:**
- Check GitHub API status
- Ask users to manually check for updates
- Provide direct download link

### Update Fails

**Possible causes:**
1. Insufficient permissions
2. Antivirus blocking
3. File in use
4. Corrupted download

**Solutions:**
- Run as administrator
- Temporarily disable antivirus
- Close all instances of the app
- Re-download the file

### Rollback Needed

If an update causes issues:

1. **Automatic Rollback:** The updater attempts this automatically on failure
2. **Manual Rollback:** 
   - Find backup file (e.g., `ClinicAutoTool.exe.backup_v1.1.0`)
   - Rename to `ClinicAutoTool.exe`
   - Run the application

---

## Alternative Update Approaches

If the current GitHub-based approach doesn't meet your needs, consider:

### 1. Self-Hosted Updates

Host updates on your own server or cloud storage (AWS S3, Google Cloud Storage):
- **Pros:** More control, no rate limits, faster downloads
- **Cons:** Requires server, maintenance, costs money

### 2. Delta Updates

Download only changed files instead of full executable:
- **Pros:** Smaller downloads, faster updates
- **Cons:** More complex implementation

### 3. Silent Background Updates

Download updates in background, apply on next restart:
- **Pros:** Less disruptive to users
- **Cons:** Users may delay restarts

### 4. Beta Channel

Separate release track for testing:
- **Pros:** Test with real users before stable release
- **Cons:** More complex release management

---

## Database Migrations

When database schema changes between versions:

1. **Plan migrations carefully**
2. **Test on backup data first**
3. **Provide rollback scripts**
4. **Document changes in release notes**

The current system automatically creates new tables if they don't exist, making upgrades seamless.

---

## Support

For issues with versioning or updates:
- Check the update_history table in the database
- Review application logs
- Contact the development team
- Report issues on GitHub

---

## Summary

The Clinic Auto-Fill application uses a robust, server-free auto-update system built on GitHub Releases. By following the best practices in this guide, you can ensure smooth, reliable updates for all users.

**Key Takeaways:**
- ✅ Use semantic versioning
- ✅ Test thoroughly before releasing
- ✅ Write clear release notes
- ✅ Users get updates automatically
- ✅ Backups happen automatically
- ✅ Rollback is automatic on failure
