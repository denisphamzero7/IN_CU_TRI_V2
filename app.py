# app.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
# Thêm dòng import này
from helpers.ui_helpers import apply_window_icon 
from config.settings import APP_TITLE
from views.main_view import MainView
from controllers.router import AppRouter

class App(ttk.Window):
    def __init__(self):
        super().__init__(themename="superhero")
        
        self.title(APP_TITLE)
        self.geometry("1600x900")

        # --- GỌI HÀM SET ICON Ở ĐÂY ---
        apply_window_icon(self) 
        # -----------------------------

        self.router = AppRouter()
        self.main_view = MainView(self, self.router)
        self.main_view.pack(fill=BOTH, expand=YES)
        self.router.set_view(self.main_view)

    def run(self):
        self.mainloop()