import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config.settings import APP_BG_COLOR 

def create_3_columns(master):
    """
    Tạo bố cục 3 cột với tỷ lệ mới:
    - Left:  15% (Giữ nguyên - Đủ cho menu)
    - Mid:   25% (Thu hẹp lại)
    - Right: 60% (Mở rộng tối đa cho Preview)
    """
    main_pane = ttk.Panedwindow(master, orient=HORIZONTAL)
    main_pane.pack(fill=BOTH, expand=YES)

    # --- 1. Cột Trái (Menu) ---
    # Giữ nguyên width=265 và các thuộc tính cố định khung
    left = tk.Frame(main_pane, bg=APP_BG_COLOR, width=265) 
    left.pack_propagate(False) 
    left.grid_propagate(False) 
    
    # --- 2. Cột Giữa (Dữ liệu) ---
    # Giảm width khởi tạo xuống một chút (400) để khớp với weight 25%
    mid = tk.Frame(main_pane, bg=APP_BG_COLOR, width=400)
    
    # --- 3. Cột Phải (Preview) ---
    # Tăng width khởi tạo lên (850) để khớp với weight 60%
    right = tk.Frame(main_pane, bg=APP_BG_COLOR, width=850)

    # --- Cấu hình Weight (Tỷ lệ co giãn) ---
    # Tổng: 15 + 25 + 60 = 100
    
    main_pane.add(left, weight=15)   # Giữ nguyên
    main_pane.add(mid, weight=25)    # Giảm từ 35 xuống 25
    main_pane.add(right, weight=60)  # Tăng từ 50 lên 60

    return left, mid, right