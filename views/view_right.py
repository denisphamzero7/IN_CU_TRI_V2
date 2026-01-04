import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from helpers.ui_helpers import create_button

class RightPanelView(ttk.Frame):
    def __init__(self, parent, router):
        super().__init__(parent)
        self.pack(fill=BOTH, expand=YES)
        self.router = router

        # --- 1. TOOLBAR MỚI (CHỨA NÚT IN & CẤU HÌNH GIẤY) ---
        # Phần này được chuyển từ cột Giữa sang
        self._setup_top_toolbar()

        # --- 2. CANVAS (GIỮ NGUYÊN) ---
        self.canvas = tk.Canvas(
            self, 
            bg="#57606f",      
            cursor="fleur",    
            highlightthickness=0 
        )
        self.canvas.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # --- BINDINGS (GIỮ NGUYÊN) ---
        self.canvas.tag_bind("draggable", "<ButtonPress-1>", router.on_drag_start)
        self.canvas.tag_bind("draggable", "<B1-Motion>", router.on_drag_motion)
        self.canvas.tag_bind("draggable", "<ButtonRelease-1>", router.on_drag_end)
        self.canvas.bind("<Shift-MouseWheel>", router.on_shift_zoom)
        self.canvas.bind("<Control-MouseWheel>", router.on_shift_zoom) 
        self.canvas.bind("<Configure>", router.on_canvas_resize)

    def _setup_top_toolbar(self):
        # Tạo frame chứa công cụ, nằm trên cùng của cột Phải
        tb = ttk.Frame(self, padding=5, bootstyle="secondary")
        tb.pack(fill=X, side=TOP)

        # --- Nhóm 1: Cấu hình giấy (Bên trái) ---
        fr_left = ttk.Frame(tb, bootstyle="secondary")
        fr_left.pack(side=LEFT)

        ttk.Label(fr_left, text="Khổ:", bootstyle="inverse-secondary").pack(side=LEFT, padx=(0,5))
        
        self.var_paper_size = tk.StringVar(value="A4")
        self.cbb_paper_size = ttk.Combobox(
            fr_left, 
            textvariable=self.var_paper_size,
            values=["A4", "A5", "A6"], 
            width=5, 
            state="readonly",
            bootstyle="warning"
        )
        self.cbb_paper_size.pack(side=LEFT)
        self.cbb_paper_size.bind("<<ComboboxSelected>>", self.router.on_paper_config_change)

        create_button(
            fr_left, "↻", self.router.rotate_template_right, style="info-outline", width=3
        ).pack(side=LEFT, padx=5)

        # --- Nhóm 2: Nút IN (Bên phải - Nổi bật) ---
        create_button(
            tb, "🖨️ IN NGAY", self.router.start_print, style="danger"
        ).pack(side=RIGHT)