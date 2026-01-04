import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config.settings import APP_TITLE,APP_HEADER, APP_ADDRESS, APP_PHONE, APP_EMAIL

class HeaderView(ttk.Frame):
    def __init__(self, parent):
        # Frame ngoài cùng: padding=5 để tạo khoảng cách với lề trái/phải/trên
        super().__init__(parent, padding=5) 
        self.pack(fill=X)
        
        # --- CẤU HÌNH AN TOÀN ---
        # Trừ đi padding (5*2) và viền (2*2) ~ 14px. Panel ~280-300px.
        SAFE_WIDTH = 250 
        
        # --- TẠO KHUNG VIỀN (BORDER CONTAINER) ---
        # Dùng màu 'warning' (Vàng cam) làm viền mỏng để tạo sự trang trọng
        border_frame = ttk.Frame(self, bootstyle="warning", padding=2)
        border_frame.pack(fill=X)

        # --- 1. PHẦN TIÊU ĐỀ (BANNER MÀU ĐỎ) ---
        title_frame = ttk.Frame(border_frame, bootstyle="danger", padding=(5, 10))
        title_frame.pack(fill=X)
        
        # Quốc huy hoặc Icon ngôi sao vàng (nếu muốn đơn giản dùng text)
        # ttk.Label(
        #     title_frame,
        #     # text="★ ★ ★", # Trang trí
        #     font=("Segoe UI", 8),
        #     bootstyle="inverse-danger",
        #     anchor="center"
        # ).pack(fill=X)

        ttk.Label(
            title_frame, 
            text=APP_HEADER.upper(), 
            font=("Segoe UI", 10, "bold"), 
            bootstyle="inverse-danger", # Chữ trắng trên nền đỏ
            anchor="center",
            justify="center",
            wraplength=SAFE_WIDTH
        ).pack(fill=X, pady=(2, 5))

        # --- 2. PHẦN THÔNG TIN (NỀN TỐI) ---
        info_frame = ttk.Frame(border_frame, bootstyle="dark", padding=10)
        info_frame.pack(fill=X)

        def create_info_row(icon, text, color="white"):
            row = ttk.Frame(info_frame, bootstyle="dark")
            row.pack(fill=X, pady=2)
            
            # Icon màu vàng cam (warning) để nổi bật trên nền tối
            ttk.Label(
                row, text=icon, font=("Segoe UI Emoji", 9), 
                bootstyle="warning", width=3, anchor="n"
            ).pack(side=LEFT, anchor="n")
            
            # Text nội dung
            ttk.Label(
                row, text=text, font=("Segoe UI", 9), 
                foreground=color, # Tự chỉnh màu text (trắng/xám nhạt)
                background="#2c3e50", # Hack nhẹ: màu nền trùng màu dark theme mặc định (hoặc bỏ dòng này nếu dùng bootstyle chuẩn)
                bootstyle="inverse-dark", 
                wraplength=SAFE_WIDTH - 30,
                justify="left"
            ).pack(side=LEFT, fill=X, expand=YES)

        # Render thông tin
        create_info_row("📍", APP_ADDRESS, color="#ecf0f1") # Màu trắng khói
        create_info_row("📞", APP_PHONE, color="#f1c40f")   # Màu vàng cho số điện thoại
        create_info_row("📧", APP_EMAIL, color="#3498db")   # Màu xanh dương nhạt cho email