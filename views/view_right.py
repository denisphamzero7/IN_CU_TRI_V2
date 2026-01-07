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
        
        # takefocus=1 để Canvas có thể nhận phím bấm
        self.canvas = tk.Canvas(self, bg="#57606f", cursor="fleur", highlightthickness=1, takefocus=1)
        self.canvas.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # --- BINDING CHUỘT ---
        self.canvas.tag_bind("draggable", "<ButtonPress-1>", self._on_canvas_click)
        self.canvas.tag_bind("draggable", "<B1-Motion>", router.on_drag_motion)
        self.canvas.tag_bind("draggable", "<ButtonRelease-1>", router.on_drag_end)
        self.canvas.bind("<Shift-MouseWheel>", router.on_shift_zoom)
        self.canvas.bind("<Control-MouseWheel>", router.on_shift_zoom) 
        self.canvas.bind("<Configure>", router.on_canvas_resize)

        # --- BINDING BÀN PHÍM ---
        # 1. Click vào canvas để Focus nhận phím
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set())
        
        # 2. Bắt sự kiện NHẤN và THẢ phím (Cơ chế game loop)
        self.canvas.bind("<KeyPress>", router.on_key_press)
        self.canvas.bind("<KeyRelease>", router.on_key_release)

    def _on_canvas_click(self, event):
        """Vừa xử lý Drag start, vừa Focus vào canvas để nhận phím"""
        self.canvas.focus_set() 
        self.router.on_drag_start(event)

    def _setup_top_toolbar(self):
        self.tb_frame = ttk.Frame(self, padding=5, bootstyle="secondary")
        self.tb_frame.pack(fill=X, side=TOP)

        create_button(self.tb_frame, "🖨️ IN NGAY", self.router.start_print, style="danger").pack(side=RIGHT, padx=(5, 0))

        # --- [SỬA] CHẾ ĐỘ IN: Mặc định "Chỉ dữ liệu" + Disabled ---
        self.var_print_mode = tk.StringVar(value="Chỉ dữ liệu")
        self.cbb_print_mode = ttk.Combobox(self.tb_frame, textvariable=self.var_print_mode, 
                                           values=["Chỉ dữ liệu", "Dữ liệu + Phôi"], 
                                           state="disabled", width=17, bootstyle="primary") # Đã khóa
        self.cbb_print_mode.pack(side=RIGHT, padx=5)

        try: printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        except: printers = []
        
        self.cbb_printer = ttk.Combobox(self.tb_frame, values=printers, state="readonly", width=20, bootstyle="primary")
        if printers: self.cbb_printer.current(0)
        self.cbb_printer.pack(side=RIGHT, padx=5)
        ttk.Label(self.tb_frame, text="Máy in:", bootstyle="inverse-secondary").pack(side=RIGHT)

        fr_range = ttk.Frame(self.tb_frame, bootstyle="secondary")
        fr_range.pack(side=RIGHT, padx=10)
        ttk.Label(fr_range, text="Từ:", bootstyle="inverse-secondary").pack(side=LEFT)
        self.var_print_from = tk.StringVar(value="1")
        ttk.Spinbox(fr_range, from_=1, to=9999, textvariable=self.var_print_from, width=4, bootstyle="primary").pack(side=LEFT)
        ttk.Label(fr_range, text="Đến:", bootstyle="inverse-secondary").pack(side=LEFT)
        self.var_print_to = tk.StringVar(value="")
        ttk.Spinbox(fr_range, from_=1, to=9999, textvariable=self.var_print_to, width=4, bootstyle="primary").pack(side=LEFT)

        fr_paper = ttk.Frame(self.tb_frame, bootstyle="secondary")
        fr_paper.pack(side=LEFT)

        # --- [SỬA] KHỔ GIẤY: Mặc định "A6" + Disabled ---
        ttk.Label(fr_paper, text="Khổ:", bootstyle="inverse-secondary").pack(side=LEFT)
        self.var_paper_size = tk.StringVar(value="A6") # Mặc định A6
        cbb_size = ttk.Combobox(fr_paper, textvariable=self.var_paper_size, values=["A4", "A5", "A6","TheCuTri"], 
                                width=5, state="disabled", bootstyle="primary") # Đã khóa
        cbb_size.pack(side=LEFT, padx=2)
        cbb_size.bind("<<ComboboxSelected>>", self.router.on_paper_config_change)

        # --- [SỬA] HƯỚNG GIẤY: Mặc định "Ngang" + Disabled ---
        self.var_orientation = tk.StringVar(value="Ngang") # Mặc định Ngang
        self.cbb_orientation = ttk.Combobox(fr_paper, textvariable=self.var_orientation, 
                                            values=["Dọc", "Ngang"], 
                                            state="disabled", width=6, bootstyle="primary") # Đã khóa
        self.cbb_orientation.pack(side=LEFT, padx=5)
        self.cbb_orientation.bind("<<ComboboxSelected>>", self.router.on_orientation_change)

        self.fr_rotate_border = ttk.Frame(fr_paper, bootstyle="primary")
        self.fr_rotate_border.pack(side=LEFT, padx=5)

        # 2. Nút bên trong màu Xám (secondary) -> Chữ sẽ màu trắng
        self.btn_rotate = create_button(
            self.fr_rotate_border, 
            "↻ Ảnh", 
            self.router.rotate_template_right, 
            width=6,
            style="secondary",   # <--- [SỬA LẠI] Dùng 'style', KHÔNG dùng 'bootstyle'
            # state="disabled"     # <--- Giữ nguyên dòng này để disable
        )
        
        # Pack với padx=1, pady=1 -> Lộ ra 1px viền màu xanh
        self.btn_rotate.pack(padx=1, pady=1)