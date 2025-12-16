"""
Standalone script to show JSON output from CSV
(Run this in the same environment as your main app)
"""
import json

# Instructions
print("=" * 70)
print("CSV TO JSON CONVERTER")
print("=" * 70)
print("\nTo use this script, run it in your virtual environment:")
print("\n  1. Activate venv:")
print("     venv\\Scripts\\activate")
print("\n  2. Run the script:")
print("     python csv_to_json_standalone.py your_file.csv")
print("\n  3. Or use in Python:")
print("     from handle_data import read_data")
print("     import json")
print("     data = read_data('your_file.csv')")
print("     print(json.dumps(data, ensure_ascii=False, indent=4))")
print("\n" + "=" * 70)

# If you want to test, paste this code in your Python console (with venv activated):
test_code = '''
from handle_data import read_data
import json

# Read CSV
data = read_data('your_file.csv')

# Save to JSON
with open('output.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"Converted {len(data)} records to output.json")
'''

print("\nQUICK TEST CODE (copy and run in Python console with venv):")
print("-" * 70)
print(test_code)
print("-" * 70)

# Create a batch file for easy use
batch_content = '''@echo off
call venv\\Scripts\\activate
python -c "import sys; import json; from handle_data import read_data; data = read_data(sys.argv[1] if len(sys.argv) > 1 else 'data.csv'); print(json.dumps(data, ensure_ascii=False, indent=4)); json.dump(data, open(sys.argv[1].replace('.csv', '.json') if len(sys.argv) > 1 else 'output.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=4); print('Saved to ' + (sys.argv[1].replace('.csv', '.json') if len(sys.argv) > 1 else 'output.json'))" %*
pause
'''

with open('convert_csv_to_json.bat', 'w', encoding='utf-8') as f:
    f.write(batch_content)

print("\n✓ Created batch file: convert_csv_to_json.bat")
print("\nUSAGE:")
print("  convert_csv_to_json.bat your_file.csv")
print("\nThis will create: your_file.json")
