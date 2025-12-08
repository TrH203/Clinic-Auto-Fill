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
    """Dialog for manual data entry."""
    
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
        self.dialog.geometry("600x700")
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.center_dialog()
        
        self.procedure_entries = []
        self.staff_entries = []
        
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
        """Setup the user interface."""
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
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
        try:
            self.date_entry = DateEntry(main_frame, width=37, background='darkblue',
                                       foreground='white', borderwidth=2, date_pattern='dd-mm-yyyy')
        except:
            # Fallback if tkcalendar not available
            self.date_entry = ttk.Entry(main_frame, width=40)
            self.date_entry.insert(0, datetime.now().strftime("%d-%m-%Y"))
        self.date_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
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
        
        # Procedures Section
        procedures_frame = ttk.LabelFrame(main_frame, text="Procedures (Thủ thuật)", 
                                         padding="10")
        procedures_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Get available procedures
        self.available_procedures = sorted(list(thu_thuat_dur_mapper.keys()))
        
        # Create checkboxes for procedures
        self.procedure_vars = {}
        proc_row = 0
        proc_col = 0
        for proc in self.available_procedures:
            var = tk.BooleanVar()
            self.procedure_vars[proc] = var
            cb = ttk.Checkbutton(procedures_frame, text=f"{proc} ({thu_thuat_dur_mapper[proc]} min)", 
                               variable=var)
            cb.grid(row=proc_row, column=proc_col, sticky=tk.W, padx=10, pady=2)
            proc_col += 1
            if proc_col > 1:
                proc_col = 0
                proc_row += 1
        
        # Staff Section
        staff_frame = ttk.LabelFrame(main_frame, text="Staff Members (Người thực hiện)", 
                                    padding="10")
        staff_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(staff_frame, text="Select up to 3 staff members in order:").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Get available staff
        self.available_staff = sorted(list(map_ys_bs.keys()))
        
        # Create 3 staff dropdowns
        self.staff_vars = []
        for i in range(3):
            ttk.Label(staff_frame, text=f"Staff {i+1}:").grid(row=i+1, column=0, sticky=tk.W, pady=5)
            var = tk.StringVar()
            dropdown = ttk.Combobox(staff_frame, textvariable=var, 
                                   values=[""] + self.available_staff, width=35, state='readonly')
            dropdown.grid(row=i+1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
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
        
        save_btn = ttk.Button(button_frame, text="Save & Add to Queue", command=self.save_entry)
        save_btn.grid(row=0, column=0, padx=5)
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_btn.grid(row=0, column=1, padx=5)
        
        # Info Label
        info_label = ttk.Label(main_frame, 
                              text="💡 Tip: Select procedures and staff members, then click Save to add to automation queue.",
                              font=('Arial', 9), foreground="gray")
        info_label.grid(row=row+1, column=0, columnspan=2, pady=(0, 10))
        
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
        
        # Check procedures
        selected_procedures = [proc for proc, var in self.procedure_vars.items() if var.get()]
        if not selected_procedures:
            messagebox.showerror("Validation Error", "Please select at least one procedure.")
            return False
        
        # Check staff
        selected_staff = [var.get() for var in self.staff_vars if var.get()]
        if not selected_staff:
            messagebox.showerror("Validation Error", "Please select at least one staff member.")
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
            
            # Get selected procedures
            procedures = [proc for proc, var in self.procedure_vars.items() if var.get()]
            
            # Get selected staff
            staff = [var.get() for var in self.staff_vars if var.get()]
            
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
            
            messagebox.showinfo("Success", "Patient data added successfully!")
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


if __name__ == "__main__":
    # Test the dialog
    root = tk.Tk()
    root.withdraw()
    
    def test_callback(data):
        print("Data saved:", data)
    
    dialog = ManualEntryDialog(root, on_save_callback=test_callback)
    result = dialog.show()
    
    if result:
        print("Result:", result)
    else:
        print("Cancelled")
    
    root.destroy()
