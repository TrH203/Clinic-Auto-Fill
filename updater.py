import os
import sys
import time
import subprocess

def main():
    if len(sys.argv) != 3:
        print("Usage: python updater.py <current_executable> <new_executable>")
        sys.exit(1)

    current_executable = sys.argv[1]
    new_executable = sys.argv[2]

    # Wait for the main application to exit
    time.sleep(2)

    try:
        # Remove the old executable
        os.remove(current_executable)

        # Rename the new executable
        os.rename(new_executable, current_executable)

        # Relaunch the application
        subprocess.Popen([current_executable])

    except Exception as e:
        print(f"Update failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
