# views/main_view.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import * # Import các hằng số như BOTH, YES
from layouts.main_layout import create_3_columns
from views.view_left import LeftPanelView
from views.view_mid import MidPanelView
from views.view_right import RightPanelView
from views.custom_dialog import CustomDialog
# 1. Kế thừa ttk.Frame để ăn theo Theme (Dark/Light)
class MainView(ttk.Frame):
    def __init__(self, master, router):
        # Có thể thêm padding cho thoáng: padding=10
        super().__init__(master, padding=5) 
        
        # 2. Đã bỏ dòng self.pack() vì app.py đã làm việc này rồi
        
        # Gọi hàm tạo layout
        # Lưu ý: Hàm create_3_columns cũng cần trả về các khung là ttk.Frame nhé!
        left_fr, mid_fr, right_fr = create_3_columns(self)
        
        self.p_left = LeftPanelView(left_fr, router)
        self.p_mid = MidPanelView(mid_fr, router)
        self.p_right = RightPanelView(right_fr, router)
        