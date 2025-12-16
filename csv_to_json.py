"""
Script to convert CSV data to JSON format for inspection
"""
import json
import sys
from handle_data import read_data

def csv_to_json(csv_file, output_json=None):
    """
    Convert CSV file to JSON format
    
    Args:
        csv_file: Path to CSV file
        output_json: Optional output JSON file path. If not provided, prints to console
    """
    print(f"Reading CSV file: {csv_file}")
    
    # Read and parse CSV data
    data = read_data(csv_file)
    
    print(f"Loaded {len(data)} records")
    
    # Convert to JSON
    json_str = json.dumps(data, ensure_ascii=False, indent=4)
    
    if output_json:
        # Save to file
        with open(output_json, 'w', encoding='utf-8') as f:
            f.write(json_str)
        print(f"✓ Saved to: {output_json}")
    else:
        # Print to console
        print("\n" + "=" * 60)
        print("JSON OUTPUT:")
        print("=" * 60)
        print(json_str)
    
    return data

if __name__ == "__main__":
    # Default: convert test data
    csv_file = "test_conflict.csv"
    output_file = "test_conflict.json"
    
    # Check if command line arguments provided
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = csv_file.replace('.csv', '.json')
    
    try:
        # First create test CSV if it doesn't exist
        import os
        if not os.path.exists(csv_file) and csv_file == "test_conflict.csv":
            print("Creating test CSV file...")
            test_csv_content = """1234567890;cứu-giác-kéo-thủy;
08:00;duy-anh-khoái;16-12-25
1234567891;cứu-giác-kéo-thủy;
08:00;khoái-anh-lực;16-12-25"""
            
            with open(csv_file, 'w', encoding='utf-8') as f:
                f.write(test_csv_content)
            print(f"✓ Created {csv_file}")
        
        # Convert
        data = csv_to_json(csv_file, output_file)
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        for i, record in enumerate(data, 1):
            print(f"\nRecord {i}:")
            print(f"  ID: {record['id']}")
            print(f"  Date: {record['ngay']}")
            print(f"  IsFirst: {record['isFirst']}")
            print(f"  Procedures: {len(record['thu_thuats'])}")
            
            for j, proc in enumerate(record['thu_thuats'], 1):
                start = proc['Ngay BD TH'].replace('{SPACE}', ' ')
                end = proc['Ngay KQ'].replace('{SPACE}', ' ')
                print(f"    {j}. {proc['Ten']:6} | {proc['Nguoi Thuc Hien']:25} | {start} - {end}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
