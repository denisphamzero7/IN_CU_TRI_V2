import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config.settings import APP_BG_COLOR 

def create_3_columns(master):
    """
    Tạo bố cục 3 cột.
    Đã điều chỉnh cột Left để KHỚP với chữ 'Đà Nẵng'.
    """
    main_pane = ttk.Panedwindow(master, orient=HORIZONTAL)
    main_pane.pack(fill=BOTH, expand=YES)

    # --- 1. Cột Trái (Menu) ---
    # [ĐIỀU CHỈNH LẠI]: Tăng từ 180 lên 265.
    # Con số 265px này đảm bảo hiển thị đủ dòng "ỦY BAN... ĐÀ NẴNG" 
    # và khung "Thông tin liên hệ" bên dưới mà không bị cắt chữ.
    left = tk.Frame(main_pane, bg=APP_BG_COLOR, width=265) 
    
    # Giữ cố định size này để không bị nội dung bên trong làm vỡ khung
    left.pack_propagate(False) 
    left.grid_propagate(False)
    
    # --- 2. Cột Giữa (Dữ liệu) ---
    # Mid chiếm khoảng 35% không gian còn lại
    mid = tk.Frame(main_pane, bg=APP_BG_COLOR, width=500)
    
    # --- 3. Cột Phải (Preview) ---
    # Right chiếm khoảng 50%
    right = tk.Frame(main_pane, bg=APP_BG_COLOR, width=700)

    # --- Cấu hình Weight ---
    # Left = 15: Tỉ lệ vừa phải, kết hợp với width=265 sẽ ra giao diện chuẩn.
    # Mid = 35
    # Right = 50
    
    main_pane.add(left, weight=15)   
    main_pane.add(mid, weight=35)    
    main_pane.add(right, weight=50)  

    return left, mid, right