import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
from pywinauto import Application
from handle_data import read_data
from tool import Tool
import time
import os
import sys
import requests
from config import PATIENT_ROW, TIEP
from database import get_current_version_from_db, initialize_database

CURRENT_VERSION = get_current_version_from_db()
GITHUB_REPO = "TrH203/Clinic-Auto-Fill"

class AutomationGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"Medical Data Automation Tool - v{CURRENT_VERSION}")
        self.root.geometry("800x600")
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
        self.current_index = 0
        
        self.update_info = None

        # Queue for thread communication
        self.log_queue = queue.Queue()
        
        self.setup_ui()
        self.setup_hotkeys()
        self.check_queue()
        self.check_for_updates()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
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
        
        browse_btn = ttk.Button(file_frame, text="Browse", command=self.browse_file)
        browse_btn.grid(row=0, column=2)
        
        # Connection section
        conn_frame = ttk.LabelFrame(main_frame, text="Application Connection", padding="10")
        conn_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.conn_status_label = ttk.Label(conn_frame, text="Status: Not Connected", 
                                          foreground="red")
        self.conn_status_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        connect_btn = ttk.Button(conn_frame, text="Connect to Application", 
                               command=self.connect_to_app)
        connect_btn.grid(row=0, column=1)
        
        # Control section
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
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
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, state='disabled')
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Clear log button
        clear_log_btn = ttk.Button(log_frame, text="Clear Log", command=self.clear_log)
        clear_log_btn.grid(row=1, column=0, sticky=tk.E, pady=(5, 0))
        
        # Status bar
        status_frame = ttk.Frame(self.root, padding="5")
        status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))

        self.version_label = ttk.Label(status_frame, text=f"Version: {CURRENT_VERSION}")
        self.version_label.grid(row=0, column=0, sticky=tk.W)

        self.update_btn = ttk.Button(status_frame, text="Check for Updates",
                                    command=self.prompt_update, state='normal')
        self.update_btn.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

    def check_for_updates(self):
        """Checks for updates in a separate thread."""
        threading.Thread(target=self._check_for_updates_thread, daemon=True).start()

    def _check_for_updates_thread(self):
        """The actual update check logic."""
        try:
            api_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
            response = requests.get(api_url)
            response.raise_for_status()

            latest_release = response.json()
            latest_version = latest_release["tag_name"]

            if latest_version > CURRENT_VERSION:
                self.update_info = latest_release
                self.root.after(0, self._enable_update_button)
        except Exception as e:
            self.log_message(f"✗ Failed to check for updates: {e}", "ERROR")

    def _enable_update_button(self):
        """Enables the update button and changes its style."""
        style = ttk.Style()
        style.configure("Update.TButton", foreground="red", font=('Arial', 9, 'bold'))
        self.update_btn.config(text="Update Available!", style="Update.TButton")

    def prompt_update(self):
        """Prompts the user to update the application."""
        if not self.update_info:
            messagebox.showinfo("No Updates", "You are using the latest version of the application.")
            return

        latest_version = self.update_info["tag_name"]
        update_message = f"A new version ({latest_version}) is available. Do you want to download and install it?"

        if messagebox.askyesno("Update Available", update_message):
            self.download_and_update()

    def download_and_update(self):
        """Downloads the latest release and launches the updater."""
        try:
            asset = self.update_info["assets"][0]
            download_url = asset["browser_download_url"]
            filename = asset["name"]

            response = requests.get(download_url, stream=True)
            response.raise_for_status()

            with open(filename, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.log_message(f"✓ Downloaded {filename}")

            # Launch the updater script
            latest_version = self.update_info["tag_name"]
            subprocess.Popen([sys.executable, "updater.py", os.path.basename(sys.argv[0]), filename, latest_version])
            self.root.destroy()

        except Exception as e:
            self.log_message(f"✗ Failed to download or apply update: {e}", "ERROR")
            messagebox.showerror("Update Error", f"Failed to download or apply update:\n{e}")

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
            self.all_data = read_data(self.data_file_path.get())
            self.log_message(f"✓ Loaded {len(self.all_data)} records from file")
            self.progress_bar['maximum'] = len(self.all_data)
            self.progress_var.set(f"0/{len(self.all_data)}")
            self.update_button_states()
        except Exception as e:
            self.log_message(f"✗ Error loading file: {str(e)}", "ERROR")
            messagebox.showerror("Error", f"Failed to load data file:\n{str(e)}")
            
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