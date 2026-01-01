# app.py
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config.settings import DEFAULT_THEME
from views.main_view import MainView
from controllers.router import AppRouter

class App(ttk.Window):
    def __init__(self):
        super().__init__(themename=DEFAULT_THEME)
        self.title("HỆ THỐNG IN THẺ CỬ TRI ")
        self.geometry("1600x900")
        
        # 1. Khởi tạo Router (Bộ não)
        self.router = AppRouter()
        
        # 2. Khởi tạo View (Giao diện), truyền Router vào
        self.main_view = MainView(self, self.router)
        # 3. QUAN TRỌNG: Phải đặt View lên cửa sổ
        # Nếu thiếu dòng này, giao diện sẽ trống trơn
        self.main_view.pack(fill=BOTH, expand=YES)
        # 3. Kết nối ngược View vào Router
        self.router.set_view(self.main_view)

    def run(self):
        self.mainloop()