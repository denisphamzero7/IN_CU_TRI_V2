import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config.settings import APP_BG_COLOR 

def create_3_columns(master):
    """
    Tạo bố cục 3 cột với tỷ lệ điều chỉnh:
    - Left:  Thu hẹp lại (Menu cố định nhỏ gọn)
    - Mid:   Vừa phải cho danh sách
    - Right: Mở rộng tối đa cho Preview
    """
    main_pane = ttk.Panedwindow(master, orient=HORIZONTAL)
    main_pane.pack(fill=BOTH, expand=YES)

    # --- 1. Cột Trái (Menu) ---
    # GIẢM WIDTH: Từ 265 xuống 180 hoặc 200 tùy ý bạn
    left = tk.Frame(main_pane, bg=APP_BG_COLOR, width=255) 
    
    # Giữ nguyên propagate(False) để form không bị co lại theo nút bấm bé xíu bên trong
    left.pack_propagate(False) 
    left.grid_propagate(False) 
    
    # --- 2. Cột Giữa (Dữ liệu) ---
    # Tăng nhẹ để bù trừ khoảng trống nếu cần
    mid = tk.Frame(main_pane, bg=APP_BG_COLOR, width=400)
    
    # --- 3. Cột Phải (Preview) ---
    right = tk.Frame(main_pane, bg=APP_BG_COLOR, width=850)

    # --- Cấu hình Weight (Tỷ lệ co giãn) ---
    # Mẹo: Để cột Menu (Left) ít bị giãn ra khi phóng to full màn hình, 
    # hãy để weight của nó thật nhỏ (hoặc bằng 0 nếu muốn cố định size).
    
    main_pane.add(left, weight=0)    # Đổi weight thành 0 hoặc số nhỏ (ví dụ 5) để nó giữ size gọn
    main_pane.add(mid, weight=30)    # Tăng weight cột giữa
    main_pane.add(right, weight=70)  # Dồn phần lớn không gian cho cột phải

    return left, mid, right