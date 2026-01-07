# helpers/ui_helpers.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from helpers.path_manager import resource_path
from config.settings import APP_ICON_NAME

def create_button(master, text, command, style="primary", width=None, icon=None, **kwargs):
    """
    Tạo nút bấm chuẩn ttkbootstrap.
    
    Args:
        style: Tên màu (primary, success, danger) hoặc kèm kiểu (primary-outline, success-link)
        **kwargs: Các tham số khác của ttk.Button (ví dụ: state, cursor, padding...)
    """
    
    btn = ttk.Button(
        master, 
        text=text, 
        command=command,
        bootstyle=style, # Đây là sức mạnh của ttkbootstrap
        width=width,
        image=icon,
        compound=LEFT if icon else None, # Nếu có icon thì đặt bên trái chữ
        **kwargs # <--- [QUAN TRỌNG] Truyền các tham số mở rộng (như state="disabled") vào đây
    )
    return btn

def apply_window_icon(window):
    """
    Hàm này áp dụng icon .ico cho bất kỳ cửa sổ nào được truyền vào (window).
    Dùng cho cả Main Window và Toplevel Window.
    """
    try:
        # Lấy đường dẫn file .ico
        icon_path = resource_path(f"assets/{APP_ICON_NAME}")
        
        # Lệnh này dành riêng cho file .ico trên Windows
        # Nó set icon ở góc trái trên cùng Title Bar VÀ dưới thanh Taskbar
        window.iconbitmap(icon_path)
        
    except Exception as e:
        print(f"⚠️ Lỗi set icon: {e}")