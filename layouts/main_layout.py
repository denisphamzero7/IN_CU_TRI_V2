# layouts/main_layout.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

def create_3_columns(master):
    """
    Tạo bố cục 3 cột có thể thay đổi kích thước (Resizeable)
    Sử dụng ttk.Panedwindow (chữ w thường)
    """

    # --- SỬA LẠI DÒNG NÀY (PanedWindow -> Panedwindow) ---
    main_pane = ttk.Panedwindow(master, orient=HORIZONTAL, bootstyle="default")
    main_pane.pack(fill=BOTH, expand=YES)

    # --- 2. Cột Trái (Left Sidebar) ---
    left = ttk.Frame(main_pane, bootstyle="secondary", padding=10)
    
    # --- 3. Cột Giữa (Main Content) ---
    mid = ttk.Frame(main_pane, padding=10, relief="solid", borderwidth=1)
    
    # --- 4. Cột Phải (Right Panel) ---
    right = ttk.Frame(main_pane, bootstyle="dark", padding=10)

    # --- 5. Add vào Panedwindow ---
    main_pane.add(left, weight=1)  
    main_pane.add(mid, weight=3)   
    main_pane.add(right, weight=6) 

    return left, mid, right