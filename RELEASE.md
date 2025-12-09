# How to Release a New Version

## Quick Steps

1. **Make sure all changes are committed**
   ```bash
   git add .
   git commit -m "Release v1.2.0"
   ```

2. **Create and push the tag**
   ```bash
   git tag v1.2.0
   git push origin main
   git push origin v1.2.0
   ```

3. **GitHub Actions will automatically:**
   - Build the .exe on Windows runner
   - Create a new release
   - Upload the .exe to the release

4. **Check the release:**
   - Go to: https://github.com/TrH203/Clinic-Auto-Fill/releases
   - Download and test the .exe
   - Edit release notes if needed

## Notes

- Build happens on **windows-latest** runner (dù bạn code trên Mac)
- The workflow uses your `PERSONAL_GITHUB_TOKEN` secret
- Build takes about 5-10 minutes
- Output: `ClinicAutoTool-v1.2.0.exe`
- Check Actions tab if build fails

## Local Build (Nếu muốn test trước)

Bạn không thể build .exe trên Mac. Cần build trên Windows:
- Dùng GitHub Actions (tự động)
- Hoặc dùng máy Windows / VM Windows

## Version Numbering

Follow semantic versioning (MAJOR.MINOR.PATCH):
- **v1.2.0** → **v1.2.1** (bug fixes)
- **v1.2.0** → **v1.3.0** (new features)
- **v1.2.0** → **v2.0.0** (breaking changes)
