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
        
        # Thêm takefocus=1 để Canvas có thể nhận phím bấm
        self.canvas = tk.Canvas(self, bg="#57606f", cursor="fleur", highlightthickness=1, takefocus=1)
        self.canvas.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # --- BINDING CHUỘT (Giữ nguyên) ---
        self.canvas.tag_bind("draggable", "<ButtonPress-1>", self._on_canvas_click) # Sửa nhẹ chỗ này để gộp logic Focus
        self.canvas.tag_bind("draggable", "<B1-Motion>", router.on_drag_motion)
        self.canvas.tag_bind("draggable", "<ButtonRelease-1>", router.on_drag_end)
        self.canvas.bind("<Shift-MouseWheel>", router.on_shift_zoom)
        self.canvas.bind("<Control-MouseWheel>", router.on_shift_zoom) 
        self.canvas.bind("<Configure>", router.on_canvas_resize)

        # --- BINDING BÀN PHÍM (MỚI) ---
        # Khi click vào canvas (khoảng trắng), cũng cho nó focus để nhận phím
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set())
        
        self.canvas.bind("<Up>", router.on_arrow_key)
        self.canvas.bind("<Down>", router.on_arrow_key)
        self.canvas.bind("<Left>", router.on_arrow_key)
        self.canvas.bind("<Right>", router.on_arrow_key)
        
        # Hỗ trợ Shift + Mũi tên (Di chuyển nhanh)
        self.canvas.bind("<Shift-Up>", router.on_arrow_key)
        self.canvas.bind("<Shift-Down>", router.on_arrow_key)
        self.canvas.bind("<Shift-Left>", router.on_arrow_key)
        self.canvas.bind("<Shift-Right>", router.on_arrow_key)

    def _on_canvas_click(self, event):
        """Vừa xử lý Drag start, vừa Focus vào canvas để nhận phím"""
        self.canvas.focus_set() # Quan trọng: Phải Focus mới bấm phím được
        self.router.on_drag_start(event)

    def _setup_top_toolbar(self):
        # ... (Giữ nguyên code cũ của hàm này) ...
        self.tb_frame = ttk.Frame(self, padding=5, bootstyle="secondary")
        self.tb_frame.pack(fill=X, side=TOP)

        create_button(self.tb_frame, "🖨️ IN NGAY", self.router.start_print, style="danger").pack(side=RIGHT, padx=(5, 0))

        self.var_print_mode = tk.StringVar(value="Chỉ dữ liệu")
        self.cbb_print_mode = ttk.Combobox(self.tb_frame, textvariable=self.var_print_mode, 
                                           values=["Chỉ dữ liệu", "Dữ liệu + Phôi"], 
                                           state="readonly", width=17, bootstyle="primary")
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

        ttk.Label(fr_paper, text="Khổ:", bootstyle="inverse-secondary").pack(side=LEFT)
        self.var_paper_size = tk.StringVar(value="A4")
        cbb_size = ttk.Combobox(fr_paper, textvariable=self.var_paper_size, values=["A4", "A5", "A6","TheCuTri"], 
                                width=3, state="readonly", bootstyle="primary")
        cbb_size.pack(side=LEFT, padx=2)
        cbb_size.bind("<<ComboboxSelected>>", self.router.on_paper_config_change)

        self.var_orientation = tk.StringVar(value="Ngang") 
        self.cbb_orientation = ttk.Combobox(fr_paper, textvariable=self.var_orientation, 
                                            values=["Dọc", "Ngang"], 
                                            state="readonly", width=6, bootstyle="primary")
        self.cbb_orientation.pack(side=LEFT, padx=5)
        self.cbb_orientation.bind("<<ComboboxSelected>>", self.router.on_orientation_change)

        create_button(fr_paper, "↻ Ảnh", self.router.rotate_template_right, style="primary-outline", width=6).pack(side=LEFT, padx=5)