#!/usr/bin/env python3
"""
Export Manual Entries from Database to CSV

This script reads the manual_entries table from app_data.db and exports it to CSV format
that is compatible with the "Nhập CSV" (Import CSV) feature in the application.

The exported CSV will be sorted by appointment date (oldest to newest).
"""

import sqlite3
import csv
import os
from datetime import datetime
from collections import defaultdict

DATABASE_FILE = "app_data_re.db"


def export_manual_entries_to_csv(output_filename="manual_entries_export.csv"):
    """
    Export manual_entries table to CSV format compatible with app's CSV import.
    
    CSV Format:
    PatientID;procedure1-procedure2-procedure3;
    HH:MM;staff1-staff2-staff3;DD-MM-YY
    HH:MM;staff1-staff2-staff3;DD-MM-YY
    ...
    
    Args:
        output_filename: Name of the output CSV file
    
    Returns:
        Number of entries exported
    """
    
    # Check if database exists
    if not os.path.exists(DATABASE_FILE):
        print(f"ERROR: Database file '{DATABASE_FILE}' not found!")
        return 0
    
    # Connect to database
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Fetch all manual entries sorted by appointment_date
    cursor.execute("""
        SELECT patient_id, procedures, staff, appointment_date, appointment_time
        FROM manual_entries
        ORDER BY appointment_date ASC, appointment_time ASC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("No manual entries found in database.")
        return 0
    
    # Group entries by patient_id
    grouped_data = defaultdict(list)
    
    for row in rows:
        patient_id = row[0]
        procedures = row[1]
        staff = row[2]
        appointment_date = row[3]
        appointment_time = row[4]
        
        grouped_data[patient_id].append({
            'procedures': procedures,
            'staff': staff,
            'appointment_date': appointment_date,
            'appointment_time': appointment_time
        })
    
    # Write to CSV file
    with open(output_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        
        for patient_id, entries in grouped_data.items():
            # First row: PatientID;procedures;
            # Use procedures from first entry (should be same for all appointments of this patient)
            procedures_str = entries[0]['procedures']
            writer.writerow([patient_id, procedures_str, ''])
            
            # Subsequent rows: HH:MM;staff;DD-MM-YY
            for entry in entries:
                appointment_date = entry['appointment_date']
                appointment_time = entry['appointment_time']
                staff = entry['staff']
                
                # Convert date format if needed
                # If date is stored as DD-MM-YYYY, we need to convert to DD-MM-YY
                try:
                    # Try parsing as DD-MM-YYYY
                    date_obj = datetime.strptime(appointment_date, "%d-%m-%Y")
                    date_short = date_obj.strftime("%d-%m-%y")
                except ValueError:
                    try:
                        # Try parsing as DD/MM/YYYY
                        date_obj = datetime.strptime(appointment_date, "%d/%m/%Y")
                        date_short = date_obj.strftime("%d-%m-%y")
                    except ValueError:
                        # If already in short format or other format, use as is
                        date_short = appointment_date
                
                writer.writerow([appointment_time, staff, date_short])
    
    total_entries = len(rows)
    print(f"✓ Successfully exported {total_entries} manual entries to '{output_filename}'")
    print(f"  Grouped into {len(grouped_data)} patient(s)")
    return total_entries


def main():
    """Main function to run the export."""
    print("=" * 60)
    print("Export Manual Entries to CSV")
    print("=" * 60)
    print()
    
    # Check if database exists
    if not os.path.exists(DATABASE_FILE):
        print(f"ERROR: Database file '{DATABASE_FILE}' not found!")
        print(f"Please make sure you're running this script in the same directory")
        print(f"as your '{DATABASE_FILE}' file.")
        return
    
    # Export to CSV
    output_file = "manual_entries_export.csv"
    count = export_manual_entries_to_csv(output_file)
    
    if count > 0:
        print()
        print("=" * 60)
        print(f"Export complete! File saved as: {output_file}")
        print("=" * 60)
        print()
        print("You can now import this file using 'Nhập CSV' in the application.")
    else:
        print()
        print("No data to export.")


if __name__ == "__main__":
    main()
