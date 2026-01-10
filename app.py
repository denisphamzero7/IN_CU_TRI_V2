# app.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from helpers.ui_helpers import apply_window_icon 
from config.settings import APP_TITLE
from views.main_view import MainView
from controllers.router import AppRouter

# [THÊM ĐOẠN NÀY] Import ctypes để xử lý DPI
import ctypes
try:
    # Báo cho Windows biết app này hỗ trợ High DPI -> Giao diện sắc nét, đúng kích thước thật
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

class App(ttk.Window):
    def __init__(self):
        super().__init__()
        
        self.title(APP_TITLE)
        
        # Tự động phóng to toàn màn hình
        self.state("zoomed") 
        
        # [QUAN TRỌNG] Đặt kích thước tối thiểu an toàn
        # 1100x600 đảm bảo lọt lòng màn hình 1366x768 (trừ thanh taskbar)
        self.minsize(1100, 600)

        # --- GỌI HÀM SET ICON Ở ĐÂY ---
        apply_window_icon(self) 
        # -----------------------------

        self.router = AppRouter()
        self.main_view = MainView(self, self.router)
        self.main_view.pack(fill=BOTH, expand=YES)
        self.router.set_view(self.main_view)

    def run(self):
        self.mainloop()