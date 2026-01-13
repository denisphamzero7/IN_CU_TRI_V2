import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config.settings import APP_HEADER, APP_ADDRESS, APP_PHONE, APP_EMAIL

# --- MÃ MÀU ---
MISA_BLUE = "#002B5E"
WHITE     = "#FFFFFF"
BLACK     = "#000000"

class HeaderView(ttk.Frame):
    def __init__(self, parent):
        # 1. CẤU HÌNH STYLE
        style = ttk.Style()
        style.configure('Header.TFrame', background=WHITE)
        
        # Tiêu đề: Font 11 Bold (To đẹp)
        style.configure('HeaderTitle.TLabel', 
                        background=WHITE, 
                        foreground=MISA_BLUE, 
                        font=("Segoe UI", 9, "bold"), 
                        anchor="center",
                        justify="center")
        
        # Nội dung: Font 9
        style.configure('InfoMisa.TLabel', background=WHITE, foreground=BLACK, font=("Segoe UI", 8))
        style.configure('InfoNormal.TLabel', background=WHITE, foreground=BLACK, font=("Segoe UI", 8))

        # 2. KHỞI TẠO FRAME
        super().__init__(parent, style='Header.TFrame', padding=5)
        self.pack(fill=X)
        
        SAFE_WIDTH = 210 # Giới hạn độ rộng dùng cho ĐỊA CHỈ
        
        # 3. TIÊU ĐỀ (ĐÃ SỬA: Bỏ wraplength để luôn là 1 hàng)
        ttk.Label(
            self, 
            text=APP_HEADER.upper(), 
            style='HeaderTitle.TLabel', 
            # wraplength=SAFE_WIDTH, <--- ĐÃ XÓA DÒNG NÀY ĐỂ KHÔNG TỰ XUỐNG DÒNG
            justify="center"
        ).pack(fill=X, pady=(0, 5))

        # 4. KHUNG THÔNG TIN
        info_frame = ttk.Frame(self, style='Header.TFrame')
        info_frame.pack(fill=X)

        def create_row(icon, text, text_style):
            row = ttk.Frame(info_frame, style='Header.TFrame')
            row.pack(fill=X, pady=1) 
            
            # Icon
            ttk.Label(
                row, 
                text=icon, 
                style='InfoNormal.TLabel', 
                width=3
            ).pack(side=LEFT, anchor="n") 
            
            # Text nội dung (Vẫn giữ xuống dòng cho địa chỉ)
            ttk.Label(
                row, 
                text=text, 
                style=text_style,
                wraplength=SAFE_WIDTH, # Địa chỉ vẫn cần cái này để không bị mất chữ
                justify="left",        
                anchor="w"
            ).pack(side=LEFT, fill=X, expand=YES)

        # 5. RENDER DỮ LIỆU
        create_row("📍", APP_ADDRESS, 'InfoMisa.TLabel') 
        create_row("📞", APP_PHONE, 'InfoNormal.TLabel')
        create_row("📧", APP_EMAIL, 'InfoNormal.TLabel')