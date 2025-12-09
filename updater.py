import os
import sys
import time
import subprocess
import shutil
from database import update_version_in_db, log_update_attempt, get_current_version_from_db

def main():
    if len(sys.argv) != 4:
        print("Usage: python updater.py <current_executable> <new_executable> <new_version>")
        sys.exit(1)

    current_executable = sys.argv[1]
    new_executable = sys.argv[2]
    new_version = sys.argv[3]
    
    old_version = get_current_version_from_db()
    backup_file = None

    try:
        # Create backup of current executable
        backup_file = f"{current_executable}.backup_v{old_version}"
        print(f"Creating backup: {backup_file}")
        
        # Wait for the main application to exit
        retries = 10
        for i in range(retries):
            try:
                # Create backup before removing
                shutil.copy2(current_executable, backup_file)
                # Remove the old executable
                os.remove(current_executable)
                break
            except PermissionError:
                if i < retries - 1:
                    print(f"Waiting for application to close... ({i+1}/{retries})")
                    time.sleep(1)
                else:
                    raise Exception("Failed to remove old executable - application may still be running")
            except Exception as e:
                raise Exception(f"Failed to create backup or remove old file: {e}")

        # Verify new executable exists
        if not os.path.exists(new_executable):
            raise Exception(f"New executable not found: {new_executable}")

        # Rename the new executable
        print(f"Installing new version {new_version}...")
        os.rename(new_executable, current_executable)

        # Update the version in the database
        update_version_in_db(new_version)
        
        # Log successful update
        log_update_attempt(old_version, new_version, True)
        
        print(f"✓ Successfully updated from {old_version} to {new_version}")
        print(f"  Backup saved as: {backup_file}")

        # Relaunch the application
        print("Relaunching application...")
        subprocess.Popen([current_executable])
        
        # Clean up old backups (keep only last 3)
        cleanup_old_backups(current_executable)

    except Exception as e:
        error_msg = f"Update failed: {e}"
        print(f"✗ {error_msg}")
        
        # Log failed update
        log_update_attempt(old_version, new_version, False, str(e))
        
        # Attempt rollback if backup exists
        if backup_file and os.path.exists(backup_file):
            try:
                print("Attempting to restore from backup...")
                if os.path.exists(new_executable):
                    os.remove(new_executable)
                shutil.copy2(backup_file, current_executable)
                print("✓ Restored from backup successfully")
                subprocess.Popen([current_executable])
            except Exception as rollback_error:
                print(f"✗ Rollback failed: {rollback_error}")
                print(f"Please manually restore from: {backup_file}")
        
        sys.exit(1)


def cleanup_old_backups(executable_name, keep_count=3):
    """Remove old backup files, keeping only the most recent ones."""
    try:
        directory = os.path.dirname(executable_name) or "."
        base_name = os.path.basename(executable_name)
        
        # Find all backup files
        backups = []
        for filename in os.listdir(directory):
            if filename.startswith(f"{base_name}.backup_v"):
                filepath = os.path.join(directory, filename)
                backups.append((filepath, os.path.getmtime(filepath)))
        
        # Sort by modification time (newest first)
        backups.sort(key=lambda x: x[1], reverse=True)
        
        # Remove old backups beyond keep_count
        for filepath, _ in backups[keep_count:]:
            try:
                os.remove(filepath)
                print(f"Cleaned up old backup: {os.path.basename(filepath)}")
            except Exception as e:
                print(f"Warning: Could not remove old backup {filepath}: {e}")
    
    except Exception as e:
        print(f"Warning: Backup cleanup failed: {e}")


if __name__ == "__main__":
    main()
