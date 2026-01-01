# layouts/main_layout.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

def create_3_columns(master):
    """
    Tạo bố cục 3 cột sử dụng place (giữ nguyên tỷ lệ % như code cũ)
    master: là MainView (ttk.Frame)
    """

    # --- 1. Cột Trái (Left Sidebar) ---
    # Dùng style "secondary" để có màu nền xám nhẹ (phân biệt với nền chính)
    # padding=10: tạo khoảng cách nội dung bên trong frame
    left = ttk.Frame(master, bootstyle="secondary", padding=10)
    left.place(relx=0, rely=0, relwidth=0.22, relheight=1.0)
    
    # --- 2. Cột Giữa (Main Content) ---
    # Dùng style mặc định (không set bootstyle) hoặc "light" để làm nền chính
    # Thêm border theo kiểu ttk: dùng relief="solid" (tùy chọn)
    mid = ttk.Frame(master, padding=10, relief="solid", borderwidth=1)
    mid.place(relx=0.22, rely=0, relwidth=0.43, relheight=1.0)
    
    # --- 3. Cột Phải (Right Panel) ---
    # Bạn muốn màu tối? Dùng bootstyle="dark"
    # Lưu ý: Nếu dùng theme 'superhero' (vốn đã tối), thì 'dark' sẽ càng tối hơn hoặc đen hẳn.
    right = ttk.Frame(master, bootstyle="dark", padding=10)
    right.place(relx=0.65, rely=0, relwidth=0.35, relheight=1.0)
    
    return left, mid, right