import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import importlib.util
import json
# from pywinauto import Application  <-- REMOVED
from handle_data import read_data, export_data_to_csv, merge_csv_and_manual_data, load_manual_data_from_json, create_data_from_manual_input, validate_all_data
# from tool import Tool <-- REMOVED
import time
import os
import sys
import webbrowser
# import ctypes <-- REMOVED
import platform
from config_dialog import ConfigDialog
from database import initialize_database, load_manual_entries_from_db, get_window_title, set_window_title, get_arrow_mode_setting, set_arrow_mode_setting
from manual_entry import ManualEntryDialog
import config
from config import PATIENT_ROW, TIEP
from updater import get_current_version, check_for_update, download_update

GITHUB_REPO = "TrH203/Clinic-Auto-Fill"

class AutomationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Medical Data Automation Tool v{get_current_version()} (MAC TEST MODE)")
        self.root.geometry("1000x850")  # Increased size to fit all content
        # Set minimum size to prevent UI breaking
        self.root.minsize(950, 800)
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

        # Check for updates in background (non-blocking)
        threading.Thread(target=self._startup_update_check, daemon=True).start()

    def setup_ui(self):
        # Use direct frame instead of canvas for better layout
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)  # Data table row expands
        
        # Title
        title_label = ttk.Label(main_frame, text="Medical Data Automation Tool (Mac Test)", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="Data File", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="CSV File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        file_entry = ttk.Entry(file_frame, textvariable=self.data_file_path, state='readonly')
        file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        browse_btn = ttk.Button(file_frame, text="Chọn CSV", command=self.browse_file)
        browse_btn.grid(row=0, column=2, padx=(0, 5))
        
        manual_btn = ttk.Button(file_frame, text="Nhập Liệu", command=self.open_manual_entry)
        manual_btn.grid(row=0, column=3, padx=(0, 5))
        
        config_btn = ttk.Button(file_frame, text="⚙️ Cấu Hình", command=self.open_config_dialog)
        config_btn.grid(row=0, column=4, padx=(0, 5))
        
        export_btn = ttk.Button(file_frame, text="📄 Xuất CSV", command=self.export_to_csv)
        export_btn.grid(row=0, column=5, padx=(0, 5))
        
        validate_btn = ttk.Button(file_frame, text="🛡️ Kiểm Tra Dữ Liệu", command=self.validate_data)
        validate_btn.grid(row=0, column=6)

        update_btn = ttk.Button(file_frame, text="Cập Nhật", command=self.check_for_updates)
        update_btn.grid(row=0, column=7, padx=(5, 0))

        batch_btn = ttk.Button(file_frame, text="🧾 Batch IDs", command=self.open_batch_editor)
        batch_btn.grid(row=0, column=7, padx=(5, 0))
        
        # Data display table
        data_table_frame = ttk.LabelFrame(main_frame, text="Loaded Data", padding="10")
        data_table_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 10))
        data_table_frame.columnconfigure(0, weight=1)
        data_table_frame.rowconfigure(0, weight=1)
        
        # Create Treeview with scrollbars
        tree_scroll_y = ttk.Scrollbar(data_table_frame, orient="vertical")
        tree_scroll_x = ttk.Scrollbar(data_table_frame, orient="horizontal")
        
        self.data_tree = ttk.Treeview(data_table_frame, 
                                      columns=('isFirst', 'ID', 'Date', 'Time', 'Procedures', 'Staff'),
                                      show='headings',
                                      height=15,
                                      yscrollcommand=tree_scroll_y.set,
                                      xscrollcommand=tree_scroll_x.set)
        
        tree_scroll_y.config(command=self.data_tree.yview)
        tree_scroll_x.config(command=self.data_tree.xview)
        
        # Configure columns
        self.data_tree.heading('isFirst', text='Đã TH')
        self.data_tree.heading('ID', text='Patient ID')
        self.data_tree.heading('Date', text='Date')
        self.data_tree.heading('Time', text='Time')
        self.data_tree.heading('Procedures', text='Procedures')
        self.data_tree.heading('Staff', text='Staff')
        
        # Set smaller column widths for better fit on small screens
        self.data_tree.column('isFirst', width=40, minwidth=35, anchor='center')
        self.data_tree.column('ID', width=85, minwidth=70, anchor='center')
        self.data_tree.column('Date', width=80, minwidth=70, anchor='center')
        self.data_tree.column('Time', width=50, minwidth=45, anchor='center')
        self.data_tree.column('Procedures', width=130, minwidth=100, anchor='w')
        self.data_tree.column('Staff', width=160, minwidth=120, anchor='w')
        
        # Grid layout for tree and scrollbars
        self.data_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        tree_scroll_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        tree_scroll_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Bind double-click to edit entry
        self.data_tree.bind('<Double-Button-1>', self.edit_entry)
        # Bind single click on isFirst column to toggle
        self.data_tree.bind('<Button-1>', self.on_tree_click)
        # Enable multi-select with Ctrl/Shift
        self.data_tree.configure(selectmode='extended')
        
        # Buttons for Check All / Uncheck All / Delete Selected
        check_btn_frame = ttk.Frame(data_table_frame)
        check_btn_frame.grid(row=2, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Button(check_btn_frame, text="☑ Chọn tất cả", command=self.check_all_isfirst).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(check_btn_frame, text="☐ Bỏ chọn tất cả", command=self.uncheck_all_isfirst).grid(row=0, column=1, padx=(0, 5))
        ttk.Button(check_btn_frame, text="🗑️ Xóa đã chọn", command=self.delete_selected_rows).grid(row=0, column=2)
        
        
        # Connection section
        conn_frame = ttk.LabelFrame(main_frame, text="Application Connection (MOCKED)", padding="10")
        conn_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Target App Label
        current_title = get_window_title() or "Mac Test Window"
        short_title = current_title if len(current_title) < 40 else current_title[:37] + "..."
        self.target_app_label = ttk.Label(conn_frame, text=f"Target: {short_title}", 
                                         foreground="blue", width=45)
        self.target_app_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # Select App Button
        select_app_btn = ttk.Button(conn_frame, text="🔍 Chọn Cửa Sổ", 
                                  command=self.select_target_window)
        select_app_btn.grid(row=0, column=1, padx=(0, 5))
        
        # Status Label
        self.conn_status_label = ttk.Label(conn_frame, text="Status: Disconnected", 
                                          foreground="red")
        self.conn_status_label.grid(row=0, column=3, padx=(10, 10))
        
        # Connect Button
        connect_btn = ttk.Button(conn_frame, text="Kết Nối (Test)", 
                                command=self.connect_to_app)
        connect_btn.grid(row=0, column=2)
        
        # Control section
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.start_btn = ttk.Button(control_frame, text="Bắt Đầu Tự Động", 
                                   command=self.start_automation, state='disabled')
        self.start_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.stop_btn = ttk.Button(control_frame, text="Dừng Tự Động", 
                                  command=self.stop_automation, state='disabled')
        self.stop_btn.grid(row=0, column=1, padx=(0, 5))
        
        self.pause_btn = ttk.Button(control_frame, text="Tạm Dừng", 
                                   command=self.pause_automation, state='disabled')
        self.pause_btn.grid(row=0, column=2, padx=(0, 5))
        
        # Emergency stop button
        self.emergency_btn = ttk.Button(control_frame, text="🛑 DỪNG KHẨN CẤP", 
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
        
        # Arrow Date Checkbox
        self.arrow_date_var = tk.BooleanVar(value=get_arrow_mode_setting())
        self.arrow_date_var.trace('w', lambda *args: set_arrow_mode_setting(self.arrow_date_var.get()))
        arrow_date_check = ttk.Checkbutton(delay_frame, text="Ngày Mũi Tên", variable=self.arrow_date_var)
        arrow_date_check.grid(row=0, column=4, padx=(10, 0))
        
        # Debug Mode Checkbox
        self.debug_mode_var = tk.BooleanVar(value=True)  # Default to True for debugging
        debug_check = ttk.Checkbutton(delay_frame, text="🐛 Debug Mode", variable=self.debug_mode_var)
        debug_check.grid(row=0, column=5, padx=(10, 0))
        
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
        hotkey_frame.grid(row=6, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0))
        
        hotkey_label = ttk.Label(hotkey_frame, text="🔥 Hotkey: Press F12 or Esc for Emergency Stop (Mock)", 
                               font=('Arial', 9, 'bold'), foreground="red")
        hotkey_label.grid(row=0, column=0, sticky=tk.W)
        
        # Hidden log widget (for backward compatibility with log_message calls)
        # Log messages will be printed to console instead
        self.log_text = scrolledtext.ScrolledText(main_frame, height=1, state='disabled')
        # Don't grid it - keep it hidden
        
    def setup_hotkeys(self):
        """Setup global hotkey for emergency stop"""
        # Bind F12 key to emergency stop
        self.root.bind('<F12>', lambda event: self.emergency_stop())
        
        # Make sure the window can capture F12 even when not focused
        self.root.focus_set()
        
        # Also bind Escape key as alternative emergency stop
        self.root.bind('<Escape>', lambda event: self.emergency_stop() if self.is_running else None)

    def _get_auto_schedule_module(self):
        """Lazy-load ai/auto_schedule.py for batch generation."""
        if hasattr(self, "_auto_schedule_module") and self._auto_schedule_module:
            return self._auto_schedule_module

        module_path = os.path.join(os.path.dirname(__file__), "ai", "auto_schedule.py")
        spec = importlib.util.spec_from_file_location("auto_schedule", module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self._auto_schedule_module = module
        return module
        
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
            messagebox.showerror("Lỗi", f"Không thể tải tập tin:\n{str(e)}")
    
    def open_manual_entry(self):
        """Open manual entry dialog."""
        try:
            dialog = ManualEntryDialog(self.root, on_save_callback=self.on_manual_entry_saved, existing_data=self.all_data)
            result = dialog.show()
        except Exception as e:
            self.log_message(f"✗ Error opening manual entry: {str(e)}", "ERROR")
            messagebox.showerror("Lỗi", f"Không thể mở nhập liệu thủ công:\n{str(e)}")
    
    def open_config_dialog(self):
        """Open the staff configuration dialog."""
        try:
            dialog = ConfigDialog(self.root)
            dialog.show()
            # After config is saved, we might want to refresh manual entry if it's open
            self.log_message("✓ Configuration updated")
        except Exception as e:
            self.log_message(f"✗ Failed to open config dialog: {str(e)}", "ERROR")
            messagebox.showerror("Lỗi", f"Không thể mở cấu hình:\n{str(e)}")

    def open_batch_editor(self):
        """Open dialog to edit batch IDs and run auto scheduling."""
        try:
            auto_schedule = self._get_auto_schedule_module()
            batch_path = os.path.join(os.path.dirname(__file__), "ai", "batch.txt")
            slots_path = os.path.join(os.path.dirname(__file__), "ai", "slots_by_date.json")
            default_output = os.path.join(os.path.dirname(__file__), "ai", "generated_schedule.csv")
            available_procedures = sorted(list(config.thu_thuat_dur_mapper.keys()))

            dialog = tk.Toplevel(self.root)
            dialog.title("Batch IDs")
            dialog.geometry("900x620")
            dialog.resizable(True, True)
            dialog.transient(self.root)
            dialog.grab_set()

            main_frame = ttk.Frame(dialog, padding="12")
            main_frame.pack(fill="both", expand=True)
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(2, weight=1)

            header_frame = ttk.Frame(main_frame)
            header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
            header_frame.columnconfigure(5, weight=1)

            ttk.Label(header_frame, text=f"Batch file: {batch_path}").grid(
                row=0, column=0, columnspan=6, sticky=tk.W, pady=(0, 6)
            )

            ttk.Label(header_frame, text="Ngày bắt đầu (DD-MM-YYYY):").grid(
                row=1, column=0, sticky=tk.W
            )
            start_date_var = tk.StringVar(value=time.strftime("%d-%m-%Y"))
            ttk.Entry(header_frame, textvariable=start_date_var, width=15).grid(
                row=1, column=1, sticky=tk.W, padx=(5, 15)
            )

            ttk.Label(header_frame, text="Ngày kết thúc (DD-MM-YYYY):").grid(
                row=1, column=2, sticky=tk.W
            )
            end_date_var = tk.StringVar(value=time.strftime("%d-%m-%Y"))
            ttk.Entry(header_frame, textvariable=end_date_var, width=15).grid(
                row=1, column=3, sticky=tk.W, padx=(5, 15)
            )

            ttk.Label(header_frame, text="Seed:").grid(row=1, column=4, sticky=tk.W)
            seed_var = tk.StringVar(value="")
            ttk.Entry(header_frame, textvariable=seed_var, width=8).grid(
                row=1, column=5, sticky=tk.W, padx=(5, 0)
            )

            ttk.Label(header_frame, text="Output CSV:").grid(
                row=2, column=0, sticky=tk.W, pady=(6, 0)
            )
            output_var = tk.StringVar(value="")
            output_entry = ttk.Entry(header_frame, textvariable=output_var, width=60)
            output_entry.grid(row=2, column=1, columnspan=4, sticky=(tk.W, tk.E), pady=(6, 0))
            def browse_output():
                filename = filedialog.asksaveasfilename(
                    title="Lưu CSV",
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                )
                if filename:
                    output_var.set(filename)
            ttk.Button(header_frame, text="Chọn...", command=browse_output).grid(
                row=2, column=5, padx=(5, 0), pady=(6, 0)
            )

            # Scrollable table for batch rows
            table_frame = ttk.Frame(main_frame)
            table_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 5))
            table_frame.columnconfigure(0, weight=1)
            table_frame.rowconfigure(0, weight=1)

            canvas = tk.Canvas(table_frame, height=280)
            scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
            inner = ttk.Frame(canvas)

            inner.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window=inner, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)

            canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

            ttk.Label(inner, text="Patient ID").grid(row=0, column=0, padx=4, pady=2, sticky=tk.W)
            for i in range(4):
                ttk.Label(inner, text=f"Thủ thuật {i+1}").grid(row=0, column=1 + i, padx=4, pady=2, sticky=tk.W)
            ttk.Label(inner, text="").grid(row=0, column=5, padx=4, pady=2)

            rows = []
            # Store the last used procedure values to pre-fill new rows
            last_procedures = [None, None, None, None]

            def refresh_row_positions():
                for idx, row in enumerate(rows, start=1):
                    row["id_entry"].grid_configure(row=idx)
                    for j, combo in enumerate(row["proc_combos"]):
                        combo.grid_configure(row=idx, column=1 + j)
                    row["remove_btn"].grid_configure(row=idx, column=5)

            def remove_row(row):
                row["id_entry"].destroy()
                for combo in row["proc_combos"]:
                    combo.destroy()
                row["remove_btn"].destroy()
                rows.remove(row)
                refresh_row_positions()

            def add_row(patient_id="", procedures=None):
                nonlocal last_procedures
                # If no procedures specified and there are existing rows, use last row's values
                if procedures is None and rows:
                    # Get procedures from the last row
                    last_row = rows[-1]
                    procedures = [v.get() for v in last_row["proc_vars"]]
                row_index = len(rows) + 1
                id_var = tk.StringVar(value=patient_id)
                id_entry = ttk.Entry(inner, textvariable=id_var, width=14)
                id_entry.grid(row=row_index, column=0, padx=4, pady=2, sticky=tk.W)

                proc_vars = []
                proc_combos = []
                for j in range(4):
                    var = tk.StringVar()
                    combo = ttk.Combobox(
                        inner,
                        textvariable=var,
                        values=available_procedures,
                        width=12,
                        state="readonly",
                    )
                    combo.grid(row=row_index, column=1 + j, padx=4, pady=2, sticky=tk.W)
                    if procedures and j < len(procedures):
                        var.set(procedures[j])
                    proc_vars.append(var)
                    proc_combos.append(combo)

                remove_btn = ttk.Button(inner, text="X", width=3)
                row = {
                    "id_var": id_var,
                    "proc_vars": proc_vars,
                    "id_entry": id_entry,
                    "proc_combos": proc_combos,
                    "remove_btn": remove_btn,
                }
                remove_btn.configure(command=lambda r=row: remove_row(r))
                remove_btn.grid(row=row_index, column=5, padx=4, pady=2)
                rows.append(row)

            def load_from_lines(lines):
                for row in list(rows):
                    remove_row(row)
                for line in lines:
                    raw = line.strip()
                    if not raw or raw.startswith("#"):
                        continue
                    parts = [p.strip() for p in raw.split(";")]
                    if not parts:
                        continue
                    patient_id = parts[0]
                    proc_list = []
                    if len(parts) > 1 and parts[1]:
                        proc_list = [p.strip() for p in parts[1].split("-") if p.strip()]
                    add_row(patient_id, proc_list)

            def load_default():
                # Always start with an empty row (disabled auto-load from batch.txt)
                add_row()

            def browse_and_load():
                filename = filedialog.askopenfilename(
                    title="Chọn file batch",
                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                )
                if filename:
                    with open(filename, "r", encoding="utf-8") as f:
                        load_from_lines(f.readlines())

            def collect_rows():
                patients = []
                errors = []
                for idx, row in enumerate(rows, start=1):
                    patient_id = row["id_var"].get().strip()
                    procs = [v.get().strip() for v in row["proc_vars"]]
                    if not patient_id and not any(procs):
                        continue
                    if not patient_id:
                        errors.append(f"Dòng {idx}: thiếu Patient ID")
                    if any(not p for p in procs):
                        errors.append(f"Dòng {idx}: thiếu thủ thuật (cần đủ 4)")
                    if patient_id and all(procs):
                        patients.append({"patient_id": patient_id, "procedures": procs})
                if errors:
                    messagebox.showerror("Lỗi", "\n".join(errors))
                    return None
                return patients

            def save_batch():
                patients = collect_rows()
                if patients is None:
                    return
                # Open file dialog to choose save location
                filename = filedialog.asksaveasfilename(
                    title="Lưu file batch",
                    defaultextension=".txt",
                    initialfile="batch.txt",
                    filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                )
                if not filename:
                    return
                with open(filename, "w", encoding="utf-8") as f:
                    for patient in patients:
                        line = f"{patient['patient_id']};" + "-".join(patient["procedures"])
                        f.write(line + "\n")
                messagebox.showinfo("Thành Công", f"Đã lưu batch file:\n{filename}")

            def run_batch():
                patients = collect_rows()
                if patients is None or not patients:
                    messagebox.showerror("Lỗi", "Vui lòng nhập ít nhất 1 Patient ID.")
                    return

                start_date = start_date_var.get().strip()
                end_date = end_date_var.get().strip()
                if not start_date or not end_date:
                    messagebox.showerror("Lỗi", "Vui lòng nhập ngày bắt đầu và ngày kết thúc.")
                    return

                seed_str = seed_var.get().strip()
                if seed_str:
                    try:
                        seed = int(seed_str)
                    except ValueError:
                        messagebox.showerror("Lỗi", "Seed phải là số nguyên hoặc để trống.")
                        return
                else:
                    seed = None  # Random seed each time

                slots_by_date = None
                slots_by_procedure = None
                time_slots = []

                if os.path.exists(slots_path):
                    with open(slots_path, "r", encoding="utf-8") as f:
                        slots_payload = json.load(f)
                    if auto_schedule.is_procedure_payload(slots_payload):
                        slots_by_procedure = auto_schedule.normalize_proc_slots(slots_payload)
                    else:
                        slots_by_date = auto_schedule.read_slots_by_date(slots_payload)
                else:
                    time_slots = auto_schedule.normalize_time_slots(
                        getattr(config, "AUTO_SCHEDULE_TIME_SLOTS", [])
                    )

                try:
                    records = auto_schedule.generate_schedule_batch(
                        patients=patients,
                        procedures_default=None,
                        start_date=start_date,
                        end_date=end_date,
                        time_slots=time_slots,
                        slots_by_date=slots_by_date,
                        slots_by_procedure=slots_by_procedure,
                        slots_kind=getattr(config, "AUTO_SCHEDULE_TIME_SLOTS_KIND", "CD"),
                        seed=seed,
                    )
                except Exception as e:
                    messagebox.showerror("Lỗi", f"Không thể tạo lịch:\n{str(e)}")
                    return

                output_path = output_var.get().strip()
                if output_path:
                    try:
                        export_data_to_csv(records, output_path)
                    except Exception as e:
                        messagebox.showerror("Lỗi", f"Không thể lưu CSV:\n{str(e)}")
                        return

                self.csv_data = records
                if output_path:
                    self.data_file_path.set(output_path)
                self.merge_all_data()
                self.update_data_table()
                self.update_button_states()
                self.log_message(f"✓ Generated {len(records)} records from batch IDs")
                messagebox.showinfo("Thành Công", f"Đã tạo {len(records)} lịch hẹn.")

            load_default()

            actions_frame = ttk.Frame(main_frame)
            actions_frame.grid(row=3, column=0, sticky=tk.W, pady=(6, 0))

            ttk.Button(actions_frame, text="Thêm dòng", command=lambda: add_row()).grid(
                row=0, column=0, padx=(0, 6)
            )
            ttk.Button(actions_frame, text="Đọc File...", command=browse_and_load).grid(
                row=0, column=1, padx=(0, 6)
            )
            ttk.Button(actions_frame, text="Lưu batch...", command=save_batch).grid(
                row=0, column=2, padx=(0, 6)
            )
            ttk.Button(actions_frame, text="Chạy batch", command=run_batch).grid(
                row=0, column=3, padx=(0, 6)
            )
            ttk.Button(actions_frame, text="Đóng", command=dialog.destroy).grid(
                row=0, column=4
            )

        except Exception as e:
            self.log_message(f"✗ Failed to open batch editor: {str(e)}", "ERROR")
            messagebox.showerror("Lỗi", f"Không thể mở batch editor:\n{str(e)}")
    
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
            messagebox.showerror("Lỗi", "Không tìm thấy dữ liệu.")
            return
        
        try:
            # Create a copy for editing
            import copy
            edit_data = copy.deepcopy(target_data)
            
            # Open manual entry dialog with existing data
            dialog = ManualEntryDialog(self.root, 
                                      on_save_callback=lambda d: self.on_entry_edited(d, is_manual, data_index),
                                      initial_data=edit_data,
                                      on_delete_callback=lambda: self.delete_entry(is_manual, data_index),
                                      existing_data=self.all_data)
            dialog.show()
            
        except Exception as e:
            self.log_message(f"✗ Error opening edit dialog: {str(e)}", "ERROR")
            messagebox.showerror("Lỗi", f"Không thể mở cửa sổ chỉnh sửa:\n{str(e)}")
    
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
            messagebox.showerror("Lỗi", f"Không thể xóa bản ghi:\n{str(e)}")
    
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
        for idx, record in enumerate(self.csv_data):
            patient_id = record.get('id', '')
            date = record.get('ngay', '')
            is_first = record.get('isFirst', False)
            is_first_display = '☑' if is_first else '☐'
            
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
            
            self.data_tree.insert('', 'end', iid=f'csv_{idx}', values=(is_first_display, patient_id, date, time_str, procedures, staff))
        
        # Add manual data
        for idx, record in enumerate(self.manual_data):
            patient_id = record.get('id', '')
            date = record.get('ngay', '')
            is_first = record.get('isFirst', False)
            is_first_display = '☑' if is_first else '☐'
            
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
            
            self.data_tree.insert('', 'end', iid=f'manual_{idx}', values=(is_first_display, patient_id, date, time_str, procedures, staff))
    
    def on_tree_click(self, event):
        """Handle click on tree to toggle isFirst checkbox."""
        region = self.data_tree.identify_region(event.x, event.y)
        if region != 'cell':
            return
        
        column = self.data_tree.identify_column(event.x)
        # Column #1 is isFirst
        if column != '#1':
            return
        
        item = self.data_tree.identify_row(event.y)
        if not item:
            return
        
        # Toggle the isFirst value in the data
        if item.startswith('csv_'):
            idx = int(item.replace('csv_', ''))
            if idx < len(self.csv_data):
                current = self.csv_data[idx].get('isFirst', False)
                self.csv_data[idx]['isFirst'] = not current
        elif item.startswith('manual_'):
            idx = int(item.replace('manual_', ''))
            if idx < len(self.manual_data):
                current = self.manual_data[idx].get('isFirst', False)
                self.manual_data[idx]['isFirst'] = not current
        
        # Update table
        self.merge_all_data()
        self.update_data_table()
    
    def check_all_isfirst(self):
        """Set isFirst to True for all records."""
        for record in self.csv_data:
            record['isFirst'] = True
        for record in self.manual_data:
            record['isFirst'] = True
        self.merge_all_data()
        self.update_data_table()
    
    def uncheck_all_isfirst(self):
        """Set isFirst to False for all records."""
        for record in self.csv_data:
            record['isFirst'] = False
        for record in self.manual_data:
            record['isFirst'] = False
        self.merge_all_data()
        self.update_data_table()
    
    def delete_selected_rows(self):
        """Delete selected rows from the table."""
        selected = self.data_tree.selection()
        if not selected:
            messagebox.showwarning("Chưa chọn", "Vui lòng chọn các hàng cần xóa.\n(Giữ Ctrl hoặc Shift để chọn nhiều hàng)")
            return
        
        if not messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa {len(selected)} hàng đã chọn?"):
            return
        
        # Collect indices to delete (in reverse order to avoid index shifting)
        csv_to_delete = []
        manual_to_delete = []
        
        for item in selected:
            if item.startswith('csv_'):
                idx = int(item.replace('csv_', ''))
                csv_to_delete.append(idx)
            elif item.startswith('manual_'):
                idx = int(item.replace('manual_', ''))
                manual_to_delete.append(idx)
        
        # Delete in reverse order to maintain correct indices
        for idx in sorted(csv_to_delete, reverse=True):
            if idx < len(self.csv_data):
                del self.csv_data[idx]
        
        for idx in sorted(manual_to_delete, reverse=True):
            if idx < len(self.manual_data):
                del self.manual_data[idx]
        
        self.merge_all_data()
        self.update_data_table()
        self.log_message(f"✓ Đã xóa {len(selected)} hàng")
            
    
    def export_to_csv(self):
        """Export all data (CSV + Manual) to CSV file in import format."""
        if not self.all_data:
            messagebox.showwarning("No Data", "No data to export.")
            return
        
        # Validate data before exporting
        try:
            errors = validate_all_data(self.all_data)
            
            if errors:
                self.log_message(f"✗ Validation failed with {len(errors)} errors.", "ERROR")
                
                # Format errors for display
                error_text = f"Tìm thấy {len(errors)} xung đột:\n\n"
                # Limit to first 5 for messagebox to avoid overflow
                display_errors = errors[:5]
                error_text += "\n\n".join(display_errors)
                
                if len(errors) > 5:
                    error_text += f"\n\n... and {len(errors) - 5} more."
                
                error_text += "\n\nVui lòng sửa các xung đột này trước khi xuất."
                
                # Ask user if they want to proceed anyway
                proceed = messagebox.askyesno(
                    "Định Dạng Sai", 
                    error_text + "\n\nBạn có muốn xuất dù sao không?",
                    icon='warning'
                )
                
                if not proceed:
                    self.log_message("Export cancelled due to validation errors.")
                    return
            else:
                self.log_message("✓ Validation passed! No conflicts found.")
        except Exception as e:
            self.log_message(f"✗ Validation error: {str(e)}", "ERROR")
            
            # Ask user if they want to proceed anyway
            proceed = messagebox.askyesno(
                "Lỗi Kiểm Tra", 
                f"Lỗi trong quá trình kiểm tra:\n{str(e)}\n\nBạn có muốn xuất dù sao không?",
                icon='warning'
            )
            
            if not proceed:
                self.log_message("Export cancelled due to validation error.")
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
            messagebox.showinfo("Xuất Thành Công", 
                              f"Đã xuất {len(self.all_data)} bản ghi ra:\n{filename}")
        
        except Exception as e:
            self.log_message(f"✗ Failed to export CSV: {e}", "ERROR")
            messagebox.showerror("Lỗi Xuất", f"Không thể xuất CSV:\n{e}")
    
    def validate_data(self):
        """Validate currently loaded data for conflicts."""
        if not self.all_data:
            messagebox.showwarning("No Data", "No data to validate. Please load CSV or add manual entries.")
            return
            
        try:
            errors = validate_all_data(self.all_data)
            
            if errors:
                self.log_message(f"✗ Validation failed with {len(errors)} errors.", "ERROR")
                
                # Format errors for display
                error_text = f"Found {len(errors)} conflict(s):\n\n"
                # Limit to first 10 for messagebox to avoid overflow
                display_errors = errors[:10]
                error_text += "\n\n".join(display_errors)
                
                if len(errors) > 10:
                    error_text += f"\n\n... and {len(errors) - 10} more."
                    
                messagebox.showerror("Định Dạng Sai", error_text)
            else:
                self.log_message("✓ Validation passed! No conflicts found.")
                messagebox.showinfo("Kiểm Tra Thành Công", 
                                  "Không tìm thấy xung đột Nhóm 1 (Nhân Viên 1/3).")
        except Exception as e:
            self.log_message(f"✗ Validation error: {str(e)}", "ERROR")
            messagebox.showerror("Lỗi", f"Lỗi trong quá trình kiểm tra:\n{str(e)}")
    
    def connect_to_app(self):
        # MOCKED FOR MAC
        # target_title = get_window_title() # Not needed for mock
        self.app = "MockApp" # Fake object
        self.dlg = "MockDlg" # Fake object
        
        self.conn_status_label.config(text="Status: Connected (MOCK) ✓", foreground="green")
        self.log_message(f"✓ Connected to Mock App successfully (Mac Test Mode)")
        self.update_button_states()
        
    def select_target_window(self):
        """Open dialog to select target window (MOCKED)."""
        messagebox.showinfo("Mac Test Mode", "Choosing window is not supported/needed in Mac Test Mode.\nOnly Data Entry/Export features are available.")
            
    def update_button_states(self):
        has_data = len(self.all_data) > 0
        is_connected = self.app is not None and self.dlg is not None
        can_start = has_data and is_connected and not self.is_running
        
        self.start_btn.config(state='normal' if can_start else 'disabled')
        self.stop_btn.config(state='normal' if self.is_running else 'disabled')
        self.pause_btn.config(state='normal' if self.is_running else 'disabled')
        
    def start_automation(self):
        import json
        with open("test.json", "w", encoding="utf-8") as f:
            json.dump(self.all_data, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Mac Test Mode", "Automation is not supported in Mac Test Mode.\nThis mode is only for Data Entry, Validation, and CSV Export.")
        return 
            
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
            messagebox.showinfo("Đã Tạm Dừng", 
                               "Tự động hóa đã tạm dừng. Nhấn 'Tạm Dừng' lại để tiếp tục.")
        else:
            self.pause_btn.config(text="Pause")
            self.log_message("▶️ Automation Resumed")
            # Give user time to focus back on target window
            messagebox.showinfo("Tiếp Tục", 
                               "Đang tiếp tục tự động hóa...")
            self.root.after(3000, lambda: self.log_message("🔄 Automation continuing..."))
        
    # ===== Auto-Update Methods =====

    def _startup_update_check(self):
        """Background check for updates on app startup. Only logs, no popup."""
        try:
            update_info = check_for_update(get_current_version(), GITHUB_REPO)
            if update_info:
                self.root.after(0, lambda: self.log_message(
                    f"Phiên bản mới v{update_info['version']} đã có! Nhấn nút 'Cập Nhật' để cập nhật."
                ))
        except Exception:
            pass

    def check_for_updates(self):
        """Manual update check triggered by button."""
        self.log_message("Checking for updates...")
        threading.Thread(target=self._do_check_for_updates, daemon=True).start()

    def _do_check_for_updates(self):
        """Worker thread for manual update check."""
        try:
            update_info = check_for_update(get_current_version(), GITHUB_REPO)
            if update_info:
                self.root.after(0, lambda: self._show_update_dialog(update_info))
            else:
                self.root.after(0, lambda: [
                    self.log_message("Bạn đang dùng phiên bản mới nhất!"),
                    messagebox.showinfo("Cập Nhật", f"Bạn đang dùng phiên bản mới nhất v{get_current_version()}!")
                ])
        except Exception as e:
            self.root.after(0, lambda: self.log_message(f"Could not check for updates: {e}"))

    def _show_update_dialog(self, update_info):
        """Show update available dialog on the main thread."""
        changelog = update_info['changelog']
        if len(changelog) > 500:
            changelog = changelog[:500] + "..."

        result = messagebox.askyesno(
            "Phiên Bản Mới",
            f"Phiên bản v{update_info['version']} đã có!\n\n"
            f"{changelog}\n\n"
            f"Cập nhật ngay?"
        )
        if result:
            messagebox.showinfo(
                "Mac Test Mode",
                f"On Windows, this would download and install v{update_info['version']}.\n"
                "Auto-update is only supported on Windows."
            )

    # ===== End Auto-Update Methods =====

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

    def log_message(self, message, level="INFO", debug_data=None):
        timestamp = time.strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # If debug mode is on and we have debug data, add it
        if self.debug_mode_var.get() and debug_data:
            formatted_message += f"           [DEBUG] {debug_data}\n"
        
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
    # Removed Windows Admin check
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
