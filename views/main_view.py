import ttkbootstrap as ttk
from layouts.main_layout import create_3_columns
from views.view_left import LeftPanelView
from views.view_mid import MidPanelView
from views.view_right import RightPanelView
# Giữ lại helper của bạn nếu muốn dùng tính năng nâng cao
from helpers.window_helper import WindowSizeGuard 

class MainView(ttk.Frame):
    def __init__(self, master, router):
        super().__init__(master, padding=5)
        
        # 1. CẤU HÌNH KÍCH THƯỚC TỐI THIỂU CHO CỬA SỔ
        # Đây là dòng quan trọng nhất để các nút không bao giờ bị mất
        # 1024x700 là kích thước chuẩn HD, đảm bảo hiển thị đủ 3 cột
        root = self.winfo_toplevel()
        root.minsize(1100, 650) 
        
        # 2. Tạo layout
        left_fr, mid_fr, right_fr = create_3_columns(self)
        
        self.p_left = LeftPanelView(left_fr, router)
        self.p_mid = MidPanelView(mid_fr, router)
        self.p_right = RightPanelView(right_fr, router)

        # 3. Helper bảo vệ layout (nếu bạn vẫn muốn dùng)
        WindowSizeGuard(
            root=root,
            fixed_widgets=[self.p_right.tb_frame],
            flexible_widgets=[left_fr, mid_fr],    
            padding_x=60,                          
            min_height=720
        )