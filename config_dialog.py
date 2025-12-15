import tkinter as tk
from tkinter import ttk, messagebox
import config
from database import get_disabled_staff, set_disabled_staff

class ConfigDialog:
    def __init__(self, parent):
        """Initialize the config dialog."""
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Staff Configuration")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        
        # Make dialog modal
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center dialog
        self.center_dialog()
        
        # Store checkbox variables
        self.checkbox_vars = {}
        
        self.setup_ui()
    
    def center_dialog(self):
        """Center the dialog on  the parent window."""
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
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Manage Staff Availability", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Info label
        info_label = ttk.Label(main_frame, 
                              text="Uncheck staff members to disable them from manual entry and automation",
                              font=('Arial', 9), foreground="gray", wraplength=450)
        info_label.pack(pady=(0, 15))
        
        # Scrollable frame for checkboxes
        canvas = tk.Canvas(main_frame, height=400)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create checkboxes for each staff member
        disabled_staff = get_disabled_staff()
        for short_name, full_name in sorted(config.map_ys_bs.items(), key=lambda x: x[1]):
            var = tk.BooleanVar(value=short_name not in disabled_staff)
            self.checkbox_vars[short_name] = var
            
            cb = ttk.Checkbutton(scrollable_frame, 
                                text=f"{full_name} ({short_name})",
                                variable=var)
            cb.pack(anchor="w", pady=2, padx=10)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(pady=(15, 0))
        
        save_btn = ttk.Button(button_frame, text="💾 Save", command=self.save_config, 
                             style="Accent.TButton")
        save_btn.grid(row=0, column=0, padx=5)
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.cancel)
        cancel_btn.grid(row=0, column=1, padx=5)
    
    def save_config(self):
        """Save the configuration to database."""
        # Get list of disabled staff
        disabled = [name for name, var in self.checkbox_vars.items() if not var.get()]
        
        # Save to database
        set_disabled_staff(disabled)
        
        messagebox.showinfo("Success", f"Configuration saved!\n{len(disabled)} staff member(s) disabled.")
        self.dialog.destroy()
    
    def write_config_to_file(self, disabled_staff_list):
        """Write the disabled_staff list to config.py file."""
        try:
            import os
            config_path = os.path.join(os.path.dirname(__file__), 'config.py')
            
            with open(config_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Find and replace the disabled_staff line
            new_lines = []
            skip_disabled = False
            for line in lines:
                if 'disabled_staff = [' in line or 'disabled_staff=[' in line:
                    # Replace with new list
                    disabled_str = ', '.join([f'"{name}"' for name in disabled_staff_list])
                    new_lines.append(f'disabled_staff = [{disabled_str}]\n')
                    skip_disabled = True
                elif skip_disabled and ']' in line and 'disabled_staff' not in line:
                    skip_disabled = False
                    continue
                elif not skip_disabled:
                    new_lines.append(line)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config file:\n{str(e)}")
    
    def cancel(self):
        """Cancel and close dialog."""
        self.dialog.destroy()
    
    def show(self):
        """Show the dialog and wait for it to close."""
        self.dialog.wait_window()
