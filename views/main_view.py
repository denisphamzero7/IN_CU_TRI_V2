# views/main_view.py
import tkinter as tk
from layouts.main_layout import create_3_columns
from views.view_left import LeftPanelView
from views.view_mid import MidPanelView
from views.view_right import RightPanelView

class MainView(tk.Frame):
    def __init__(self, root, router):
        super().__init__(root)
        self.pack(fill="both", expand=True)
        
        left_fr, mid_fr, right_fr = create_3_columns(self)
        
        self.p_left = LeftPanelView(left_fr, router)
        self.p_mid = MidPanelView(mid_fr, router)
        self.p_right = RightPanelView(right_fr, router)