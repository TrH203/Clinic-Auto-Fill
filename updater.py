import os
import sys
import time
import subprocess
from database import update_version_in_db

def main():
    if len(sys.argv) != 4:
        print("Usage: python updater.py <current_executable> <new_executable> <new_version>")
        sys.exit(1)

    current_executable = sys.argv[1]
    new_executable = sys.argv[2]
    new_version = sys.argv[3]

    # Wait for the main application to exit
    retries = 10
    for i in range(retries):
        try:
            # Remove the old executable
            os.remove(current_executable)
            break
        except PermissionError:
            if i < retries - 1:
                time.sleep(1)
            else:
                raise

    try:
        # Rename the new executable
        os.rename(new_executable, current_executable)

        # Update the version in the database
        update_version_in_db(new_version)

        # Relaunch the application
        subprocess.Popen([current_executable])

    except Exception as e:
        print(f"Update failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
