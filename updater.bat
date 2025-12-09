@echo off
REM Auto-updater batch script for Windows
REM Usage: updater.bat <current_exe> <new_exe_full_path> <new_version>

setlocal

set CURRENT_EXE=%1
set NEW_EXE=%2
set NEW_VERSION=%3
set BACKUP_EXE=%CURRENT_EXE%.backup

echo ================================================
echo Clinic Auto-Tool Updater
echo ================================================
echo.
echo Updating to version %NEW_VERSION%...
echo Current: %CURRENT_EXE%
echo New file: %NEW_EXE%
echo.

REM Wait for main app to close
echo Waiting for application to close...
timeout /t 3 /nobreak > nul

REM Backup current version
if exist "%CURRENT_EXE%" (
    echo Creating backup...
    copy /Y "%CURRENT_EXE%" "%BACKUP_EXE%" > nul
    if errorlevel 1 (
        echo ERROR: Failed to create backup!
        goto :error
    )
    echo Backup created: %BACKUP_EXE%
)

REM Delete old exe (with retries for antivirus)
echo Removing old version...
set /a retry=0
:delete_retry
del /F /Q "%CURRENT_EXE%" > nul 2>&1
if exist "%CURRENT_EXE%" (
    set /a retry+=1
    if %retry% LSS 5 (
        echo Retry %retry%/5 - Waiting for file access...
        timeout /t 2 /nobreak > nul
        goto :delete_retry
    ) else (
        echo ERROR: Cannot delete old file after 5 attempts!
        echo Please close all instances of the application.
        goto :error
    )
)

REM Move new version from TEMP to current location
echo Installing new version...
move /Y "%NEW_EXE%" "%CURRENT_EXE%" > nul
if errorlevel 1 (
    echo ERROR: Failed to install new version!
    echo Restoring from backup...
    if exist "%BACKUP_EXE%" (
        copy /Y "%BACKUP_EXE%" "%CURRENT_EXE%" > nul
    )
    goto :error
)

echo.
echo ================================================
echo Update successful!
echo ================================================
echo.
echo Launching updated application...

REM Launch updated app
start "" "%CURRENT_EXE%"

REM Clean up old backups (keep only most recent)
timeout /t 2 /nobreak > nul
for %%F in ("%CURRENT_EXE%.backup*") do (
    if not "%%~nxF"=="%BACKUP_EXE%" (
        del /F /Q "%%F" > nul 2>&1
    )
)

echo Update complete. This window will close in 3 seconds...
timeout /t 3 /nobreak > nul
exit /b 0

:error
echo.
echo ================================================
echo Update failed!
echo ================================================
echo.
echo Possible solutions:
echo 1. Disable antivirus temporarily
echo 2. Run as Administrator  
echo 3. Close all instances of the application
echo 4. Move app to a different folder
echo.
pause
exit /b 1
