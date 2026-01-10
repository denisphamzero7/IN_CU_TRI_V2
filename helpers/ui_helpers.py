# helpers/ui_helpers.py

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from helpers.path_manager import resource_path
from config.settings import APP_ICON_NAME

# Thêm tham số padding mặc định là None
def create_button(master, text, command, style="primary", width=None, icon=None, padding=None, **kwargs):
    """
    Tạo nút bấm chuẩn ttkbootstrap.
    - padding: (ngang, dọc) hoặc (trái, trên, phải, dưới). VD: (10, 20) để nút cao hơn.
    """
    
    # [FIX LỖI]: Loại bỏ 'font' khỏi kwargs (như code cũ của bạn)
    if 'font' in kwargs:
        kwargs.pop('font') 

    # [LOGIC]: Compound
    comp_state = LEFT if (icon and text) else None

    # Nếu người dùng truyền padding, thêm vào kwargs để ttk.Button xử lý
    # Nếu không truyền, để ttk tự quyết định (thường là mặc định của theme)
    if padding:
        kwargs['padding'] = padding

    btn = ttk.Button(
        master, 
        text=text, 
        command=command,
        bootstyle=style, 
        width=width,
        image=icon,
        compound=comp_state,
        **kwargs 
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