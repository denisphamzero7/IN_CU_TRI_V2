import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
# Import màu từ settings để đồng bộ
from config.settings import APP_BG_COLOR 

def create_3_columns(master):
    """
    Tạo bố cục 3 cột (Trái - Giữa - Phải)
    Sử dụng tk.Frame thuần để đảm bảo nền màu MISA đồng nhất
    """

    # Panedwindow vẫn dùng ttk để có thanh kéo co giãn đẹp
    # style có thể cần cấu hình, nhưng mặc định nó khá trung tính
    main_pane = ttk.Panedwindow(master, orient=HORIZONTAL)
    main_pane.pack(fill=BOTH, expand=YES)

    # --- 2. Cột Trái (Left Sidebar) ---
    # Dùng tk.Frame + bg=APP_BG_COLOR
    # Bỏ padding ở đây, để padding cho View con xử lý thì linh hoạt hơn
    left = tk.Frame(main_pane, bg=APP_BG_COLOR) 
    
    # --- 3. Cột Giữa (Main Content) ---
    # Dùng tk.Frame + bg=APP_BG_COLOR
    # Thêm highlightthickness=1 để tạo đường kẻ mỏng ngăn cách nếu muốn
    mid = tk.Frame(main_pane, bg=APP_BG_COLOR, highlightthickness=0)
    
    # --- 4. Cột Phải (Right Panel) ---
    # Dùng tk.Frame + bg=APP_BG_COLOR
    right = tk.Frame(main_pane, bg=APP_BG_COLOR)

    # --- 5. Add vào Panedwindow ---
    main_pane.add(left, weight=1)   # Cột trái nhỏ
    main_pane.add(mid, weight=3)    # Cột giữa vừa
    main_pane.add(right, weight=6)  # Cột phải lớn (Preview)

    return left, mid, right