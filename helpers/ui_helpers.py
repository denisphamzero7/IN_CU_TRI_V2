import ttkbootstrap as ttk
from ttkbootstrap.constants import *

def create_button(master, text, command, style="primary", width=None, icon=None):
    """
    Tạo nút bấm chuẩn ttkbootstrap.
    
    Args:
        style: Tên màu (primary, success, danger) hoặc kèm kiểu (primary-outline, success-link)
    """
    # ttkbootstrap hỗ trợ từ khóa "outline" để làm nút viền
    # Ví dụ: style="danger-outline"
    
    btn = ttk.Button(
        master, 
        text=text, 
        command=command,
        bootstyle=style, # Đây là sức mạnh của ttkbootstrap
        width=width,
        image=icon,
        compound=LEFT if icon else None # Nếu có icon thì đặt bên trái chữ
    )
    return btn