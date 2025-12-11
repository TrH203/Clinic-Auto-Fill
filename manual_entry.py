"""
Manual Entry Dialog for the Clinic Auto-Fill application.
Provides a GUI for manually entering patient appointment data.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

from config import thu_thuat_dur_mapper, map_ys_bs
import config
from handle_data import create_data_from_manual_input
from database import save_manual_entry_to_db
import unicodedata

def remove_accents(input_str):
    """Remove accents from string for searching."""
    if not input_str:
        return ""
    s1 = unicodedata.normalize('NFD', input_str)
    s2 = ''.join(c for c in s1 if unicodedata.category(c) != 'Mn')
    return s2.lower()


class ManualEntryDialog:
    """Dialog for manual data entry with scrollable UI."""
    
    # Class variable to remember last used date across instances
    last_used_date = None
    
    def __init__(self, parent, on_save_callback=None, initial_data=None, on_delete_callback=None):
        """
        Initialize the manual entry dialog.
        
        Args:
            parent: Parent window
            on_save_callback: Callback function when data is saved
            initial_data: Optional dict with existing data for editing
            on_delete_callback: Optional callback function when entry is deleted
        """
        self.parent = parent
        self.on_save_callback = on_save_callback
        self.on_delete_callback = on_delete_callback
        self.initial_data = initial_data
        self.result = None
        
        # Create dialog window
        self.dialog = tk.Toplevel(parent)
        title = "Edit Patient Data" if initial_data else "Manual Patient Data Entry"
        self.dialog.title(title)
        self.dialog.geometry("620x680")  # Larger to fit all content without scrolling
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog on parent
        self.center_dialog()
        
        # Proper callback for cleanup
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Track all comboboxes for focus management
        self.all_comboboxes = []
        
        # Bind Escape to clear focus globally
        self.dialog.bind('<Escape>', self.clear_focus)
        
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
        # Main frame with compact padding
        main_frame = ttk.Frame(self.dialog, padding="15")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Enter Patient Appointment Data", 
                               font=('Arial', 12, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        row = 1
        
        # Patient ID
        ttk.Label(main_frame, text="Patient ID:", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        self.patient_id_var = tk.StringVar()
        self.patient_id_entry = ttk.Entry(main_frame, textvariable=self.patient_id_var, width=40)
        self.patient_id_entry.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Appointment Date
        ttk.Label(main_frame, text="Appointment Date:", font=('Arial', 10, 'bold')).grid(
            row=row, column=0, sticky=tk.W, pady=5)
        
        date_input_frame = ttk.Frame(main_frame)
        date_input_frame.grid(row=row, column=1, sticky=(tk.W, tk.E), pady=5)
        
        self.date_entry = ttk.Entry(date_input_frame, width=20)
        self.date_entry.grid(row=0, column=0, padx=(0, 10))
        
        # Set initial date: use last used date or today
        if ManualEntryDialog.last_used_date:
            initial_date = ManualEntryDialog.last_used_date
        else:
            initial_date = datetime.now().strftime("%d-%m-%Y")
        self.date_entry.insert(0, initial_date)
        
        # Bind key release for smart date formatting
        self.date_entry.bind('<KeyRelease>', self.on_date_key_release)
        # Bind click to select all
        self.date_entry.bind('<Button-1>', lambda e: self.date_entry.select_range(0, tk.END))
        self.date_entry.bind('<FocusIn>', lambda e: self.date_entry.select_range(0, tk.END))
        # Bind arrow keys for date navigation
        self.date_entry.bind('<Up>', self.increment_date)
        self.date_entry.bind('<Down>', self.decrement_date)
        
        ttk.Label(date_input_frame, text="(DD-MM-YYYY)", font=('Arial', 8), foreground="gray").grid(
            row=0, column=1, padx=(5, 0))
        
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
        # Select all on click/focus
        hour_spinbox.bind('<Button-1>', lambda e: hour_spinbox.select_range(0, tk.END))
        hour_spinbox.bind('<FocusIn>', lambda e: hour_spinbox.select_range(0, tk.END))

        ttk.Label(time_frame, text=":").grid(row=0, column=1, padx=5)
        minute_spinbox = ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.minute_var, 
                                    width=5, format="%02.0f")
        minute_spinbox.grid(row=0, column=2)
        # Select all on click/focus
        minute_spinbox.bind('<Button-1>', lambda e: minute_spinbox.select_range(0, tk.END))
        minute_spinbox.bind('<FocusIn>', lambda e: minute_spinbox.select_range(0, tk.END))
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
        self.procedure_combos = []  # Track combobox widgets
        for i in range(4):
            ttk.Label(procedures_frame, text=f"Thủ thuật {i+1}:").grid(
                row=i, column=0, sticky=tk.W, pady=5, padx=(0, 10))
            var = tk.StringVar()
            dropdown = ttk.Combobox(procedures_frame, textvariable=var, 
                                   values=self.available_procedures, width=35, state='readonly')
            dropdown.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=5)
            # Auto-focus next on selection
            dropdown.bind('<<ComboboxSelected>>', lambda e, idx=i: self.on_procedure_selected(e, idx))
            # Manual open with Down arrow key only (no auto-open)
            self.procedure_vars.append(var)
            self.procedure_combos.append(dropdown)
            self.all_comboboxes.append(dropdown)
        
        # Staff Section - Autocomplete comboboxes
        staff_frame = ttk.LabelFrame(main_frame, text="Staff Members (Người thực hiện)", 
                                    padding="10")
        staff_frame.grid(row=row, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        ttk.Label(staff_frame, text="💡 Gõ tên để tìm nhanh, chọn 1-3 người theo thứ tự:").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # Get available staff (capitalize for display) and filter out disabled staff
        self.available_staff = sorted([k for k in map_ys_bs.keys() if k not in config.disabled_staff])
        self.staff_display = [s.title() for s in self.available_staff]
        
        # Create 3 staff comboboxes with autocomplete
        self.staff_vars = []
        self.staff_combos = []  # Track combobox widgets
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
                    if event.keysym in ('Return', 'Up', 'Down', 'Next', 'Prior'):
                        return
                    
                    value = var_widget.get()
                    if value == '':
                        combo_widget['values'] = values_list
                    else:
                        search_term = remove_accents(value)
                        data = []
                        for item in values_list:
                            if search_term in remove_accents(item):
                                data.append(item)
                        combo_widget['values'] = data
                        
                        # Show dropdown if matches found
                        if data:
                            try:
                                combo_widget.event_generate('<Down>')
                            except:
                                pass
                                
                def on_focus_out(event):
                     # Optional: enforce selection or leave as is
                     pass

                return on_keyrelease
            
            combo.bind('<KeyRelease>', make_autocomplete(combo, var, self.staff_display))
            # Handle Enter to select first option if available or move focus
            def on_enter(event, combo=combo, var=var):
                values = combo['values']
                if values:
                     # If exact match or close enough, maybe select?
                     # For now just let standard combobox behavior work or user arrow keys.
                     # If user hits enter and dropdown is showing, it selects.
                     pass
                self.focus_next_widget(event)
                return "break" # Prevent default behavior
                
            combo.bind('<Return>', on_enter)
            # Auto-focus next on selection (if user clicks)
            combo.bind('<<ComboboxSelected>>', lambda e, idx=i: self.on_staff_selected(e, idx))
            # Manual open with Down arrow key only (no auto-open)
            
            self.staff_vars.append(var)
            self.staff_combos.append(combo)
            self.all_comboboxes.append(combo)
        
        # Bind Enter key navigation for other fields
        self.patient_id_entry.bind('<Return>', self.focus_next_widget)
        self.date_entry.bind('<Return>', self.focus_next_widget)
        hour_spinbox.bind('<Return>', self.focus_next_widget)
        minute_spinbox.bind('<Return>', self.focus_next_widget)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, columnspan=2, pady=15)
        
        save_btn = ttk.Button(button_frame, text="💾 Save & Add to Queue", 
                             command=self.save_entry, style="Accent.TButton")
        save_btn.grid(row=0, column=0, padx=5)
        
        # Only show delete button if editing existing entry
        if self.initial_data and self.on_delete_callback:
            delete_btn = ttk.Button(button_frame, text="🗑️ Delete", 
                                   command=self.confirm_delete)
            delete_btn.grid(row=0, column=1, padx=5)
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_btn.grid(row=0, column=2, padx=5)
        
        # Info Label
        info_label = ttk.Label(main_frame, 
                              text="💡 Chọn đủ 4 thủ thuật và ít nhất 1 người thực hiện",
                              font=('Arial', 9), foreground="gray")
        info_label.grid(row=row+1, column=0, columnspan=2, pady=(0, 10))
        
        # Pre-fill data if editing (must be after all widgets are created)
        if self.initial_data:
            self.prefill_data()
    
    def on_date_key_release(self, event):
        """Handle smart date formatting."""
        # ignore backspace or delete
        if event.keysym in ('BackSpace', 'Delete'):
            return

        entry = self.date_entry
        text = entry.get()
        cursor_pos = entry.index(tk.INSERT)
        
        # Only process if we are at the end of the input to avoid messing up editing in middle
        if cursor_pos != len(text):
            return

        new_text = text
        
        # Auto-add dash after day (2 chars)
        if len(text) == 2 and text.isdigit():
            new_text = text + "-"
        
        # Auto-add dash after month (5 chars: dd-mm)
        elif len(text) == 5:
            # Check if headers are valid digits before adding dash
            parts = text.split('-')
            if len(parts) == 2 and len(parts[1]) == 2 and parts[1].isdigit():
                new_text = text + "-"
                
        # Auto-expand year (dd-mm-yy -> dd-mm-20yy)
        elif len(text) == 8:
            parts = text.split('-')
            if len(parts) == 3 and len(parts[2]) == 2 and parts[2].isdigit():
                yy = parts[2]
                new_text = f"{parts[0]}-{parts[1]}-20{yy}"

        if new_text != text:
            entry.delete(0, tk.END)
            entry.insert(0, new_text)
    
    def increment_date(self, event):
        """Increase date by one day using Up arrow."""
        try:
            current_text = self.date_entry.get().strip()
            current_date = datetime.strptime(current_text, "%d-%m-%Y")
            new_date = current_date + timedelta(days=1)
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, new_date.strftime("%d-%m-%Y"))
        except:
            pass  # If date is invalid, do nothing
        return "break"  # Prevent default behavior
    
    def decrement_date(self, event):
        """Decrease date by one day using Down arrow."""
        try:
            current_text = self.date_entry.get().strip()
            current_date = datetime.strptime(current_text, "%d-%m-%Y")
            new_date = current_date - timedelta(days=1)
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, new_date.strftime("%d-%m-%Y"))
        except:
            pass  # If date is invalid, do nothing
        return "break"  # Prevent default behavior
    
    def prefill_data(self):
        """Pre-fill form with initial data for editing."""
        if not self.initial_data:
            return
        
        data = self.initial_data
        
        # Fill patient ID
        if 'id' in data:
            self.patient_id_var.set(data['id'])
        
        # Fill date - use the 'ngay' field directly
        if 'ngay' in data:
            date_value = data['ngay']
            self.date_entry.delete(0, tk.END)
            self.date_entry.insert(0, date_value)
        
        # Fill time from first procedure
        if 'thu_thuats' in data and len(data['thu_thuats']) > 0:
            first_proc = data['thu_thuats'][0]
            # Try to extract time from 'Ngay BD TH' field
            if 'Ngay BD TH' in first_proc:
                time_str = first_proc['Ngay BD TH'].replace('{SPACE}', ' ')
                # Format is "DD-MM-YYYY HH:MM"
                if ' ' in time_str:
                    parts = time_str.split(' ')
                    if len(parts) >= 2:
                        time_part = parts[1]  # Get the HH:MM part
                        if ':' in time_part:
                            hour, minute = time_part.split(':')
                            self.hour_var.set(hour.zfill(2))  # Ensure 2 digits
                            self.minute_var.set(minute.zfill(2))
            
            # Fill procedures
            for i, proc in enumerate(data['thu_thuats'][:4]):
                if i < len(self.procedure_vars):
                    proc_name = proc.get('Ten', '')
                    self.procedure_vars[i].set(proc_name)
            
            # Update procedure options after setting values
            self.update_procedure_options()
            
            # Fill staff - extract unique staff from procedures
            staff_names = []
            for proc in data['thu_thuats']:
                staff_full = proc.get('Nguoi Thuc Hien', '')
                # Convert full name back to short name
                staff_short = None
                for short, full in map_ys_bs.items():
                    if full == staff_full and short not in [s.lower() for s in staff_names]:
                        staff_short = short.title()
                        break
                if staff_short and len(staff_names) < 3:
                    staff_names.append(staff_short)
            
            # Set staff values
            for i, staff_name in enumerate(staff_names):
                if i < len(self.staff_vars):
                    self.staff_vars[i].set(staff_name)
            
            # Update staff options after setting values
            self.update_staff_options()
    
    def on_procedure_selected(self, event, combo_index):
        """Handle procedure selection and update other comboboxes."""
        # Update available options in all other procedure comboboxes
        self.update_procedure_options()
        # Then move focus
        self.focus_next_widget(event)
    
    def on_staff_selected(self, event, combo_index):
        """Handle staff selection and update other comboboxes."""
        # Update available options in all other staff comboboxes
        self.update_staff_options()
        # Then move focus
        self.focus_next_widget(event)
    
    def update_procedure_options(self):
        """Update available options in procedure comboboxes based on current selections."""
        # Get all currently selected procedures
        selected = [var.get() for var in self.procedure_vars if var.get()]
        
        # Update each combobox
        for i, combo in enumerate(self.procedure_combos):
            current_value = self.procedure_vars[i].get()
            # Available options = all options minus selected (except current)
            available = [p for p in self.available_procedures if p not in selected or p == current_value]
            combo['values'] = available
    
    def update_staff_options(self):
        """Update available options in staff comboboxes based on current selections."""
        # Get all currently selected staff (normalize to title case)
        selected = [var.get() for var in self.staff_vars if var.get()]
        
        # Update each combobox
        for i, combo in enumerate(self.staff_combos):
            current_value = self.staff_vars[i].get()
            # Available options = all options minus selected (except current)
            available = [s for s in self.staff_display if s not in selected or s == current_value]
            combo['values'] = available
        
    def validate_input(self):
        """Validate user input."""
        # Check patient ID
        if not self.patient_id_var.get().strip():
            messagebox.showerror("Validation Error", "Please enter a Patient ID.")
            return False
        
        # Check date
        try:
            date_str = self.date_entry.get().strip()
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
            # Get date
            date_str = self.date_entry.get().strip()
            
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
            save_manual_entry_to_db(
                patient_id=data['id'],
                procedures="-".join(procedures),
                staff="-".join(staff),
                appointment_date=date_str,
                appointment_time=time_str,
                notes=""
            )
            
            self.result = data
            
            # Call callback if provided
            if self.on_save_callback:
                self.on_save_callback(data)
            
            # Remember this date for next entry
            ManualEntryDialog.last_used_date = date_str
            
            # Continuous Entry: Clear form instead of closing
            # Keep ID and select all for easy overwrite
            # self.patient_id_var.set("")
            
            # Clear Procedures
            for var in self.procedure_vars:
                var.set("")
            # Reset procedure options
            self.update_procedure_options()
                
            # Clear Staff
            for var in self.staff_vars:
                var.set("")
            # Reset staff options
            self.update_staff_options()
            
            # Visual feedback
            # Show a temporary success label or just a quick message
            
            # Focus back to Patient ID
            # Use after() to ensure focus works after messagebox if used, 
            # but we want to be faster so maybe just a label update?
            # Let's use a non-intrusive status or title update
            original_title = self.dialog.title()
            self.dialog.title(f"✓ Saved {data['id']}! Ready for next...")
            self.dialog.after(2000, lambda: self.dialog.title(original_title))
            
            # Force focus to ID entry
            # Force focus to ID entry and select all
            self.patient_id_entry.focus_set()
            self.patient_id_entry.select_range(0, tk.END)
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save entry:\n{str(e)}")
    
    def on_close(self):
        """Handle dialog closing to cleanup bindings."""
        # Unbind mousewheel to prevent errors after destroy
        if hasattr(self, '_mousewheel_func'):
            try:
                self.dialog.unbind_all("<MouseWheel>")
            except:
                pass
        
        self.result = None
        self.dialog.destroy()

    def cancel(self):
        """Cancel and close dialog."""
        self.on_close()
    
    def confirm_delete(self):
        """Confirm and delete the current entry."""
        if not self.initial_data:
            return
        
        patient_id = self.initial_data.get('id', 'Unknown')
        response = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete the entry for Patient ID: {patient_id}?\n\nThis action cannot be undone.",
            icon='warning'
        )
        
        if response:
            # Call delete callback if provided
            if self.on_delete_callback:
                self.on_delete_callback()
            # Close dialog
            self.on_close()
    
    def clear_focus(self, event):
        """Clear focus when clicking background or pressing Esc."""
        # First, ensure dialog processes any pending events
        self.dialog.update_idletasks()
        
        # Try to close all dropdowns by focusing elsewhere temporarily
        # This forces comboboxes to close their popups
        try:
            # Create a temporary dummy widget to steal focus
            # then immediately set focus to dialog
            self.dialog.focus_set()
            self.dialog.update_idletasks()
        except:
            pass

    def bind_recursive_click(self, widget):
        """Recursively bind click event to widget and its children to clear focus."""
        # Don't bind to entry/combobox/button/spinbox components that need focus/click
        try:
            bind_tags = widget.bindtags()
            # Basic check: if it's an input widget, skip
            if isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Spinbox, ttk.Button, tk.Text)):
                pass # Don't override
            else:
                # Bind to the widget
                widget.bind('<Button-1>', self.clear_focus, add='+')
            
            # Recurse for children
            for child in widget.winfo_children():
                self.bind_recursive_click(child)
        except:
            pass

    def focus_next_widget(self, event):
        """Move focus to the next widget."""
        event.widget.tk_focusNext().focus()
        return "break"
        
    def show(self):
        """Show the dialog and wait for it to close."""
        self.dialog.wait_window()
        return self.result

