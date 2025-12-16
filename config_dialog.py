import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import config
from database import get_disabled_staff, set_disabled_staff, add_doctor_leave, get_all_doctor_leaves, delete_doctor_leave

class ConfigDialog:
    def __init__(self, parent):
        """Initialize the config dialog."""
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Configuration")
        self.dialog.geometry("800x650")  # Increased from 600 to 800 for two columns
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.center_dialog()
        
        # Store checkbox variables
        self.checkbox_vars = {}
        
        # Store leave tree reference
        self.leave_tree = None
        
        self.setup_ui()
    
    def center_dialog(self):
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()
        
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"+{x}+{y}")
    
    def setup_ui(self):
        """Setup the user interface with tabs."""
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Configuration", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)
        
        # Tab 1: Staff Availability
        self.setup_staff_tab(notebook)
        
        # Tab 2: Leave Schedule
        self.setup_leave_tab(notebook)
        
        # Buttons at bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(15, 0))
        
        close_btn = ttk.Button(button_frame, text="Close", command=self.dialog.destroy)
        close_btn.pack()
    
    def setup_staff_tab(self, notebook):
        """Setup the staff availability tab."""
        staff_frame = ttk.Frame(notebook, padding="15")
        notebook.add(staff_frame, text="Staff Availability")
        
        # Info label
        info_label = ttk.Label(staff_frame, 
                              text="Uncheck staff members to disable them from manual entry and automation",
                              font=('Arial', 9), foreground="gray", wraplength=500)
        info_label.pack(pady=(0, 15))
        
        # Main container for the two lists
        lists_container = ttk.Frame(staff_frame)
        lists_container.pack(fill="both", expand=True)
        
        # Initialize vars for all potential staff
        disabled_staff = get_disabled_staff()
        all_keys = set(config.staff_p1_p3.keys()) | set(config.staff_p2.keys())
        
        for key in all_keys:
            self.checkbox_vars[key] = tk.BooleanVar(value=key not in disabled_staff)
            
        def create_staff_list(parent, title, staff_dict):
            frame = ttk.LabelFrame(parent, text=title, padding="10")
            
            # Scrollbar setup
            canvas = tk.Canvas(frame)
            scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            scrollable_frame = ttk.Frame(canvas)
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Populate
            for short_name, full_name in sorted(staff_dict.items(), key=lambda x: x[1]):
                # Use shared variable
                var = self.checkbox_vars[short_name]
                cb = ttk.Checkbutton(scrollable_frame, 
                                    text=f"{full_name} ({short_name})",
                                    variable=var)
                cb.pack(anchor="w", pady=2)
                
                # Add mousewheel scrolling
                def _on_mousewheel(event, c=canvas):
                    c.yview_scroll(int(-1*(event.delta/120)), "units")
                cb.bind("<MouseWheel>", _on_mousewheel)
            
            frame.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
            
            return frame

        # Group 1 List
        f1 = create_staff_list(lists_container, "Group 1 (Staff 1 & 3)", config.staff_p1_p3)
        f1.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Group 2 List
        f2 = create_staff_list(lists_container, "Group 2 (Staff 2)", config.staff_p2)
        f2.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Save button for this tab
        save_btn = ttk.Button(staff_frame, text="💾 Save", command=self.save_staff_config, 
                             style="Accent.TButton")
        save_btn.pack(pady=(15, 0))
    
    def setup_leave_tab(self, notebook):
        """Setup the leave schedule tab."""
        leave_frame = ttk.Frame(notebook, padding="15")
        notebook.add(leave_frame, text="Leave Schedule")
        
        # Add leave section
        add_frame = ttk.LabelFrame(leave_frame, text="Add Leave", padding="10")
        add_frame.pack(fill="x", pady=(0, 15))
        
        # Doctor selection
        ttk.Label(add_frame, text="Doctor:").grid(row=0, column=0, sticky=tk.W, pady= 5)
        self.leave_staff_var = tk.StringVar()
        staff_combo = ttk.Combobox(add_frame, textvariable=self.leave_staff_var, 
                                   values=sorted([f"{v} ({k})" for k, v in config.map_ys_bs.items()]),
                                   width=30)
        staff_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Date
        ttk.Label(add_frame, text="Date:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.leave_date_var = tk.StringVar(value=datetime.now().strftime("%d-%m-%Y"))
        date_entry = ttk.Entry(add_frame, textvariable=self.leave_date_var, width=32)
        date_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        ttk.Label(add_frame, text="(DD-MM-YYYY)", font=('Arial', 8), foreground="gray").grid(
            row=1, column=2, padx=(5, 0))
        
        # Session
        ttk.Label(add_frame, text="Session:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.leave_session_var = tk.StringVar(value="morning")
        session_frame = ttk.Frame(add_frame)
        session_frame.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Radiobutton(session_frame, text="Sáng (7h-12h)", variable=self.leave_session_var, 
                       value="morning").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(session_frame, text="Chiều (13h-17h)", variable=self.leave_session_var, 
                       value="afternoon").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(session_frame, text="Cả ngày", variable=self.leave_session_var, 
                       value="full_day").pack(side="left")
        
        # Reason
        ttk.Label(add_frame, text="Reason:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.leave_reason_var = tk.StringVar()
        reason_entry = ttk.Entry(add_frame, textvariable=self.leave_reason_var, width=32)
        reason_entry.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Add button
        add_btn = ttk.Button(add_frame, text="Add Leave", command=self.add_leave)
        add_btn.grid(row=4, column=1, pady=(10, 0))
        
        add_frame.columnconfigure(1, weight=1)
        
        # Current leaves section
        leaves_frame = ttk.LabelFrame(leave_frame, text="Current Leaves", padding="10")
        leaves_frame.pack(fill="both", expand=True)
        
        # Treeview for leaves
        tree_frame = ttk.Frame(leaves_frame)
        tree_frame.pack(fill="both", expand=True)
        
        columns = ("Doctor", "Date", "Session", "Reason")
        self.leave_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        
        self.leave_tree.heading("Doctor", text="Doctor")
        self.leave_tree.heading("Date", text="Date")
        self.leave_tree.heading("Session", text="Session")
        self.leave_tree.heading("Reason", text="Reason")
        
        self.leave_tree.column("Doctor", width=150)
        self.leave_tree.column("Date", width=100)
        self.leave_tree.column("Session", width=100)
        self.leave_tree.column("Reason", width=150)
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.leave_tree.yview)
        self.leave_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.leave_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        
        # Delete button
        delete_btn = ttk.Button(leaves_frame, text="Delete Selected", command=self.delete_leave)
        delete_btn.pack(pady=(10, 0))
        
        # Load leaves
        self.refresh_leaves()
    
    def add_leave(self):
        """Add a new leave record."""
        try:
            # Validate inputs
            staff_selection = self.leave_staff_var.get()
            if not staff_selection:
                messagebox.showerror("Error", "Please select a doctor")
                return
            
            # Extract short name from selection "Full Name (short)"
            short_name = staff_selection.split("(")[1].strip(")")
            
            date_str = self.leave_date_var.get().strip()
            # Validate date format and convert to YYYY-MM-DD
            try:
                date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                db_date = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Error", "Invalid date format. Use DD-MM-YYYY")
                return
            
            session = self.leave_session_var.get()
            reason = self.leave_reason_var.get().strip()
            
            # Add to database
            add_doctor_leave(short_name, db_date, session, reason)
            
            # Refresh list
            self.refresh_leaves()
            
            # Clear form
            self.leave_reason_var.set("")
            
            messagebox.showinfo("Success", "Leave added successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add leave:\n{str(e)}")
    
    def delete_leave(self):
        """Delete selected leave."""
        selection = self.leave_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a leave to delete")
            return
        
        item = selection[0]
        leave_id = self.leave_tree.item(item, "values")[4]  # Hidden column
        
        if messagebox.askyesno("Confirm", "Delete this leave record?"):
            delete_doctor_leave(int(leave_id))
            self.refresh_leaves()
            messagebox.showinfo("Success", "Leave deleted")
    
    def refresh_leaves(self):
        """Refresh the leave tree with current data."""
        # Clear existing
        for item in self.leave_tree.get_children():
            self.leave_tree.delete(item)
        
        # Load from database
        leaves = get_all_doctor_leaves()
        for leave in leaves:
            # Get full name from short name
            full_name = config.map_ys_bs.get(leave['staff_short_name'], leave['staff_short_name'])
            
            # Format date for display (YYYY-MM-DD -> DD-MM-YYYY)
            date_display = leave['leave_date']
            try:
                d = datetime.strptime(date_display, "%Y-%m-%d")
                date_display = d.strftime("%d-%m-%Y")
            except:
                pass # Already in DD-MM-YYYY or invalid
            
            # Format session
            session_map = {
                "morning": "Sáng",
                "afternoon": "Chiều",
                "full_day": "Cả ngày"
            }
            session_text = session_map.get(leave['session'], leave['session'])
            
            # Insert with ID as hidden value
            self.leave_tree.insert("", "end", values=(
                full_name,
                date_display,
                session_text,
                leave['reason'],
                leave['id']  # Hidden
            ))
    
    def save_staff_config(self):
        """Save the staff availability configuration."""
        # Get list of disabled staff
        disabled = [name for name, var in self.checkbox_vars.items() if not var.get()]
        
        # Save to database
        set_disabled_staff(disabled)
        
        messagebox.showinfo("Success", f"Configuration saved!\n{len(disabled)} staff member(s) disabled.")
    
    def show(self):
        """Show the dialog and wait for it to close."""
        self.dialog.wait_window()
