import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import win32print
from helpers.ui_helpers import create_button

class RightPanelView(ttk.Frame):
    def __init__(self, parent, router):
        super().__init__(parent)
        self.pack(fill=BOTH, expand=YES)
        self.router = router
        self._setup_top_toolbar()
        
        self.canvas = tk.Canvas(self, bg="#57606f", cursor="fleur", highlightthickness=0)
        self.canvas.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        self.canvas.tag_bind("draggable", "<ButtonPress-1>", router.on_drag_start)
        self.canvas.tag_bind("draggable", "<B1-Motion>", router.on_drag_motion)
        self.canvas.tag_bind("draggable", "<ButtonRelease-1>", router.on_drag_end)
        self.canvas.bind("<Shift-MouseWheel>", router.on_shift_zoom)
        self.canvas.bind("<Control-MouseWheel>", router.on_shift_zoom) 
        self.canvas.bind("<Configure>", router.on_canvas_resize)

    def _setup_top_toolbar(self):
        self.tb_frame = ttk.Frame(self, padding=5, bootstyle="secondary")
        self.tb_frame.pack(fill=X, side=TOP)

        # 1. Nút IN NGAY
        create_button(self.tb_frame, "🖨️ IN NGAY", self.router.start_print, style="danger").pack(side=RIGHT, padx=(5, 0))

        # 2. Máy in & Chế độ in (FIX LỖI QUAN TRỌNG TẠI ĐÂY)
        self.var_print_mode = tk.StringVar(value="Dữ liệu + Phôi")
        # Gán vào self.cbb_print_mode để PrintController gọi được
        self.cbb_print_mode = ttk.Combobox(self.tb_frame, textvariable=self.var_print_mode, 
                                           values=["Chỉ dữ liệu", "Dữ liệu + Phôi"], 
                                           state="readonly", width=12)
        self.cbb_print_mode.pack(side=RIGHT, padx=5)

        try: printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        except: printers = []
        
        self.cbb_printer = ttk.Combobox(self.tb_frame, values=printers, state="readonly", width=20)
        if printers: self.cbb_printer.current(0)
        self.cbb_printer.pack(side=RIGHT, padx=5)
        ttk.Label(self.tb_frame, text="Máy in:", bootstyle="inverse-secondary").pack(side=RIGHT)

        # 3. Chọn hàng in
        fr_range = ttk.Frame(self.tb_frame, bootstyle="secondary")
        fr_range.pack(side=RIGHT, padx=10)
        ttk.Label(fr_range, text="Từ:", bootstyle="inverse-secondary").pack(side=LEFT)
        self.var_print_from = tk.StringVar(value="1")
        ttk.Spinbox(fr_range, from_=1, to=9999, textvariable=self.var_print_from, width=4).pack(side=LEFT)
        ttk.Label(fr_range, text="Đến:", bootstyle="inverse-secondary").pack(side=LEFT)
        self.var_print_to = tk.StringVar(value="")
        ttk.Spinbox(fr_range, from_=1, to=9999, textvariable=self.var_print_to, width=4).pack(side=LEFT)

        # 4. Cấu hình giấy
        fr_paper = ttk.Frame(self.tb_frame, bootstyle="secondary")
        fr_paper.pack(side=LEFT)

        ttk.Label(fr_paper, text="Khổ:", bootstyle="inverse-secondary").pack(side=LEFT)
        self.var_paper_size = tk.StringVar(value="A4")
        cbb_size = ttk.Combobox(fr_paper, textvariable=self.var_paper_size, values=["A4", "A5", "A6"], width=3, state="readonly")
        cbb_size.pack(side=LEFT, padx=2)
        cbb_size.bind("<<ComboboxSelected>>", self.router.on_paper_config_change)

        self.var_orientation = tk.StringVar(value="portrait") 
        ttk.Radiobutton(fr_paper, text="Dọc", variable=self.var_orientation, value="portrait", 
                        command=self.router.on_orientation_change, bootstyle="info-toolbutton").pack(side=LEFT, padx=2)
        ttk.Radiobutton(fr_paper, text="Ngang", variable=self.var_orientation, value="landscape", 
                        command=self.router.on_orientation_change, bootstyle="warning-toolbutton").pack(side=LEFT, padx=2)

        create_button(fr_paper, "↻ Ảnh", self.router.rotate_template_right, style="secondary-outline", width=6).pack(side=LEFT, padx=5)