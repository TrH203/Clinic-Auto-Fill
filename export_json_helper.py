"""
Simple test to add to your interface.py or run separately
Add this to the bottom of interface.py to enable "Export JSON" feature
"""

# You can add this method to AutomationGUI class:
def export_to_json_method(self):
    """Export all data to JSON format for inspection."""
    if not self.all_data:
        messagebox.showwarning("No Data", "No data to export.")
        return
    
    filename = filedialog.asksaveasfilename(
        title="Export Data to JSON",
        defaultextension=".json",
        filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
    )
    
    if not filename:
        return
    
    try:
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.all_data, f, ensure_ascii=False, indent=4)
        
        self.log_message(f"✓ Exported {len(self.all_data)} records to JSON: {filename}")
        messagebox.showinfo("Export Successful", 
                          f"Exported {len(self.all_data)} records to:\n{filename}")
    except Exception as e:
        self.log_message(f"✗ Failed to export JSON: {e}", "ERROR")
        messagebox.showerror("Export Error", f"Failed to export JSON:\n{e}")

# Quick standalone test script
if __name__ == "__main__":
    print("Quick CSV to JSON Test")
    print("=" * 60)
    
    # Test CSV content
    test_csv = """1234567890;cứu-giác-kéo-thủy;
08:00;duy-anh-khoái;16-12-25
1234567891;cứu-giác-kéo-thủy;
08:00;khoái-anh-lực;16-12-25"""
    
    # Save test CSV
    with open('quick_test.csv', 'w', encoding='utf-8') as f:
        f.write(test_csv)
    
    print("Created: quick_test.csv")
    print("\nNow run in your venv Python console:")
    print("-" * 60)
    print("""
from handle_data import read_data
import json

data = read_data('quick_test.csv')

with open('quick_test.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(json.dumps(data, ensure_ascii=False, indent=4))
    """)
    print("-" * 60)
    print("\nOR simply use the GUI:")
    print("  1. Load quick_test.csv in the app")
    print("  2. Click 'Export CSV' button")
    print("  3. Choose .json extension")
