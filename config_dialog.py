import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import config
from database import (get_disabled_staff, set_disabled_staff, add_doctor_leave, 
                      get_all_doctor_leaves, delete_doctor_leave, get_all_staff,
                      add_staff, delete_staff, add_weekly_leave, 
                      get_all_weekly_leaves, delete_weekly_leave)

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
        title_label = ttk.Label(main_frame, text="Cấu Hình", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Create notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill="both", expand=True)
        
        # Tab 1: Staff Availability
        self.setup_staff_tab(notebook)
        
        # Tab 2: Leave Schedule
        self.setup_leave_tab(notebook)
        
        # Tab 3: Staff Management
        self.setup_staff_management_tab(notebook)
        
        # Tab 4: Coordinates
        self.setup_coordinates_tab(notebook)
        
        # Buttons at bottom
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(15, 0))
        
        close_btn = ttk.Button(button_frame, text="Đóng", command=self.dialog.destroy)
        close_btn.pack()
    
    def setup_staff_tab(self, notebook):
        """Setup the staff availability tab."""
        staff_frame = ttk.Frame(notebook, padding="15")
        notebook.add(staff_frame, text="Trạng Thái Nhân Viên")
        
        # Info label
        info_label = ttk.Label(staff_frame, 
                              text="Bỏ chọn nhân viên để vô hiệu hóa họ khỏi nhập liệu thủ công và tự động",
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
        f1 = create_staff_list(lists_container, "Nhóm 1 (Nhân Viên 1 & 3)", config.staff_p1_p3)
        f1.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Group 2 List
        f2 = create_staff_list(lists_container, "Nhóm 2 (Nhân Viên 2)", config.staff_p2)
        f2.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Save button for this tab
        save_btn = ttk.Button(staff_frame, text="💾 Lưu", command=self.save_staff_config, 
                             style="Accent.TButton")
        save_btn.pack(pady=(15, 0))
    
    def setup_leave_tab(self, notebook):
        """Setup the leave schedule tab with sub-notebook for date and weekly leaves."""
        leave_frame = ttk.Frame(notebook, padding="10")
        notebook.add(leave_frame, text="Lịch Nghỉ")
        
        # Create sub-notebook for different leave types
        leave_notebook = ttk.Notebook(leave_frame)
        leave_notebook.pack(fill="both", expand=True)
        
        # Tab 1: Date-specific leaves
        self.setup_date_leave_section(leave_notebook)
        
        # Tab 2: Weekly recurring leaves
        self.setup_weekly_leave_section(leave_notebook)
    
    def setup_date_leave_section(self, notebook):
        """Setup section for date-specific leaves."""
        date_frame = ttk.Frame(notebook, padding="10")
        notebook.add(date_frame, text="Nghỉ Theo Ngày")
        
        # Add leave section
        add_frame = ttk.LabelFrame(date_frame, text="Thêm Lịch Nghỉ", padding="10")
        add_frame.pack(fill="x", pady=(0, 10))
        
        # Doctor selection
        ttk.Label(add_frame, text="Nhân viên:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.leave_staff_var = tk.StringVar()
        staff_combo = ttk.Combobox(add_frame, textvariable=self.leave_staff_var, 
                                   values=sorted([f"{v} ({k})" for k, v in config.map_ys_bs.items()]),
                                   width=30)
        staff_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Date
        ttk.Label(add_frame, text="Ngày:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.leave_date_var = tk.StringVar(value=datetime.now().strftime("%d-%m-%Y"))
        date_entry = ttk.Entry(add_frame, textvariable=self.leave_date_var, width=32)
        date_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        ttk.Label(add_frame, text="(DD-MM-YYYY)", font=('Arial', 8), foreground="gray").grid(
            row=1, column=2, padx=(5, 0))
        
        # Session
        ttk.Label(add_frame, text="Buổi:").grid(row=2, column=0, sticky=tk.W, pady=5)
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
        ttk.Label(add_frame, text="Lý Do:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.leave_reason_var = tk.StringVar()
        reason_entry = ttk.Entry(add_frame, textvariable=self.leave_reason_var, width=32)
        reason_entry.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Add button
        add_btn = ttk.Button(add_frame, text="➕ Thêm Lịch Nghỉ", command=self.add_leave)
        add_btn.grid(row=4, column=1, pady=(10, 0))
        
        add_frame.columnconfigure(1, weight=1)
        
        # Current leaves section
        leaves_frame = ttk.LabelFrame(date_frame, text="Danh Sách Lịch Nghỉ Theo Ngày", padding="10")
        leaves_frame.pack(fill="both", expand=True)
        
        # Treeview for leaves
        tree_frame = ttk.Frame(leaves_frame)
        tree_frame.pack(fill="both", expand=True)
        
        columns = ("Doctor", "Date", "Session", "Reason")
        self.leave_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        
        self.leave_tree.heading("Doctor", text="Nhân viên")
        self.leave_tree.heading("Date", text="Ngày")
        self.leave_tree.heading("Session", text="Buổi")
        self.leave_tree.heading("Reason", text="Lý do")
        
        self.leave_tree.column("Doctor", width=150)
        self.leave_tree.column("Date", width=100)
        self.leave_tree.column("Session", width=80)
        self.leave_tree.column("Reason", width=150)
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.leave_tree.yview)
        self.leave_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.leave_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        
        # Delete button
        delete_btn = ttk.Button(leaves_frame, text="🗑️ Xóa Đã Chọn", command=self.delete_leave)
        delete_btn.pack(pady=(10, 0))
        
        # Load leaves
        self.refresh_leaves()
    
    def setup_weekly_leave_section(self, notebook):
        """Setup section for weekly recurring leaves."""
        weekly_frame = ttk.Frame(notebook, padding="10")
        notebook.add(weekly_frame, text="Nghỉ Hằng Tuần")
        
        # Add weekly leave section
        add_frame = ttk.LabelFrame(weekly_frame, text="Thêm Lịch Nghỉ Hằng Tuần", padding="10")
        add_frame.pack(fill="x", pady=(0, 10))
        
        # Staff selection
        ttk.Label(add_frame, text="Nhân viên:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.weekly_staff_var = tk.StringVar()
        staff_combo = ttk.Combobox(add_frame, textvariable=self.weekly_staff_var, 
                                   values=sorted([f"{v} ({k})" for k, v in config.map_ys_bs.items()]),
                                   width=30)
        staff_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Day of week selection
        ttk.Label(add_frame, text="Thứ:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.weekly_day_var = tk.StringVar()
        day_values = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
        day_combo = ttk.Combobox(add_frame, textvariable=self.weekly_day_var, 
                                 values=day_values, width=30, state="readonly")
        day_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        day_combo.current(0)
        
        # Session
        ttk.Label(add_frame, text="Buổi:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.weekly_session_var = tk.StringVar(value="morning")
        session_frame = ttk.Frame(add_frame)
        session_frame.grid(row=2, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        ttk.Radiobutton(session_frame, text="Sáng (7h-12h)", variable=self.weekly_session_var, 
                       value="morning").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(session_frame, text="Chiều (13h-17h)", variable=self.weekly_session_var, 
                       value="afternoon").pack(side="left", padx=(0, 10))
        ttk.Radiobutton(session_frame, text="Cả ngày", variable=self.weekly_session_var, 
                       value="full_day").pack(side="left")
        
        # Reason
        ttk.Label(add_frame, text="Lý Do:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.weekly_reason_var = tk.StringVar()
        reason_entry = ttk.Entry(add_frame, textvariable=self.weekly_reason_var, width=32)
        reason_entry.grid(row=3, column=1, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # Add button
        add_btn = ttk.Button(add_frame, text="➕ Thêm Lịch Nghỉ Hằng Tuần", command=self.add_weekly_leave)
        add_btn.grid(row=4, column=1, pady=(10, 0))
        
        add_frame.columnconfigure(1, weight=1)
        
        # Current weekly leaves section
        leaves_frame = ttk.LabelFrame(weekly_frame, text="Danh Sách Lịch Nghỉ Hằng Tuần", padding="10")
        leaves_frame.pack(fill="both", expand=True)
        
        # Treeview for weekly leaves
        tree_frame = ttk.Frame(leaves_frame)
        tree_frame.pack(fill="both", expand=True)
        
        columns = ("Doctor", "Day", "Session", "Reason")
        self.weekly_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=8)
        
        self.weekly_tree.heading("Doctor", text="Nhân viên")
        self.weekly_tree.heading("Day", text="Thứ")
        self.weekly_tree.heading("Session", text="Buổi")
        self.weekly_tree.heading("Reason", text="Lý do")
        
        self.weekly_tree.column("Doctor", width=150)
        self.weekly_tree.column("Day", width=100)
        self.weekly_tree.column("Session", width=80)
        self.weekly_tree.column("Reason", width=150)
        
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.weekly_tree.yview)
        self.weekly_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.weekly_tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        
        # Delete button
        delete_btn = ttk.Button(leaves_frame, text="🗑️ Xóa Đã Chọn", command=self.delete_weekly_leave_ui)
        delete_btn.pack(pady=(10, 0))
        
        # Load weekly leaves
        self.refresh_weekly_leaves()
    
    def add_leave(self):
        """Add a new leave record."""
        try:
            # Validate inputs
            staff_selection = self.leave_staff_var.get()
            if not staff_selection:
                messagebox.showerror("Lỗi", "Vui lòng chọn bác sĩ")
                return
            
            # Extract short name from selection "Full Name (short)"
            short_name = staff_selection.split("(")[1].strip(")")
            
            date_str = self.leave_date_var.get().strip()
            # Validate date format and convert to YYYY-MM-DD
            try:
                date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                db_date = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Lỗi", "Định dạng ngày không hợp lệ. Sử dụng DD-MM-YYYY")
                return
            
            session = self.leave_session_var.get()
            reason = self.leave_reason_var.get().strip()
            
            # Add to database
            add_doctor_leave(short_name, db_date, session, reason)
            
            # Refresh list
            self.refresh_leaves()
            
            # Clear form
            self.leave_reason_var.set("")
            
            messagebox.showinfo("Thành Công", "Thêm lịch nghỉ thành công")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm lịch nghỉ:\n{str(e)}")
    
    def delete_leave(self):
        """Delete selected leave."""
        selection = self.leave_tree.selection()
        if not selection:
            messagebox.showwarning("Cảnh Báo", "Vui lòng chọn lịch nghỉ để xóa")
            return
        
        item = selection[0]
        leave_id = self.leave_tree.item(item, "values")[4]  # Hidden column
        
        if messagebox.askyesno("Xác Nhận", "Xóa bản ghi lịch nghỉ này?"):
            delete_doctor_leave(int(leave_id))
            self.refresh_leaves()
            messagebox.showinfo("Thành Công", "Lịch nghỉ đã xóa")
    
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
    
    def add_weekly_leave(self):
        """Add a new weekly recurring leave record."""
        try:
            # Validate inputs
            staff_selection = self.weekly_staff_var.get()
            if not staff_selection:
                messagebox.showerror("Lỗi", "Vui lòng chọn nhân viên")
                return
            
            # Extract short name from selection "Full Name (short)"
            short_name = staff_selection.split("(")[1].strip(")")
            
            # Get day of week (0=Monday, ..., 6=Sunday)
            day_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
            day_str = self.weekly_day_var.get()
            if day_str not in day_names:
                messagebox.showerror("Lỗi", "Vui lòng chọn thứ")
                return
            day_of_week = day_names.index(day_str)
            
            session = self.weekly_session_var.get()
            reason = self.weekly_reason_var.get().strip()
            
            # Add to database
            add_weekly_leave(short_name, day_of_week, session, reason)
            
            # Refresh list
            self.refresh_weekly_leaves()
            
            # Clear form
            self.weekly_reason_var.set("")
            
            messagebox.showinfo("Thành Công", f"Thêm lịch nghỉ hằng tuần: {day_str}")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm lịch nghỉ hằng tuần:\n{str(e)}")
    
    def delete_weekly_leave_ui(self):
        """Delete selected weekly leave."""
        selection = self.weekly_tree.selection()
        if not selection:
            messagebox.showwarning("Cảnh Báo", "Vui lòng chọn lịch nghỉ để xóa")
            return
        
        item = selection[0]
        leave_id = self.weekly_tree.item(item, "values")[4]  # Hidden column
        
        if messagebox.askyesno("Xác Nhận", "Xóa bản ghi lịch nghỉ hằng tuần này?"):
            delete_weekly_leave(int(leave_id))
            self.refresh_weekly_leaves()
            messagebox.showinfo("Thành Công", "Đã xóa lịch nghỉ hằng tuần")
    
    def refresh_weekly_leaves(self):
        """Refresh the weekly leave tree with current data."""
        # Clear existing
        for item in self.weekly_tree.get_children():
            self.weekly_tree.delete(item)
        
        # Load from database
        leaves = get_all_weekly_leaves()
        
        day_names = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "CN"]
        session_map = {
            "morning": "Sáng",
            "afternoon": "Chiều",
            "full_day": "Cả ngày"
        }
        
        for leave in leaves:
            # Get full name from short name
            full_name = config.map_ys_bs.get(leave['staff_short_name'], leave['staff_short_name'])
            
            # Format day of week
            day_text = day_names[leave['day_of_week']] if leave['day_of_week'] < len(day_names) else str(leave['day_of_week'])
            
            # Format session
            session_text = session_map.get(leave['session'], leave['session'])
            
            # Insert with ID as hidden value
            self.weekly_tree.insert("", "end", values=(
                full_name,
                day_text,
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
        
        messagebox.showinfo("Thành Công", f"Cấu hình đã lưu!\n{len(disabled)} nhân viên đã vô hiệu hóa.")
    
    def setup_staff_management_tab(self, notebook):
        """Setup the staff management tab."""
        staff_mgmt_frame = ttk.Frame(notebook, padding="15")
        notebook.add(staff_mgmt_frame, text="Quản Lý Nhân Viên")
        
        # Info label
        info_label = ttk.Label(staff_mgmt_frame,
                              text="Thêm hoặc xóa nhân viên từ danh sách. Nhân viên đã xóa sẽ không xuất hiện trong việc nhập liệu.",
                              font=('Arial', 9), foreground="gray", wraplength=700)
        info_label.pack(pady=(0, 15))
        
        # Two columns for Group 1 and Group 2
        columns_frame = ttk.Frame(staff_mgmt_frame)
        columns_frame.pack(fill="both", expand=True)
        
        # ===== Group 1 Column =====
        group1_frame = ttk.LabelFrame(columns_frame, text="Nhóm 1 (Y tá/KTV - Vị trí 1 & 3)", padding="10")
        group1_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Add form for Group 1
        add1_frame = ttk.Frame(group1_frame)
        add1_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(add1_frame, text="Tên ngắn:", font=('Arial', 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.g1_short_var = tk.StringVar()
        ttk.Entry(add1_frame, textvariable=self.g1_short_var, width=15).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(add1_frame, text="Tên đầy đủ:", font=('Arial', 9)).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.g1_full_var = tk.StringVar()
        ttk.Entry(add1_frame, textvariable=self.g1_full_var, width=25).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Button(add1_frame, text="➕ Thêm", command=lambda: self.add_staff_member(1)).grid(row=2, column=1, pady=5)
        add1_frame.columnconfigure(1, weight=1)
        
        # List for Group 1
        ttk.Separator(group1_frame, orient='horizontal').pack(fill='x', pady=5)
        ttk.Label(group1_frame, text="Danh sách hiện tại:", font=('Arial', 9, 'bold')).pack(anchor="w", pady=(5, 2))
        
        list1_frame = ttk.Frame(group1_frame)
        list1_frame.pack(fill="both", expand=True)
        
        self.g1_tree = ttk.Treeview(list1_frame, columns=("Short", "Full"), show="headings", height=10)
        self.g1_tree.heading("Short", text="Tên ngắn")
        self.g1_tree.heading("Full", text="Tên đầy đủ")
        self.g1_tree.column("Short", width=80)
        self.g1_tree.column("Full", width=150)
        
        g1_scroll = ttk.Scrollbar(list1_frame, orient="vertical", command=self.g1_tree.yview)
        self.g1_tree.configure(yscrollcommand=g1_scroll.set)
        
        self.g1_tree.pack(side="left", fill="both", expand=True)
        g1_scroll.pack(side="right", fill="y")
        
        ttk.Button(group1_frame, text="🗑️ Xóa đã chọn", command=lambda: self.delete_staff_member(1)).pack(pady=(10, 0))
        
        # ===== Group 2 Column =====
        group2_frame = ttk.LabelFrame(columns_frame, text="Nhóm 2 (Bác sĩ - Vị trí 2)", padding="10")
        group2_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Add form for Group 2
        add2_frame = ttk.Frame(group2_frame)
        add2_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(add2_frame, text="Tên ngắn:", font=('Arial', 9)).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.g2_short_var = tk.StringVar()
        ttk.Entry(add2_frame, textvariable=self.g2_short_var, width=15).grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Label(add2_frame, text="Tên đầy đủ:", font=('Arial', 9)).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.g2_full_var = tk.StringVar()
        ttk.Entry(add2_frame, textvariable=self.g2_full_var, width=25).grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
        
        ttk.Button(add2_frame, text="➕ Thêm", command=lambda: self.add_staff_member(2)).grid(row=2, column=1, pady=5)
        add2_frame.columnconfigure(1, weight=1)
        
        # List for Group 2
        ttk.Separator(group2_frame, orient='horizontal').pack(fill='x', pady=5)
        ttk.Label(group2_frame, text="Danh sách hiện tại:", font=('Arial', 9, 'bold')).pack(anchor="w", pady=(5, 2))
        
        list2_frame = ttk.Frame(group2_frame)
        list2_frame.pack(fill="both", expand=True)
        
        self.g2_tree = ttk.Treeview(list2_frame, columns=("Short", "Full"), show="headings", height=10)
        self.g2_tree.heading("Short", text="Tên ngắn")
        self.g2_tree.heading("Full", text="Tên đầy đủ")
        self.g2_tree.column("Short", width=80)
        self.g2_tree.column("Full", width=150)
        
        g2_scroll = ttk.Scrollbar(list2_frame, orient="vertical", command=self.g2_tree.yview)
        self.g2_tree.configure(yscrollcommand=g2_scroll.set)
        
        self.g2_tree.pack(side="left", fill="both", expand=True)
        g2_scroll.pack(side="right", fill="y")
        
        ttk.Button(group2_frame, text="🗑️ Xóa đã chọn", command=lambda: self.delete_staff_member(2)).pack(pady=(10, 0))
        
        # Load initial data
        self.refresh_staff_lists()
    
    def refresh_staff_lists(self):
        """Refresh both staff lists from database."""
        # Clear existing
        for item in self.g1_tree.get_children():
            self.g1_tree.delete(item)
        for item in self.g2_tree.get_children():
            self.g2_tree.delete(item)
        
        # Load from database
        all_staff = get_all_staff()
        
        for staff in all_staff:
            if staff['group_id'] == 1:
                self.g1_tree.insert("", "end", values=(staff['short_name'], staff['full_name']))
            elif staff['group_id'] == 2:
                self.g2_tree.insert("", "end", values=(staff['short_name'], staff['full_name']))
    
    def add_staff_member(self, group_id):
        """Add a new staff member to the specified group."""
        try:
            if group_id == 1:
                short_name = self.g1_short_var.get().strip()
                full_name = self.g1_full_var.get().strip()
            else:
                short_name = self.g2_short_var.get().strip()
                full_name = self.g2_full_var.get().strip()
            
            if not short_name or not full_name:
                messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ tên ngắn và tên đầy đủ")
                return
            
            # Add to database
            add_staff(short_name, full_name, group_id)
            
            # Reload config
            config.reload_staff()
            
            # Refresh list
            self.refresh_staff_lists()
            
            # Clear form
            if group_id == 1:
                self.g1_short_var.set("")
                self.g1_full_var.set("")
            else:
                self.g2_short_var.set("")
                self.g2_full_var.set("")
            
            messagebox.showinfo("Thành Công", f"Đã thêm {full_name} ({short_name}) vào Nhóm {group_id}")
            
        except ValueError as e:
            messagebox.showerror("Lỗi", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm nhân viên:\n{str(e)}")
    
    def delete_staff_member(self, group_id):
        """Delete selected staff member from the specified group."""
        tree = self.g1_tree if group_id == 1 else self.g2_tree
        selection = tree.selection()
        
        if not selection:
            messagebox.showwarning("Cảnh Báo", "Vui lòng chọn nhân viên để xóa")
            return
        
        item = selection[0]
        values = tree.item(item, "values")
        short_name = values[0]
        full_name = values[1]
        
        if messagebox.askyesno("Xác Nhận", 
                               f"Xóa nhân viên {full_name} ({short_name})?\n\n"
                               "Lưu ý: Nhân viên này sẽ không còn xuất hiện trong danh sách nhập liệu."):
            try:
                # Delete from database
                delete_staff(short_name)
                
                # Reload config
                config.reload_staff()
                
                # Refresh list
                self.refresh_staff_lists()
                
                messagebox.showinfo("Thành Công", f"Đã xóa {full_name}")
                
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa nhân viên:\n{str(e)}")
    
    def setup_coordinates_tab(self, notebook):
        """Setup the coordinates configuration tab."""
        import pyautogui
        from database import get_all_coordinates, save_all_coordinates, restore_default_coordinates
        
        coords_frame = ttk.Frame(notebook, padding="15")
        notebook.add(coords_frame, text="Tọa Độ")
        
        # Info label
        info_label = ttk.Label(coords_frame,
                              text="Cấu hình tọa độ các phần tử trên UI. Nhấn 'Bắt Tọa Độ' để xem vị trí con trỏ.",
                              font=('Arial', 9), foreground="gray", wraplength=700)
        info_label.pack(pady=(0, 10))
        
        # Create scrollable frame for coordinates
        canvas_container = ttk.Frame(coords_frame)
        canvas_container.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(canvas_container)
        scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Load coordinates
        coords = get_all_coordinates()
        sorted_coords = sorted(coords.items())
        
        # Store entry widgets
        self.coord_entry_widgets = {}
        
        # Header
        header_frame = ttk.Frame(scrollable_frame)
        header_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        ttk.Label(header_frame, text="Tên", font=('Arial', 9, 'bold'), width=22).grid(row=0, column=0, padx=5)
        ttk.Label(header_frame, text="X", font=('Arial', 9, 'bold'), width=8).grid(row=0, column=1, padx=5)
        ttk.Label(header_frame, text="Y", font=('Arial', 9, 'bold'), width=8).grid(row=0, column=2, padx=5)
        ttk.Label(header_frame, text="Mô Tả", font=('Arial', 9, 'bold'), width=28).grid(row=0, column=3, padx=5)
        ttk.Label(header_frame, text="", width=12).grid(row=0, column=4)
        
        # Separator
        ttk.Separator(scrollable_frame, orient='horizontal').pack(fill='x', padx=5, pady=(0, 5))
        
        # Create rows for each coordinate
        for name, (x, y, description) in sorted_coords:
            row_frame = ttk.Frame(scrollable_frame)
            row_frame.pack(fill="x", padx=5, pady=2)
            
            # Name label
            ttk.Label(row_frame, text=name, width=22).grid(row=0, column=0, padx=5, sticky="w")
            
            # X coordinate
            x_var = tk.IntVar(value=x)
            x_entry = ttk.Entry(row_frame, textvariable=x_var, width=8)
            x_entry.grid(row=0, column=1, padx=5)
            
            # Y coordinate
            y_var = tk.IntVar(value=y)
            y_entry = ttk.Entry(row_frame, textvariable=y_var, width=8)
            y_entry.grid(row=0, column=2, padx=5)
            
            # Description
            ttk.Label(row_frame, text=description[:35], width=28).grid(row=0, column=3, padx=5, sticky="w")
            
            # Capture button
            def make_capture_callback(coord_name, xv, yv):
                return lambda: self.show_position_tracker(coord_name, xv, yv)
            
            capture_btn = ttk.Button(row_frame, text="🎯 Bắt Tọa Độ",
                                   command=make_capture_callback(name, x_var, y_var))
            capture_btn.grid(row=0, column=4, padx=5)
            
            # Store references
            self.coord_entry_widgets[name] = {
                'x_var': x_var,
                'y_var': y_var,
                'description': description
            }
        
        # Buttons frame
        buttons_frame = ttk.Frame(coords_frame)
        buttons_frame.pack(fill="x", pady=(10, 0))
        
        save_coords_btn = ttk.Button(buttons_frame, text="💾 Lưu Tọa Độ",
                                     command=self.save_coordinates)
        save_coords_btn.pack(side="left", padx=(0, 5))
        
        restore_btn = ttk.Button(buttons_frame, text="🔄 Khôi Phục Mặc Định",
                                command=self.restore_default_coords)
        restore_btn.pack(side="left")
    
    def show_position_tracker(self, coord_name, x_var, y_var):
        """Show cursor position tracker window."""
        import pyautogui
        
        pos_window = tk.Toplevel(self.dialog)
        pos_window.title(f"Vị Trí Con Trỏ - {coord_name}")
        pos_window.attributes('-topmost', True)
        pos_window.geometry("400x250")
        
        # Center on screen
        screen_width = pos_window.winfo_screenwidth()
        screen_height = pos_window.winfo_screenheight()
        x = (screen_width - 400) // 2
        y = (screen_height - 250) // 2
        pos_window.geometry(f"400x250+{x}+{y}")
        
        frame = ttk.Frame(pos_window, padding="20")
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text=f"Hiển Thị Vị Trí: {coord_name}",
                 font=('Arial', 12, 'bold')).pack(pady=(0, 15))
        
        pos_label = ttk.Label(frame, text="X: 0, Y: 0",
                             font=('Arial', 16, 'bold'), foreground='blue')
        pos_label.pack(pady=20)
        
        ttk.Label(frame,
                 text="Di chuyển chuột đến vị trí mong muốn\nSau đó nhập thủ công giá trị X, Y vào ô bên trái\n\nNhấn ESC hoặc Đóng để thoát",
                 font=('Arial', 9), justify="center").pack(pady=10)
        
        def update_position():
            if pos_window.winfo_exists():
                try:
                    pos = pyautogui.position()
                    pos_label.config(text=f"X: {pos.x}, Y: {pos.y}")
                    pos_window.after(50, update_position)
                except:
                    pass
        
        update_position()
        
        close_btn = ttk.Button(frame, text="Đóng (ESC)",
                              command=pos_window.destroy)
        close_btn.pack(pady=10)
        
        pos_window.bind('<Escape>', lambda e: pos_window.destroy())
        pos_window.focus_set()
    
    def save_coordinates(self):
        """Save all coordinates to database."""
        try:
            from database import save_all_coordinates
            import config
            
            coords_to_save = {}
            for name, widgets in self.coord_entry_widgets.items():
                x = widgets['x_var'].get()
                y = widgets['y_var'].get()
                description = widgets['description']
                coords_to_save[name] = (x, y, description)
            
            save_all_coordinates(coords_to_save)
            config.reload_coordinates()
            
            messagebox.showinfo("Thành Công",
                              f"Đã lưu {len(coords_to_save)} tọa độ vào database.",
                              parent=self.dialog)
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu tọa độ:\n{str(e)}",
                               parent=self.dialog)
    
    def restore_default_coords(self):
        """Restore coordinates to defaults."""
        if messagebox.askyesno("Xác Nhận",
                              "Bạn có chắc muốn khôi phục tất cả tọa độ về giá trị mặc định?",
                              parent=self.dialog):
            try:
                from database import restore_default_coordinates
                import config
                
                restore_default_coordinates()
                config.reload_coordinates()
                
                messagebox.showinfo("Thành Công",
                                  "Đã khôi phục tất cả tọa độ về giá trị mặc định.\nVui lòng đóng và mở lại dialog để xem thay đổi.",
                                  parent=self.dialog)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể khôi phục tọa độ:\n{str(e)}",
                                   parent=self.dialog)
    
    def show(self):
        """Show the dialog and wait for it to close."""
        self.dialog.wait_window()
