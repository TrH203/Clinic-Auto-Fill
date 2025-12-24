import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import threading
import time


class CoordinateConfigDialog:
    """Dialog for configuring UI element coordinates with capture functionality."""
    
    def __init__(self, parent):
        self.parent = parent
        self.dialog = None
        self.coords_data = {}
        self.entry_widgets = {}
        self.capture_mode = False
        self.overlay_window = None
        
    def show(self):
        """Display the coordinate configuration dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Cấu Hình Tọa Độ")
        self.dialog.geometry("750x650")
        self.dialog.resizable(True, True)
        
        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        self.load_coordinates()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        self.dialog.wait_window()
        
    def setup_ui(self):
        """Setup the UI components."""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Cấu Hình Tọa Độ UI", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Instructions
        instructions = ttk.Label(main_frame, 
                                text="Nhấn 'Bắt Tọa Độ' để chọn vị trí mới trên màn hình. "
                                     "Cửa sổ sẽ thu nhỏ, đếm ngược 3 giây, sau đó click vào vị trí mong muốn.",
                                wraplength=650,
                                justify="left")
        instructions.pack(pady=(0, 10))
        
        # Create scrollable frame for coordinates
        canvas = tk.Canvas(main_frame, height=350)
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
        
        self.coords_frame = scrollable_frame
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        save_btn = ttk.Button(button_frame, text="💾 Lưu Tất Cả", 
                             command=self.save_all_coordinates)
        save_btn.pack(side="left", padx=(0, 5))
        
        restore_btn = ttk.Button(button_frame, text="🔄 Khôi Phục Mặc Định", 
                                command=self.restore_defaults)
        restore_btn.pack(side="left", padx=(0, 5))
        
        close_btn = ttk.Button(button_frame, text="Đóng", 
                              command=self.dialog.destroy)
        close_btn.pack(side="right")
        
    def load_coordinates(self):
        """Load coordinates from database and display them."""
        from database import get_all_coordinates
        
        coords = get_all_coordinates()
        
        # Sort by name for consistent display
        sorted_coords = sorted(coords.items())
        
        # Create header
        header_frame = ttk.Frame(self.coords_frame)
        header_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        ttk.Label(header_frame, text="Tên", font=('Arial', 9, 'bold'), width=25).grid(row=0, column=0, padx=5)
        ttk.Label(header_frame, text="X", font=('Arial', 9, 'bold'), width=8).grid(row=0, column=1, padx=5)
        ttk.Label(header_frame, text="Y", font=('Arial', 9, 'bold'), width=8).grid(row=0, column=2, padx=5)
        ttk.Label(header_frame, text="Mô Tả", font=('Arial', 9, 'bold'), width=25).grid(row=0, column=3, padx=5)
        ttk.Label(header_frame, text="", width=12).grid(row=0, column=4)
        
        # Add separator
        ttk.Separator(self.coords_frame, orient='horizontal').pack(fill='x', padx=5, pady=(0, 5))
        
        # Create rows for each coordinate
        for name, (x, y, description) in sorted_coords:
            self.coords_data[name] = {'x': x, 'y': y, 'description': description}
            self.create_coord_row(name, x, y, description)
    
    def create_coord_row(self, name, x, y, description):
        """Create a row for a single coordinate."""
        row_frame = ttk.Frame(self.coords_frame)
        row_frame.pack(fill="x", padx=5, pady=2)
        
        # Name label
        name_label = ttk.Label(row_frame, text=name, width=25)
        name_label.grid(row=0, column=0, padx=5, sticky="w")
        
        # X coordinate
        x_var = tk.IntVar(value=x)
        x_entry = ttk.Entry(row_frame, textvariable=x_var, width=8)
        x_entry.grid(row=0, column=1, padx=5)
        
        # Y coordinate
        y_var = tk.IntVar(value=y)
        y_entry = ttk.Entry(row_frame, textvariable=y_var, width=8)
        y_entry.grid(row=0, column=2, padx=5)
        
        # Description
        desc_label = ttk.Label(row_frame, text=description[:30], width=25)
        desc_label.grid(row=0, column=3, padx=5, sticky="w")
        
        # Capture button
        capture_btn = ttk.Button(row_frame, text="🎯 Bắt Tọa Độ", 
                                command=lambda: self.capture_coordinate(name, x_var, y_var))
        capture_btn.grid(row=0, column=4, padx=5)
        
        # Store references
        self.entry_widgets[name] = {
            'x_var': x_var,
            'y_var': y_var,
            'x_entry': x_entry,
            'y_entry': y_entry
        }
    
    
    def capture_coordinate(self, coord_name, x_var, y_var):
        """Show cursor position for user to manually copy coordinates."""
        # Create position display window
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
        
        title_label = ttk.Label(frame, 
                               text=f"Hiển Thị Vị Trí: {coord_name}",
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # Large position display
        pos_label = ttk.Label(frame,
                             text="X: 0, Y: 0",
                             font=('Arial', 16, 'bold'),
                             foreground='blue')
        pos_label.pack(pady=20)
        
        instruction = ttk.Label(frame,
                               text="Di chuyển chuột đến vị trí mong muốn\nSau đó nhập thủ công giá trị X, Y vào ô bên trái\n\nNhấn ESC hoặc Đóng để thoát",
                               font=('Arial', 9),
                               justify="center")
        instruction.pack(pady=10)
        
        # Update position continuously
        def update_position():
            if pos_window.winfo_exists():
                try:
                    pos = pyautogui.position()
                    pos_label.config(text=f"X: {pos.x}, Y: {pos.y}")
                    pos_window.after(50, update_position)
                except:
                    pass
        
        update_position()
        
        # Close button
        def close_window():
            pos_window.destroy()
        
        close_btn = ttk.Button(frame, text="Đóng (ESC)", command=close_window)
        close_btn.pack(pady=10)
        
        # Bind ESC key
        pos_window.bind('<Escape>', lambda e: close_window())
        
        # Focus on window so ESC works
        pos_window.focus_set()
    
    
    def save_all_coordinates(self):
        """Save all coordinates to database."""
        try:
            from database import save_all_coordinates
            import config
            
            # Collect all coordinates from entry widgets
            coords_to_save = {}
            for name, widgets in self.entry_widgets.items():
                x = widgets['x_var'].get()
                y = widgets['y_var'].get()
                description = self.coords_data[name]['description']
                coords_to_save[name] = (x, y, description)
            
            # Save to database
            save_all_coordinates(coords_to_save)
            
            # Reload coordinates in config module
            config.reload_coordinates()
            
            messagebox.showinfo("Thành Công", 
                              f"Đã lưu {len(coords_to_save)} tọa độ vào database.",
                              parent=self.dialog)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu tọa độ:\n{str(e)}", 
                               parent=self.dialog)
    
    def restore_defaults(self):
        """Restore all coordinates to default values."""
        result = messagebox.askyesno("Xác Nhận", 
                                    "Bạn có chắc muốn khôi phục tất cả tọa độ về giá trị mặc định?",
                                    parent=self.dialog)
        
        if result:
            try:
                from database import restore_default_coordinates, get_all_coordinates
                import config
                
                # Restore to defaults in database
                restore_default_coordinates()
                
                # Reload coordinates in config module
                config.reload_coordinates()
                
                # Reload the UI
                self.dialog.destroy()
                self.show()
                
                messagebox.showinfo("Thành Công", 
                                  "Đã khôi phục tất cả tọa độ về giá trị mặc định.",
                                  parent=self.dialog)
                
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể khôi phục tọa độ mặc định:\n{str(e)}", 
                                   parent=self.dialog)


if __name__ == "__main__":
    # Test the dialog
    root = tk.Tk()
    root.withdraw()
    
    dialog = CoordinateConfigDialog(root)
    dialog.show()
