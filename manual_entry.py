"""
Manual Entry Dialog for the Clinic Auto-Fill application.
Provides a GUI for manually entering patient appointment data.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from tkcalendar import DateEntry
from config import thu_thuat_dur_mapper, map_ys_bs
from handle_data import create_data_from_manual_input
from database import save_manual_entry_to_db


class ManualEntryDialog:
    """Dialog for manual data entry with scrollable UI."""
    
    def __init__(self, parent, on_save_callback=None):
        """
        Initialize the manual entry dialog.
        
        Args:
            parent: Parent window
            on_save_callback: Callback function when data is saved
        """
        self.parent = parent
        self.on_save_callback = on_save_callback
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Manual Patient Data Entry")
        self.dialog.geometry("650x550")  # Smaller height for scrolling
        self.dialog.resizable(False, True)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.center_dialog()
        
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
        """Setup the scrollable user interface."""
        # Create canvas and scrollbar
        canvas = tk.Canvas(self.dialog)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas, padding="20")
        
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
        
        main_frame = scrollable_frame
        
        # Title
        title_label = ttk.Label(main_frame, text="Enter Patient Appointment Data", 
                               font=('Arial', 12, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        row = 1
        
        # Patient ID
        ttk.Label(main_frame, text="Patient ID:", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        self.patient_id_var = tk.StringVar()
        patient_id_entry = ttk.Entry(main_frame, textvariable=self.patient_id_var, width=40)
        patient_id_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Appointment Date
        ttk.Label(main_frame, text="Appointment Date:", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        
        date_input_frame = ttk.Frame(main_frame)
        date_input_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        
        try:
            self.date_entry = DateEntry(date_input_frame, width=20, background='darkblue',
                                       foreground='white', borderwidth=2, date_pattern='dd-mm-yyyy')
        except:
            self.date_entry = ttk.Entry(date_input_frame, width=23)
            self.date_entry.insert(0, datetime.now().strftime("%d-%m-%Y"))
        self.date_entry.grid(row=0, column=0, padx=(0, 10))
        
        # Quick date input (DDMMYY format)
        ttk.Label(date_input_frame, text="or Quick:").grid(row=0, column=1, padx=(0, 5))
        self.quick_date_var = tk.StringVar()
        self.quick_date_entry = ttk.Entry(date_input_frame, textvariable=self.quick_date_var, width=10)
        self.quick_date_entry.grid(row=0, column=2)
        
        # Quick date hint
        ttk.Label(date_input_frame, text="(e.g., 091225)", font=('Arial', 8), foreground="gray").grid(
            row=0, column=3, padx=(5, 0))
        
        # Bind quick date input
        self.quick_date_entry.bind('<KeyRelease>', self.on_quick_date_input)
        
        row += 1
        
        # Appointment Time
        ttk.Label(main_frame, text="Appointment Time:", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        time_frame = ttk.Frame(main_frame)
        time_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        
        self.hour_var = tk.StringVar(value="08")
        self.minute_var = tk.StringVar(value="00")
        
        hour_spinbox = ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var, 
                                  width=5, format="%02.0f")
        hour_spinbox.grid(row=0, column=0)
        ttk.Label(time_frame, text=":").grid(row=0, column=1, padx=5)
        minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, 
                                    width=5, format="%02.0f")
        minute_spinbox.grid(row=0, column=2)
        row += 1
        
        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=15)
        row += 1
        
        # Procedures Section - EXACTLY 4 dropdowns
        procedures_frame = ttk.LabelFrame(main_frame, text="Procedures (Chọn đúng 4 thủ thuật theo thứ tự)", 
                                         padding="10")
        procedures_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Get available procedures
        self.available_procedures = sorted(list(thu_thuat_dur_mapper.keys()))
        
        # Create 4 procedure dropdowns
        self.procedure_vars = []
        for i in range(4):
            ttk.Label(procedures_frame, text=f"Thủ thuật {i+1}:").grid(
                row=i, column=0, sticky=tk.W, pady=5, padx=(0, 10))
            var = tk.StringVar()
            dropdown = ttk.Combobox(procedures_frame, textvariable=var, 
                                   values=self.available_procedures, width=35, state='readonly')
            dropdown.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=5)
            self.procedure_vars.append(var)
        
        # Staff Section - Autocomplete comboboxes
        staff_frame = ttk.LabelFrame(main_frame, text="Staff Members (Người thực hiện)", 
                                    padding="10")
        staff_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(staff_frame, text="💡 Gõ tên để tìm nhanh, chọn 1-3 người theo thứ tự:").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Get available staff (capitalize for display)
        self.available_staff = sorted(list(map_ys_bs.keys()))
        self.staff_display = [s.title() for s in self.available_staff]
        
        # Create 3 staff comboboxes with autocomplete
        self.staff_vars = []
        for i in range(3):
            ttk.Label(staff_frame, text=f"Người {i+1}:").grid(row=i+1, column=0, sticky=tk.W, pady=5)
            var = tk.StringVar()
            
            # Create combobox that allows typing
            combo = ttk.Combobox(staff_frame, textvariable=var, 
                                values=self.staff_display, width=35)
            combo.grid(row=i+1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
            
            # Add autocomplete behavior
            def make_autocomplete(combo_widget, var_widget, values_list):
                def on_keyrelease(event):
                    value = var_widget.get()
                    if value == '':
                        combo_widget['values'] = values_list
                    else:
                        data = []
                        for item in values_list:
                            if value.lower() in item.lower():
                                data.append(item)
                        combo_widget['values'] = data
                return on_keyrelease
            
            combo.bind('<KeyRelease>', make_autocomplete(combo, var, self.staff_display))
            self.staff_vars.append(var)
        
        # Notes Section
        notes_frame = ttk.LabelFrame(main_frame, text="Notes (Optional)", padding="10")
        notes_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        self.notes_text = tk.Text(notes_frame, height=3, width=50)
        self.notes_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=20)
        
        save_btn = ttk.Button(button_frame, text="💾 Save & Add to Queue", 
                             command=self.save_entry, style="Accent.TButton")
        save_btn.grid(row=0, column=0, padx=5)
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_btn.grid(row=0, column=1, padx=5)
        
        # Info Label
        info_label = ttk.Label(main_frame, 
                              text="💡 Chọn đủ 4 thủ thuật và ít nhất 1 người thực hiện",
                              font=('Arial', 9), foreground="gray")
        info_label.grid(row=row+1, column=0, columnspan=2, pady=(0, 10))
    
    def on_quick_date_input(self, event):
        """Handle quick date input (DDMMYY format)."""
        quick_input = self.quick_date_var.get().strip()
        
        # Check if input is 6 digits
        if len(quick_input) == 6 and quick_input.isdigit():
            try:
                dd = quick_input[0:2]
                mm = quick_input[2:4]
                yy = quick_input[4:6]
                
                # Convert to full year (assume 20YY)
                yyyy = f"20{yy}"
                
                # Validate date
                date_str = f"{dd}-{mm}-{yyyy}"
                datetime.strptime(date_str, "%d-%m-%Y")  # Validate
                
                # Update the main date entry
                if hasattr(self.date_entry, 'set_date'):
                    date_obj = datetime.strptime(date_str, "%d-%m-%Y")
                    self.date_entry.set_date(date_obj)
                else:
                    self.date_entry.delete(0, tk.END)
                    self.date_entry.insert(0, date_str)
                
                # Visual feedback
                self.quick_date_entry.config(foreground='green')
            except ValueError:
                # Invalid date
                self.quick_date_entry.config(foreground='red')
        else:
            # Reset color if not 6 digits
            self.quick_date_entry.config(foreground='black')
        
    def validate_input(self):
        """Validate user input."""
        # Check patient ID
        if not self.patient_id_var.get().strip():
            messagebox.showerror("Validation Error", "Please enter a Patient ID.")
            return False
        
        # Check date
        try:
            if hasattr(self.date_entry, 'get_date'):
                date_str = self.date_entry.get_date().strftime("%d-%m-%Y")
            else:
                date_str = self.date_entry.get()
                datetime.strptime(date_str, "%d-%m-%Y")
        except ValueError:
            messagebox.showerror("Validation Error", "Invalid date format. Use DD-MM-YYYY.")
            return False
        
        # Check time
        try:
            hour = int(self.hour_var.get())
            minute = int(self.minute_var.get())
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError()
        except ValueError:
            messagebox.showerror("Validation Error", "Invalid time format.")
            return False
        
        # Check procedures - MUST BE EXACTLY 4
        selected_procedures = [var.get() for var in self.procedure_vars if var.get()]
        if len(selected_procedures) != 4:
            messagebox.showerror("Validation Error", 
                               f"Please select EXACTLY 4 procedures.\nCurrently selected: {len(selected_procedures)}")
            return False
        
        # Check staff
        selected_staff = [var.get().lower() for var in self.staff_vars if var.get()]
        if not selected_staff:
            messagebox.showerror("Validation Error", "Please select at least one staff member.")
            return False
        
        # Validate staff names exist in config
        for staff in selected_staff:
            if staff not in self.available_staff:
                messagebox.showerror("Validation Error", f"Unknown staff member: {staff}")
                return False
        
        return True
    
    def save_entry(self):
        """Save the entry and close dialog."""
        if not self.validate_input():
            return
        
        try:
            # Get date
            if hasattr(self.date_entry, 'get_date'):
                date_str = self.date_entry.get_date().strftime("%d-%m-%Y")
            else:
                date_str = self.date_entry.get()
            
            # Get time
            time_str = f"{self.hour_var.get()}:{self.minute_var.get()}"
            
            # Get selected procedures - EXACTLY 4
            procedures = [var.get() for var in self.procedure_vars]
            
            # Get selected staff (normalize to lowercase)
            staff = [var.get().lower() for var in self.staff_vars if var.get()]
            
            # Create automation data
            data = create_data_from_manual_input(
                patient_id=self.patient_id_var.get().strip(),
                procedures_list=procedures,
                staff_list=staff,
                appointment_date=date_str,
                appointment_time=time_str
            )
            
            # Save to database
            notes = self.notes_text.get("1.0", tk.END).strip()
            save_manual_entry_to_db(
                patient_id=self.patient_id_var.get().strip(),
                procedures="-".join(procedures),
                staff="-".join(staff),
                appointment_date=date_str,
                appointment_time=time_str,
                notes=notes
            )
            
            self.result = data
            
            # Call callback if provided
            if self.on_save_callback:
                self.on_save_callback(data)
            
            messagebox.showinfo("Success", f"✓ Added patient {self.patient_id_var.get()} with 4 procedures!")
            self.dialog.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save entry:\n{str(e)}")
    
    def cancel(self):
        """Cancel and close dialog."""
        self.result = None
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and wait for it to close."""
        self.dialog.wait_window()
        return self.result
