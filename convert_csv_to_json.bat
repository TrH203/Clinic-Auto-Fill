@echo off
echo ===================================
echo CSV to JSON Converter
echo ===================================
echo.

REM Activate virtual environment
call venv\Scripts\activate

REM Get CSV filename from argument or use default
set CSV_FILE=%1
if "%CSV_FILE%"=="" set CSV_FILE=quick_test.csv

REM Run Python code to convert
python -c "import json; from handle_data import read_data; data = read_data('%CSV_FILE%'); output_file = '%CSV_FILE%'.replace('.csv', '.json'); json.dump(data, open(output_file, 'w', encoding='utf-8'), ensure_ascii=False, indent=4); print('Converted %CSV_FILE% to ' + output_file); print('Records:', len(data))"

echo.
echo ===================================
echo Done!
echo ===================================
pause
