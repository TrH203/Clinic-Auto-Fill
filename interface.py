import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
from pywinauto import Application
from handle_data import read_data, load_manual_data_from_json, merge_csv_and_manual_data, export_data_to_csv
from tool import Tool
import time
import os
import sys
import webbrowser
from config import PATIENT_ROW, TIEP
from database import get_current_version_from_db, initialize_database, load_manual_entries_from_db
from manual_entry import ManualEntryDialog

CURRENT_VERSION = get_current_version_from_db()
GITHUB_REPO = "TrH203/Clinic-Auto-Fill"
GITHUB_RELEASES_URL = f"https://github.com/{GITHUB_REPO}/releases"

class AutomationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Medical Data Automation Tool - v{CURRENT_VERSION}")
        self.root.geometry("850x650")
        # Set minimum size to prevent UI breaking
        self.root.minsize(750, 550)
        self.root.resizable(True, True)
        
        # Variables
        self.is_running = False
        self.paused = False
        self.emergency_stop_flag = False
        self.current_thread = None
        self.data_file_path = tk.StringVar()
        self.app = None
        self.dlg = None
        self.all_data = []
        self.manual_data = []
        self.csv_data = []
        self.current_index = 0

        # Queue for thread communication
        self.log_queue = queue.Queue()
        
        # Auto-save file path
        self.auto_save_path = os.path.join(os.path.dirname(__file__), 'auto_save.csv')
        
        self.setup_ui()
        self.setup_hotkeys()
        self.check_queue()
        
        # Bind close event for auto-save
        self.root.protocol("WM_DELETE_WINDOW", self.on_app_close)
        
        # Auto-load data if available
        self.auto_load_data()
        
        
    def setup_ui(self):
        # Create canvas and scrollbar for scrollable window
        canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding="10")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Use scrollable_frame as main container
        main_frame = scrollable_frame
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Medical Data Automation Tool", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="Data File", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="CSV File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        file_entry = ttk.Entry(file_frame, textvariable=self.data_file_path, state='readonly')
        file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        browse_btn = ttk.Button(file_frame, text="Browse CSV", command=self.browse_file)
        browse_btn.grid(row=0, column=2, padx=(0, 5))
        
        manual_btn = ttk.Button(file_frame, text="Manual Entry", command=self.open_manual_entry)
        manual_btn.grid(row=0, column=3, padx=(0, 5))
        
        export_btn = ttk.Button(file_frame, text="📄 Export CSV", command=self.export_to_csv)
        export_btn.grid(row=0, column=4)
        
        # Data display table
        data_table_frame = ttk.LabelFrame(main_frame, text="Loaded Data", padding="10")
        data_table_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 10))
        data_table_frame.columnconfigure(0, weight=1)
        data_table_frame.rowconfigure(0, weight=1)
        
        # Create Treeview with scrollbars
        tree_scroll_y = ttk.Scrollbar(data_table_frame, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(data_table_frame, orient="horizontal")
        
        self.data_tree = ttk.Treeview(data_table_frame, 
                                      columns=('ID', 'Date', 'Time', 'Procedures', 'Staff', 'Source'),
                                      show='headings',
                                      height=6,
                                      yscrollcommand=tree_scroll_y.set,
                                      xscrollcommand=tree_scroll_x.set)
        
        tree_scroll_y.config(command=self.data_tree.yview)
        tree_scroll_x.config(command=self.data_tree.xview)
        
        # Configure columns
        self.data_tree.heading('ID', text='Patient ID')
        self.data_tree.heading('Date', text='Date')
        self.data_tree.heading('Time', text='Time')
        self.data_tree.heading('Procedures', text='Procedures')
        self.data_tree.heading('Staff', text='Staff')
        self.data_tree.heading('Source', text='Source')
        
        # Set smaller column widths for better fit on small screens
        self.data_tree.column('ID', width=85, minwidth=70, anchor='center')
        self.data_tree.column('Date', width=80, minwidth=70, anchor='center')
        self.data_tree.column('Time', width=50, minwidth=45, anchor='center')
        self.data_tree.column('Procedures', width=130, minwidth=100, anchor='w')
        self.data_tree.column('Staff', width=160, minwidth=120, anchor='w')
        self.data_tree.column('Source', width=55, minwidth=50, anchor='center')
        
        # Grid layout for tree and scrollbars
        self.data_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind double-click to edit entry
        self.data_tree.bind('<Double-Button-1>', self.edit_entry)
        
        
        # Connection section
        conn_frame = ttk.LabelFrame(main_frame, text="Application Connection", padding="10")
        conn_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.conn_status_label = ttk.Label(conn_frame, text="Status: Not Connected", 
                                          foreground="red")
        self.conn_status_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        connect_btn = ttk.Button(conn_frame, text="Connect to Application", 
                               command=self.connect_to_app)
        connect_btn.grid(row=0, column=1)
        
        # Control section
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="Start Automation", 
                                   command=self.start_automation, state='disabled')
        self.start_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_btn = ttk.Button(control_frame, text="Stop Automation", 
                                  command=self.stop_automation, state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=(0, 5))
        
        self.pause_btn = ttk.Button(control_frame, text="Pause", 
                                   command=self.pause_automation, state='disabled')
        self.pause_btn.grid(row=0, column=2, padx=(0, 5))
        
        # Emergency stop button
        self.emergency_btn = ttk.Button(control_frame, text="🛑 EMERGENCY STOP", 
                                       command=self.emergency_stop, 
                                       style="Emergency.TButton")
        self.emergency_btn.grid(row=0, column=3, padx=(10, 0))
        
        # Configure emergency button style
        style = ttk.Style()
        style.configure("Emergency.TButton", foreground="red", font=('Arial', 9, 'bold'))
        
        # Delay settings
        delay_frame = ttk.Frame(control_frame)
        delay_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(delay_frame, text="Delay between actions (seconds):").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.delay_var = tk.DoubleVar(value=0.5)
        delay_spinbox = ttk.Spinbox(delay_frame, from_=0.1, to=5.0, increment=0.1, 
                                   textvariable=self.delay_var, width=10)
        delay_spinbox.grid(row=0, column=1, padx=(0, 10))
        
        ttk.Label(delay_frame, text="Step delay (seconds):").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        
        self.step_delay_var = tk.DoubleVar(value=1.0)
        step_delay_spinbox = ttk.Spinbox(delay_frame, from_=0.5, to=10.0, increment=0.5, 
                                        textvariable=self.step_delay_var, width=10)
        step_delay_spinbox.grid(row=0, column=3)
        
        # Progress section
        progress_frame = ttk.Frame(control_frame)
        progress_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        progress_frame.columnconfigure(1, weight=1)
        
        ttk.Label(progress_frame, text="Progress:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.progress_var = tk.StringVar(value="0/0")
        self.progress_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=1, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Current ID section
        id_frame = ttk.Frame(control_frame)
        id_frame.grid(row=3, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(id_frame, text="Current ID:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.current_id_var = tk.StringVar(value="None")
        current_id_label = ttk.Label(id_frame, textvariable=self.current_id_var, 
                                   font=('Arial', 10, 'bold'), foreground="blue")
        current_id_label.grid(row=0, column=1, sticky=tk.W)
        
        # Hotkey info
        hotkey_frame = ttk.Frame(control_frame)
        hotkey_frame.grid(row=4, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        hotkey_label = ttk.Label(hotkey_frame, text="🔥 Hotkey: Press F12 for Emergency Stop", 
                               font=('Arial', 9, 'bold'), foreground="red")
        hotkey_label.grid(row=0, column=0, sticky=tk.W)
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear log button
        clear_log_btn = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_log_btn.grid(row=1, column=0, sticky=tk.E, pady=(5, 0))
        
        



    def setup_hotkeys(self):
        """Setup global hotkey for emergency stop"""
        # Bind F12 key to emergency stop
        self.root.bind('<F12>', lambda event: self.emergency_stop())
        
        # Make sure the window can capture F12 even when not focused
        self.root.focus_set()
        
        # Also bind Escape key as alternative emergency stop
        self.root.bind('<Escape>', lambda event: self.emergency_stop() if self.is_running else None)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select CSV Data File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.data_file_path.set(filename)
            self.load_data_file()
            
    def load_data_file(self):
        try:
            self.csv_data = read_data(self.data_file_path.get())
            self.merge_all_data()
            self.update_data_table()
            self.log_message(f"✓ Loaded {len(self.csv_data)} records from CSV file")
            self.update_button_states()
        except Exception as e:
            self.log_message(f"✗ Error loading file: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to load data file:\n{str(e)}")
    
    def open_manual_entry(self):
        """Open manual entry dialog."""
        try:
            dialog = ManualEntryDialog(self.root, on_save_callback=self.on_manual_entry_saved)
            result = dialog.show()
        except Exception as e:
            self.log_message(f"✗ Error opening manual entry: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to open manual entry:\n{str(e)}")
    
    def on_manual_entry_saved(self, data):
        """Callback when manual entry is saved."""
        self.manual_data.append(data)
        self.merge_all_data()
        self.update_data_table()
        self.log_message(f"✓ Added manual entry for Patient ID: {data['id']}")
    
    def edit_entry(self, event=None):
        """Edit selected entry from the data table."""
        selection = self.data_tree.selection()
        if not selection:
            return
        
        # Get the selected item
        item = selection[0]
        values = self.data_tree.item(item, 'values')
        
        if not values:
            return
        
        patient_id = values[0]
        source = values[5]  # CSV or Manual
        
        # Get the index of the selected item in the tree
        all_items = self.data_tree.get_children()
        tree_index = all_items.index(item)
        
        # Find the corresponding data entry using the tree index
        # The tree displays CSV data first, then manual data
        target_data = None
        data_index = None
        is_manual = False
        
        csv_count = len(self.csv_data)
        
        if tree_index < csv_count:
            # This is a CSV entry
            target_data = self.csv_data[tree_index]
            data_index = tree_index
            is_manual = False
        else:
            # This is a manual entry
            manual_index = tree_index - csv_count
            if manual_index < len(self.manual_data):
                target_data = self.manual_data[manual_index]
                data_index = manual_index
                is_manual = True
        
        if not target_data:
            messagebox.showerror("Error", "Could not find entry data.")
            return
        
        try:
            # Create a copy for editing
            import copy
            edit_data = copy.deepcopy(target_data)
            
            # Open manual entry dialog with existing data
            dialog = ManualEntryDialog(self.root, 
                                      on_save_callback=lambda d: self.on_entry_edited(d, is_manual, data_index),
                                      initial_data=edit_data,
                                      on_delete_callback=lambda: self.delete_entry(is_manual, data_index))
            dialog.show()
            
        except Exception as e:
            self.log_message(f"✗ Error opening edit dialog: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to open edit dialog:\n{str(e)}")
    
    def on_entry_edited(self, updated_data, is_manual, data_index):
        """Callback when an entry is edited."""
        # Update the data in the appropriate list
        if is_manual:
            if data_index < len(self.manual_data):
                self.manual_data[data_index] = updated_data
        else:
            if data_index < len(self.csv_data):
                self.csv_data[data_index] = updated_data
        
        # Refresh the merged data and table
        self.merge_all_data()
        self.update_data_table()
        self.log_message(f"✓ Updated entry for Patient ID: {updated_data['id']}")
    
    def delete_entry(self, is_manual, data_index):
        """Delete an entry from the data lists."""
        try:
            if is_manual:
                if data_index < len(self.manual_data):
                    deleted_entry = self.manual_data.pop(data_index)
                    self.log_message(f"✓ Deleted manual entry for Patient ID: {deleted_entry.get('id', 'Unknown')}")
            else:
                if data_index < len(self.csv_data):
                    deleted_entry = self.csv_data.pop(data_index)
                    self.log_message(f"✓ Deleted CSV entry for Patient ID: {deleted_entry.get('id', 'Unknown')}")
            
            # Refresh the merged data and table
            self.merge_all_data()
            self.update_data_table()
        except Exception as e:
            self.log_message(f"✗ Error deleting entry: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to delete entry:\n{str(e)}")
    
    def merge_all_data(self):
        """Merge CSV and manual data."""
        self.all_data = merge_csv_and_manual_data(self.csv_data, self.manual_data)
        total = len(self.all_data)
        self.progress_bar['maximum'] = total if total > 0 else 1
        self.progress_var.set(f"0/{total}")
        self.log_message(f"📊 Total records: {total} (CSV: {len(self.csv_data)}, Manual: {len(self.manual_data)})")
    
    def update_data_table(self):
        """Update the data table with current records."""
        # Clear existing items
        for item in self.data_tree.get_children():
            self.data_tree.delete(item)
        
        # Add CSV data
        for record in self.csv_data:
            patient_id = record.get('id', '')
            date = record.get('ngay', '')
            
            # Extract time from first thu_thuat
            time_str = ''
            if record.get('thu_thuats') and len(record['thu_thuats']) > 0:
                first_tt = record['thu_thuats'][0]
                ngay_bd_th = first_tt.get('Ngay BD TH', '')
                if '{SPACE}' in ngay_bd_th:
                    time_str = ngay_bd_th.split('{SPACE}')[1] if len(ngay_bd_th.split('{SPACE}')) > 1 else ''
            
            # Get procedures
            procedures = ', '.join([tt.get('Ten', '') for tt in record.get('thu_thuats', [])])
            
            # Get staff (unique)
            staff_set = set()
            for tt in record.get('thu_thuats', []):
                staff_name = tt.get('Nguoi Thuc Hien', '')
                if staff_name:
                    staff_set.add(staff_name)
            staff = ', '.join(sorted(staff_set))
            
            self.data_tree.insert('', 'end', values=(patient_id, date, time_str, procedures, staff, 'CSV'))
        
        # Add manual data
        for record in self.manual_data:
            patient_id = record.get('id', '')
            date = record.get('ngay', '')
            
            # Extract time from first thu_thuat
            time_str = ''
            if record.get('thu_thuats') and len(record['thu_thuats']) > 0:
                first_tt = record['thu_thuats'][0]
                ngay_bd_th = first_tt.get('Ngay BD TH', '')
                if '{SPACE}' in ngay_bd_th:
                    time_str = ngay_bd_th.split('{SPACE}')[1] if len(ngay_bd_th.split('{SPACE}')) > 1 else ''
            
            # Get procedures
            procedures = ', '.join([tt.get('Ten', '') for tt in record.get('thu_thuats', [])])
            
            # Get staff (unique)
            staff_set = set()
            for tt in record.get('thu_thuats', []):
                staff_name = tt.get('Nguoi Thuc Hien', '')
                if staff_name:
                    staff_set.add(staff_name)
            staff = ', '.join(sorted(staff_set))
            
            self.data_tree.insert('', 'end', values=(patient_id, date, time_str, procedures, staff, 'Manual'))
            
    
    def export_to_csv(self):
        """Export all data (CSV + Manual) to CSV file in import format."""
        if not self.all_data:
            messagebox.showwarning("No Data", "No data to export.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Data to CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not filename:
            return
        

        try:
            export_data_to_csv(self.all_data, filename)
            self.log_message(f"✓ Exported {len(self.all_data)} records to {filename}")
            messagebox.showinfo("Export Successful", 
                              f"Exported {len(self.all_data)} records in import format to:\n{filename}\n\n"
                              f"Includes both loaded CSV and manual entries.")
        
        except Exception as e:
            self.log_message(f"✗ Failed to export CSV: {e}", "ERROR")
            messagebox.showerror("Export Error", f"Failed to export CSV:\n{e}")
    
    def connect_to_app(self):
        try:
            self.app = Application(backend="uia").connect(title_re="User: Trần Thị Thu Hiền")
            self.dlg = self.app.window(title_re="User: Trần Thị Thu Hiền")
            self.conn_status_label.config(text="Status: Connected ✓", foreground="green")
            self.log_message("✓ Connected to application successfully")
            self.update_button_states()
        except Exception as e:
            self.conn_status_label.config(text="Status: Connection Failed ✗", foreground="red")
            self.log_message(f"✗ Connection failed: {str(e)}", "ERROR")
            messagebox.showerror("Connection Error", 
                               f"Failed to connect to application:\n{str(e)}\n\n"
                               "Make sure the application is running and the window title matches.")
            
    def update_button_states(self):
        has_data = len(self.all_data) > 0
        is_connected = self.app is not None and self.dlg is not None
        can_start = has_data and is_connected and not self.is_running
        
        self.start_btn.config(state='normal' if can_start else 'disabled')
        self.stop_btn.config(state='normal' if self.is_running else 'disabled')
        self.pause_btn.config(state='normal' if self.is_running else 'disabled')
        
    def start_automation(self):
        if not self.all_data:
            messagebox.showwarning("Warning", "Please load a data file first.")
            return
            
        if not (self.app and self.dlg):
            messagebox.showwarning("Warning", "Please connect to the application first.")
            return
            
        self.is_running = True
        self.current_index = 0
        self.update_button_states()
        self.log_message("🚀 Starting automation process...")
        
        # Start automation in a separate thread
        self.current_thread = threading.Thread(target=self.run_automation, daemon=True)
        self.current_thread.start()
        
    def stop_automation(self):
        self.is_running = False
        self.paused = False
        self.update_button_states()
        self.log_message("⏹️ Stopping automation...")
        
    def emergency_stop(self):
        """Emergency stop that immediately halts all operations"""
        self.emergency_stop_flag = True
        self.is_running = False
        self.paused = False
        self.update_button_states()
        self.log_message("🛑 EMERGENCY STOP ACTIVATED! (F12 pressed)")
        
        # Flash the window to indicate emergency stop
        original_title = self.root.title()
        self.root.title("🛑 EMERGENCY STOP ACTIVATED! 🛑")
        self.root.after(3000, lambda: self.root.title(original_title))
        
        # Show brief notification without blocking
        self.root.bell()  # System beep
        messagebox.showwarning("Emergency Stop", 
                             "🛑 EMERGENCY STOP ACTIVATED!\n\n"
                             "Hotkey: F12 pressed\n"
                             "All automation operations halted.\n\n"
                             "You can now safely interact with other windows.")
        
    def pause_automation(self):
        """Toggle pause state with user control"""
        self.paused = not self.paused
        if self.paused:
            self.pause_btn.config(text="Resume")
            self.log_message("⏸️ Automation Paused - You can now interact with other windows")
            messagebox.showinfo("Paused", 
                              "Automation is now paused.\n\n"
                              "You can safely interact with other windows.\n"
                              "Click 'Resume' to continue automation.")
        else:
            self.pause_btn.config(text="Pause")
            self.log_message("▶️ Automation Resumed")
            # Give user time to focus back on target window
            messagebox.showinfo("Resuming", 
                              "Automation will resume in 3 seconds.\n\n"
                              "Make sure the target application window is visible and focused.")
            self.root.after(3000, lambda: self.log_message("🔄 Automation continuing..."))
        
    def run_automation(self):
        try:
            self.emergency_stop_flag = False
            
            for i, data in enumerate(self.all_data):
                # Check for emergency stop first
                if self.emergency_stop_flag or not self.is_running:
                    break
                    
                # Check for pause
                while self.paused and self.is_running and not self.emergency_stop_flag:
                    time.sleep(0.5)
                    
                if self.emergency_stop_flag or not self.is_running:
                    break
                    
                self.current_index = i
                current_id = data.get("id", "Unknown")
                
                # Update UI in main thread
                self.root.after(0, lambda: self.current_id_var.set(current_id))
                self.root.after(0, lambda: self.progress_var.set(f"{i+1}/{len(self.all_data)}"))
                self.root.after(0, lambda: self.progress_bar.config(value=i+1))
                
                self.log_message(f"📋 Processing ID: {current_id} ({i+1}/{len(self.all_data)})")
                
                try:
                    # Create tool with custom delays
                    tool = Tool(app=self.app, dlg=self.dlg)
                    
                    # Execute automation steps with delays and emergency stop checks
                    steps = [
                        ("Setting 'Cho thuc hien' mode", lambda: tool.click_thuc_hien(mode=data["isFirst"])),
                        (f"Setting start date: {data['ngay']}", lambda: tool.type_ngay_bat_dau(ngay=data["ngay"])),
                        (f"Setting end date: {data['ngay']}", lambda: tool.type_ngay_ket_thuc(ngay=data["ngay"])),
                        (f"Entering ID: {current_id}", lambda: tool.type_id(id=data["id"])),
                        ("Clicking reload", lambda: tool.click_reload()),
                        ("Selecting patient row", lambda: tool._double_click_position(coords=PATIENT_ROW)),
                        ("Filling medical procedure data", lambda: tool.fill_thu_thuat_data(data["thu_thuats"], mode=data["isFirst"])),
                        ("Clicking next", lambda: tool._click_position(coords=TIEP))
                    ]
                    
                    for step_name, step_func in steps:
                        if self.emergency_stop_flag or not self.is_running:
                            break
                            
                        # Check for pause before each step
                        while self.paused and self.is_running and not self.emergency_stop_flag:
                            time.sleep(0.5)
                            
                        if self.emergency_stop_flag or not self.is_running:
                            break
                            
                        self.log_message(f"  → {step_name}")
                        
                        # Execute the step
                        step_func()
                        
                        # Add delay between steps
                        step_delay = self.step_delay_var.get()
                        if step_delay > 0:
                            time.sleep(step_delay)
                    
                    if not self.emergency_stop_flag and self.is_running:
                        self.log_message(f"✅ Completed processing ID: {current_id}")
                    
                except Exception as e:
                    if self.emergency_stop_flag:
                        self.log_message(f"🛑 Emergency stop during ID {current_id}")
                        break
                    else:
                        self.log_message(f"❌ Error processing ID {current_id}: {str(e)}", "ERROR")
                        continue
                        
        except Exception as e:
            self.log_message(f"❌ Automation error: {str(e)}", "ERROR")
        finally:
            self.is_running = False
            self.paused = False
            self.emergency_stop_flag = False
            self.root.after(0, self.update_button_states)
            self.root.after(0, lambda: self.pause_btn.config(text="Pause"))
            
            if self.emergency_stop_flag:
                self.log_message("🛑 Automation stopped by emergency stop")
            elif self.current_index >= len(self.all_data) - 1:
                self.log_message("🎉 Automation completed successfully!")
            else:
                self.log_message("⏹️ Automation stopped")
                
    def check_queue(self):
        """Check for messages from worker thread"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                # Process message if needed
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.check_queue)
            
    def log_message(self, message, level="INFO"):
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        def update_log():
            self.log_text.config(state='normal')
            self.log_text.insert(tk.END, formatted_message)
            self.log_text.see(tk.END)
            self.log_text.config(state='disabled')
            
        if threading.current_thread() == threading.main_thread():
            update_log()
        else:
            self.root.after(0, update_log)
            
    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state='disabled')

    def auto_save_data(self):
        """Automatically save all data to CSV file."""
        try:
            if self.all_data:
                export_data_to_csv(self.all_data, self.auto_save_path)
                self.log_message(f"✓ Auto-saved {len(self.all_data)} records to {self.auto_save_path}")
            else:
                if os.path.exists(self.auto_save_path):
                    os.remove(self.auto_save_path)
        except Exception as e:
            self.log_message(f"✗ Auto-save failed: {str(e)}", "ERROR")
    
    def auto_load_data(self):
        """Automatically load data from auto-save file if it exists."""
        try:
            if os.path.exists(self.auto_save_path):
                self.data_file_path.set(self.auto_save_path)
                self.csv_data = read_data(self.auto_save_path)
                manual_entries = load_manual_entries_from_db()
                self.manual_data = load_manual_data_from_json(manual_entries)
                self.merge_all_data()
                self.update_data_table()
                self.log_message(f"✓ Auto-loaded {len(self.all_data)} records")
        except Exception as e:
            self.log_message(f"✗ Auto-load failed: {str(e)}", "ERROR")
    
    def on_app_close(self):
        """Handle application closing - auto-save data."""
        try:
            self.auto_save_data()
            self.root.destroy()
        except:
            self.root.destroy()

def main():
    initialize_database()
    root = tk.Tk()
    app = AutomationGUI(root)
    
    def on_closing():
        if app.is_running:
            if messagebox.askokcancel("Quit", "Automation is running. Do you want to stop and quit?"):
                app.stop_automation()
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()