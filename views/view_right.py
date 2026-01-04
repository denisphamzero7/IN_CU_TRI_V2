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

        self.canvas = tk.Canvas(
            self, 
            bg="#57606f",      
            cursor="fleur",    
            highlightthickness=0 
        )
        self.canvas.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # Binding các sự kiện Canvas
        self.canvas.tag_bind("draggable", "<ButtonPress-1>", router.on_drag_start)
        self.canvas.tag_bind("draggable", "<B1-Motion>", router.on_drag_motion)
        self.canvas.tag_bind("draggable", "<ButtonRelease-1>", router.on_drag_end)
        self.canvas.bind("<Shift-MouseWheel>", router.on_shift_zoom)
        self.canvas.bind("<Control-MouseWheel>", router.on_shift_zoom) 
        self.canvas.bind("<Configure>", router.on_canvas_resize)

    def _setup_top_toolbar(self):
        tb = ttk.Frame(self, padding=5, bootstyle="secondary")
        tb.pack(fill=X, side=TOP)

        # ---------------------------------------------------------
        # 1. Nút IN NGAY (Ngoài cùng bên phải)
        create_button(
            tb, "🖨️ IN NGAY", self.router.start_print, style="danger"
        ).pack(side=RIGHT, padx=(5, 0))

        # ---------------------------------------------------------
        # 2. Combobox CHỌN CHẾ ĐỘ IN (Chỉ dữ liệu / Kèm phôi)
        self.var_print_mode = tk.StringVar(value="Chỉ dữ liệu")  
        self.cbb_print_mode = ttk.Combobox(
            tb, 
            textvariable=self.var_print_mode,
            values=["Chỉ dữ liệu", "Dữ liệu + Phôi"],
            state="readonly",
            width=15,
            bootstyle="success"
        )
        self.cbb_print_mode.pack(side=RIGHT, padx=5)

        # ---------------------------------------------------------
        # 3. CHỌN MÁY IN
        try:
            printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
            default_printer = win32print.GetDefaultPrinter()
        except:
            printers = []
            default_printer = ""

        self.cbb_printer = ttk.Combobox(
            tb, values=printers, state="readonly", width=25, bootstyle="info"
        )
        self.cbb_printer.pack(side=RIGHT, padx=5)
        
        if default_printer in printers:
            self.cbb_printer.current(printers.index(default_printer))
        elif printers:
            self.cbb_printer.current(0)
        
        ttk.Label(tb, text="Máy in:", bootstyle="inverse-secondary").pack(side=RIGHT, padx=(5, 2))

        # ---------------------------------------------------------
        # 4. CỤM TỪ HÀNG - ĐẾN HÀNG
        fr_range = ttk.Frame(tb, bootstyle="secondary")
        fr_range.pack(side=RIGHT, padx=10)

        ttk.Label(fr_range, text="Từ:", bootstyle="inverse-secondary").pack(side=LEFT, padx=(5, 2))
        
        self.var_print_from = tk.StringVar(value="1") 
        self.spin_from = ttk.Spinbox(
            fr_range, from_=1, to=9999, textvariable=self.var_print_from, 
            width=4, bootstyle="light"
        )
        self.spin_from.pack(side=LEFT)

        ttk.Label(fr_range, text="Đến:", bootstyle="inverse-secondary").pack(side=LEFT, padx=(5, 2))

        self.var_print_to = tk.StringVar(value="") 
        self.spin_to = ttk.Spinbox(
            fr_range, from_=1, to=9999, textvariable=self.var_print_to, 
            width=4, bootstyle="light"
        )
        self.spin_to.pack(side=LEFT)

        # ---------------------------------------------------------
        # 5. KHỔ GIẤY & XOAY (Bên trái)
        fr_paper = ttk.Frame(tb, bootstyle="secondary")
        fr_paper.pack(side=LEFT)

        ttk.Label(fr_paper, text="Khổ:", bootstyle="inverse-secondary").pack(side=LEFT, padx=(0,2))
        
        self.var_paper_size = tk.StringVar(value="A4")
        self.cbb_paper_size = ttk.Combobox(
            fr_paper, 
            textvariable=self.var_paper_size, 
            values=["A4", "A5", "A6"], 
            width=3, 
            state="readonly", 
            bootstyle="warning"
        )
        self.cbb_paper_size.pack(side=LEFT)
        self.cbb_paper_size.bind("<<ComboboxSelected>>", self.router.on_paper_config_change)

        # Nút Xoay Nội Dung (Template)
        create_button(
            fr_paper, "↻", self.router.rotate_template_right, 
            style="info-outline", width=4
        ).pack(side=LEFT, padx=2)
        
        # Nút Xoay Giấy (Paper Orientation) - Chỉ hiện Icon ▮
        self.btn_rotate_paper = create_button(
            fr_paper, 
            "▮",  # Icon mặc định (Dọc)
            self.router.toggle_paper_orientation, 
            style="info-outline", 
            width=4 
        )
        self.btn_rotate_paper.pack(side=LEFT, padx=2)