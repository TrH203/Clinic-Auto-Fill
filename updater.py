import os
import sys
import subprocess
import platform
import requests
from packaging.version import parse as parse_version


def get_current_version():
    """Read version from the bundled VERSION file."""
    # PyInstaller frozen mode: bundled files are extracted to sys._MEIPASS
    if getattr(sys, 'frozen', False):
        version_path = os.path.join(sys._MEIPASS, 'VERSION')
    else:
        version_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'VERSION')

    try:
        with open(version_path, 'r') as f:
            return f.read().strip()
    except Exception:
        return "0.0.0"


def check_for_update(current_version, repo):
    """Check GitHub releases for a newer version.

    Returns dict with version/download_url/changelog if update available, else None.
    """
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code != 200:
            return None

        data = resp.json()
        tag = data.get("tag_name", "")
        remote_version = tag.lstrip("v")

        if not remote_version:
            return None

        if parse_version(remote_version) == parse_version(current_version):
            return None

        # Find the .exe asset
        download_url = None
        for asset in data.get("assets", []):
            if asset["name"].endswith(".exe"):
                download_url = asset["browser_download_url"]
                break

        if not download_url:
            return None

        return {
            "version": remote_version,
            "download_url": download_url,
            "changelog": data.get("body", ""),
        }
    except Exception:
        return None


def download_update(url, dest_path, progress_callback=None):
    """Download the new exe to dest_path. Returns True on success."""
    try:
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0

        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total > 0:
                        progress_callback(downloaded / (1024 * 1024), total / (1024 * 1024))

        return True
    except Exception:
        # Clean up partial download
        try:
            if os.path.exists(dest_path):
                os.remove(dest_path)
        except Exception:
            pass
        return False


def apply_update_windows(new_exe_path, current_exe_path):
    """Spawn a bat script that replaces the running exe after it exits.

    This function does NOT return - it calls sys.exit(0).
    """
    bat_path = os.path.join(os.path.dirname(current_exe_path), "_update.bat")

    bat_content = f'''@echo off
setlocal
set "OLD_EXE={current_exe_path}"
set "NEW_EXE={new_exe_path}"
set RETRIES=0

:wait_loop
timeout /t 1 /nobreak >nul
del "%OLD_EXE%" 2>nul
if exist "%OLD_EXE%" (
    set /a RETRIES+=1
    if %RETRIES% lss 15 goto wait_loop
    echo Update failed - could not replace old version.
    del "%NEW_EXE%" 2>nul
    pause
    goto :eof
)

move "%NEW_EXE%" "%OLD_EXE%"
if errorlevel 1 (
    echo Update failed - could not move new version.
    pause
    goto :eof
)

start "" "%OLD_EXE%"
del "%~f0"
'''

    with open(bat_path, "w") as f:
        f.write(bat_content)

    # CREATE_NO_WINDOW = 0x08000000
    subprocess.Popen(
        [bat_path],
        creationflags=0x08000000,
        close_fds=True,
    )

    # os._exit() kills the entire process immediately (unlike sys.exit which
    # only raises SystemExit and won't terminate from a daemon thread)
    os._exit(0)
