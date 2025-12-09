@echo off
REM Auto-updater batch script for Windows
REM Usage: updater.bat <current_exe> <new_exe> <new_version>

setlocal

set CURRENT_EXE=%1
set NEW_EXE=%2
set NEW_VERSION=%3
set BACKUP_EXE=%CURRENT_EXE%.backup

echo Updating to version %NEW_VERSION%...

REM Wait for main app to close
timeout /t 2 /nobreak > nul

REM Backup current version
if exist "%CURRENT_EXE%" (
    echo Creating backup...
    copy /Y "%CURRENT_EXE%" "%BACKUP_EXE%" > nul
    if errorlevel 1 (
        echo Failed to create backup!
        goto :error
    )
)

REM Delete old exe
echo Removing old version...
del /F /Q "%CURRENT_EXE%" > nul 2>&1
if exist "%CURRENT_EXE%" (
    timeout /t 1 /nobreak > nul
    del /F /Q "%CURRENT_EXE%" > nul 2>&1
)

REM Install new version
echo Installing new version...
move /Y "%NEW_EXE%" "%CURRENT_EXE%" > nul
if errorlevel 1 (
    echo Failed to install new version!
    echo Restoring from backup...
    copy /Y "%BACKUP_EXE%" "%CURRENT_EXE%" > nul
    goto :error
)

echo Update successful!
echo Launching application...

REM Launch updated app
start "" "%CURRENT_EXE%"

REM Clean up
timeout /t 2 /nobreak > nul
if exist "%BACKUP_EXE%.old" del /F /Q "%BACKUP_EXE%.old" > nul 2>&1

exit /b 0

:error
echo Update failed!
pause
exit /b 1
