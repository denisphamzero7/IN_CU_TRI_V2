# FILE: views/main_view.py
import ttkbootstrap as ttk
from layouts.main_layout import create_3_columns
from views.view_left import LeftPanelView
from views.view_mid import MidPanelView
from views.view_right import RightPanelView
# Import helper mới tạo
from helpers.window_helper import WindowSizeGuard 

class MainView(ttk.Frame):
    def __init__(self, master, router):
        super().__init__(master, padding=5)
        
        # Tạo layout 3 cột
        left_fr, mid_fr, right_fr = create_3_columns(self)
        
        # Tạo các Panel
        self.p_left = LeftPanelView(left_fr, router)
        self.p_mid = MidPanelView(mid_fr, router)
        self.p_right = RightPanelView(right_fr, router)

        # =========================================================
        # TỰ ĐỘNG KHÓA KÍCH THƯỚC MÀN HÌNH (Chống mất nút)
        # =========================================================
        # Helper sẽ đợi giao diện vẽ xong rồi tự đo chiều rộng thanh Toolbar
        WindowSizeGuard(
            root=self.winfo_toplevel(),
            fixed_widgets=[self.p_right.tb_frame], # Thanh công cụ bên phải
            flexible_widgets=[left_fr, mid_fr],    # Cột trái và giữa
            padding_x=60,                          # Khoảng hở an toàn
            min_height=720
        )