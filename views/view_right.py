import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from helpers.ui_helpers import create_button

class RightPanelView(ttk.Frame):
    def __init__(self, parent, router):
        super().__init__(parent)
        self.pack(fill=BOTH, expand=YES)
        self.router = router

        # --- 1. TOOLBAR MỚI (Đã sửa giao diện "Từ hàng... Đến hàng...") ---
        self._setup_top_toolbar()

        # --- 2. CANVAS (Giữ nguyên) ---
        self.canvas = tk.Canvas(
            self, 
            bg="#57606f",      
            cursor="fleur",    
            highlightthickness=0 
        )
        self.canvas.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # --- BINDINGS (Giữ nguyên) ---
        self.canvas.tag_bind("draggable", "<ButtonPress-1>", router.on_drag_start)
        self.canvas.tag_bind("draggable", "<B1-Motion>", router.on_drag_motion)
        self.canvas.tag_bind("draggable", "<ButtonRelease-1>", router.on_drag_end)
        self.canvas.bind("<Shift-MouseWheel>", router.on_shift_zoom)
        self.canvas.bind("<Control-MouseWheel>", router.on_shift_zoom) 
        self.canvas.bind("<Configure>", router.on_canvas_resize)

    def _setup_top_toolbar(self):
        # Frame tổng (Toolbar)
        tb = ttk.Frame(self, padding=5, bootstyle="secondary")
        tb.pack(fill=X, side=TOP)

        # --- CHIẾN THUẬT PACK: Ưu tiên 2 đầu trước, giữa sau ---

        # 1. Nút IN NGAY (Pack RIGHT trước tiên để luôn neo chặt ở lề phải)
        create_button(
            tb, "🖨️ IN NGAY", self.router.start_print, style="danger"
        ).pack(side=RIGHT, padx=(5, 0))

        # 2. Cụm chọn Hàng (Pack RIGHT tiếp theo để nằm ngay cạnh nút In)
        fr_range = ttk.Frame(tb, bootstyle="secondary")
        fr_range.pack(side=RIGHT, padx=5)

        # Rút gọn chữ để tiết kiệm diện tích: "Từ hàng" -> "Từ"
        ttk.Label(fr_range, text="Từ hàng:", bootstyle="inverse-secondary").pack(side=LEFT, padx=(5, 2))
        
        self.var_print_from = tk.StringVar(value="1") 
        self.spin_from = ttk.Spinbox(
            fr_range, 
            from_=1, to=9999, 
            textvariable=self.var_print_from, 
            width=4, # Giảm width còn 4 (đủ cho 9999)
            bootstyle="light"
        )
        self.spin_from.pack(side=LEFT)

        # "Đến hàng" -> "Đến"
        ttk.Label(fr_range, text="Đến hàng:", bootstyle="inverse-secondary").pack(side=LEFT, padx=(5, 2))

        self.var_print_to = tk.StringVar(value="") 
        self.spin_to = ttk.Spinbox(
            fr_range, 
            from_=1, to=9999, 
            textvariable=self.var_print_to, 
            width=4, 
            bootstyle="light"
        )
        self.spin_to.pack(side=LEFT)

        # 3. Cụm cấu hình Giấy (Pack LEFT để nằm bên trái)
        fr_paper = ttk.Frame(tb, bootstyle="secondary")
        fr_paper.pack(side=LEFT)

        ttk.Label(fr_paper, text="Khổ:", bootstyle="inverse-secondary").pack(side=LEFT, padx=(0,2))
        
        self.var_paper_size = tk.StringVar(value="A4")
        self.cbb_paper_size = ttk.Combobox(
            fr_paper, 
            textvariable=self.var_paper_size, 
            values=["A4", "A5", "A6"], 
            width=3, # Giảm width combobox
            state="readonly", 
            bootstyle="warning"
        )
        self.cbb_paper_size.pack(side=LEFT)
        self.cbb_paper_size.bind("<<ComboboxSelected>>", self.router.on_paper_config_change)

        create_button(
            fr_paper, "↻", self.router.rotate_template_right, style="info-outline", width=2
        ).pack(side=LEFT, padx=2)