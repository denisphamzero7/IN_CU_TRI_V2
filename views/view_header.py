import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config.settings import APP_HEADER, APP_ADDRESS, APP_PHONE, APP_EMAIL

# --- MÃ MÀU ---
MISA_BLUE = "#002B5E"  # Xanh MISA Đậm
WHITE     = "#FFFFFF"  # Trắng
BLACK     = "#000000"  # Đen

class HeaderView(ttk.Frame):
    def __init__(self, parent):
        # 1. CẤU HÌNH STYLE (CONFIG NHƯ LEFT PANEL)
        style = ttk.Style()
        
        # A. Style cho Frame nền Trắng (Header.TFrame)
        style.configure('Header.TFrame', background=WHITE)
        
        # B. Style cho Tiêu đề (HeaderTitle.TLabel): Nền trắng, Chữ Xanh MISA, Đậm
        style.configure('HeaderTitle.TLabel', 
                        background=WHITE, 
                        foreground=MISA_BLUE, 
                        font=("Segoe UI", 11, "bold"),
                        anchor="center",
                        justify="center")
        
        # C. Style cho Nội dung MISA (InfoMisa.TLabel): Nền trắng, Chữ Xanh MISA (Dùng cho địa chỉ)
        style.configure('InfoMisa.TLabel', 
                        background=WHITE, 
                        foreground=BLACK, 
                        font=("Segoe UI", 9))

        # D. Style cho Nội dung Thường (InfoNormal.TLabel): Nền trắng, Chữ Đen (Dùng cho SĐT, Email)
        style.configure('InfoNormal.TLabel', 
                        background=WHITE, 
                        foreground=BLACK, 
                        font=("Segoe UI", 9))

        # ---------------------------------------------------------

        # 2. KHỞI TẠO HEADER VỚI STYLE TRẮNG
        super().__init__(parent, style='Header.TFrame', padding=5)
        self.pack(fill=X)
        
        SAFE_WIDTH = 300 
        
        # 3. TIÊU ĐỀ (Dùng style HeaderTitle)
        ttk.Label(
            self, 
            text=APP_HEADER.upper(), 
            style='HeaderTitle.TLabel', # <--- Áp dụng style tiêu đề
            wraplength=SAFE_WIDTH
        ).pack(fill=X, pady=(0, 2))

        # 4. KHUNG THÔNG TIN (Dùng style nền trắng)
        info_frame = ttk.Frame(self, style='Header.TFrame')
        info_frame.pack(fill=X)

        def create_row(icon, text, text_style):
            # Row Frame (Nền trắng)
            row = ttk.Frame(info_frame, style='Header.TFrame')
            row.pack(fill=X, pady=0) # Sát nhau
            
            # Icon (Luôn dùng màu đen -> InfoNormal)
            ttk.Label(
                row, 
                text=icon, 
                style='InfoNormal.TLabel', 
                width=3
            ).pack(side=LEFT, anchor="n", pady=1)
            
            # Text nội dung (Style tùy biến: Xanh hoặc Đen)
            ttk.Label(
                row, 
                text=text, 
                style=text_style, # <--- Nhận style từ tham số
                wraplength=SAFE_WIDTH - 30
            ).pack(side=LEFT, fill=X, expand=YES, pady=1)

        # 5. RENDER DỮ LIỆU
        # - Địa chỉ: Màu Xanh MISA -> Dùng 'InfoMisa.TLabel'
        create_row("📍", APP_ADDRESS, 'InfoMisa.TLabel') 
        
        # - SĐT: Màu Đen -> Dùng 'InfoNormal.TLabel'
        create_row("📞", APP_PHONE, 'InfoNormal.TLabel')
        
        # - Email: Màu Đen -> Dùng 'InfoNormal.TLabel'
        create_row("📧", APP_EMAIL, 'InfoNormal.TLabel')