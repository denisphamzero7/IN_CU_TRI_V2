import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import win32print
from helpers.ui_helpers import create_button
from config.settings import APP_BG_COLOR
from helpers.msg_helper import MsgHelper

class RightPanelView(ttk.Frame):
    def __init__(self, parent, router):
        # --- CẤU HÌNH STYLE ---
        style = ttk.Style()
        style.configure('Misa.TFrame', background=APP_BG_COLOR)
        style.configure('MisaToolbar.TLabel', background=APP_BG_COLOR, foreground="#333333")
        
        # Style cho Checkbox và Toolbar
        style.configure('Toolbar.TCheckbutton', background=APP_BG_COLOR, foreground="#333333", font=("Segoe UI", 9, "bold"))
        style.map('Toolbar.TCheckbutton', background=[('active', APP_BG_COLOR)], foreground=[('active', 'black')])
        style.configure('Toolbar.TButton', font=("Segoe UI", 9))

        super().__init__(parent, style='Misa.TFrame')
        self.pack(fill=BOTH, expand=YES)
        self.router = router
        
        # --- 2. TOOLBAR ---
        self._setup_top_toolbar()
        style.configure('ManualCenter.Danger.TButton', 
                        font=("Segoe UI Emoji", 13), # Đặt font emoji chuẩn
                        padding=(100, 5, 5, 5)        # (Trái=15, Trên=5, Phải=5, Dưới=5)
                        )
        # --- 3. CANVAS ---
        self.canvas = tk.Canvas(self, bg="#57606f", cursor="fleur", highlightthickness=1, takefocus=1)
        self.canvas.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # Binding
        self.canvas.tag_bind("draggable", "<ButtonPress-1>", self._on_canvas_click)
        self.canvas.tag_bind("draggable", "<B1-Motion>", router.on_drag_motion)
        self.canvas.tag_bind("draggable", "<ButtonRelease-1>", router.on_drag_end)
        self.canvas.bind("<Shift-MouseWheel>", router.on_shift_zoom)
        self.canvas.bind("<Control-MouseWheel>", router.on_shift_zoom) 
        self.canvas.bind("<Configure>", router.on_canvas_resize)
        self.canvas.bind("<Button-1>", lambda e: self.canvas.focus_set())
        self.canvas.bind("<KeyPress>", router.on_key_press)
        self.canvas.bind("<KeyRelease>", router.on_key_release)

    def _on_canvas_click(self, event):
        self.canvas.focus_set() 
        self.router.on_drag_start(event)

    def _require_license(self, func, *args):
        """Kiểm tra bản quyền"""
        if self.router.ctrl_license.is_licensed:
            return func(*args)
        else:
            MsgHelper.show_warning("Tính năng này chỉ dành cho bản quyền Pro!")

    def _setup_top_toolbar(self):
        # Frame tổng chứa cả 2 hàng
        self.tb_frame = ttk.Frame(self, padding=5, style='Misa.TFrame')
        self.tb_frame.pack(fill=X, side=TOP)

        # ============================================================
        # [HÀNG 1] CODE CŨ: CẤU HÌNH GIẤY & IN ẤN
        # ============================================================
        row1 = ttk.Frame(self.tb_frame, style='Misa.TFrame')
        row1.pack(fill=X, side=TOP, pady=(0, 5)) # Cách hàng dưới 5px

        btn_print = ttk.Button(
            row1,
            # [MẸO QUAN TRỌNG]: Thêm khoảng trắng vào text để đẩy icon
            # - Muốn icon sang phải -> Thêm dấu cách vào bên TRÁI ("  🖨️")
            # - Muốn icon sang trái -> Thêm dấu cách vào bên PHẢI ("🖨️  ")
            # - Thử thêm 1-2 dấu cách cho đến khi thấy nó nằm giữa
            text=" 🖨️ ", 
             width=3,
            command=self.router.start_print,
            bootstyle="danger", 
            
            # width=4  <-- XÓA HOẶC COMMENT DÒNG NÀY ĐI
            # Để nút tự co giãn theo lượng khoảng trắng bạn thêm vào
        )
        btn_print.pack(side=RIGHT, padx=(5, 0))
        # CHẾ ĐỘ IN
        self.var_print_mode = tk.StringVar(value="Chỉ dữ liệu")
        self.cbb_print_mode = ttk.Combobox(row1, textvariable=self.var_print_mode, 
                                           values=["Chỉ dữ liệu", "Dữ liệu + Phôi"], 
                                           state="disabled", width=17, bootstyle="primary")
        self.cbb_print_mode.pack(side=RIGHT, padx=5)

        try: printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        except: printers = []
        
        
        self.cbb_printer = ttk.Combobox(row1, values=printers, state="readonly", width=20, bootstyle="primary")
        if printers: self.cbb_printer.current(0)
        self.cbb_printer.pack(side=RIGHT, padx=5)
        
        ttk.Label(row1, text="Máy in:", style='MisaToolbar.TLabel').pack(side=RIGHT)

        fr_range = ttk.Frame(row1, style='Misa.TFrame')
        fr_range.pack(side=RIGHT, padx=10)
        ttk.Label(fr_range, text="Từ:", style='MisaToolbar.TLabel').pack(side=LEFT)
        self.var_print_from = tk.StringVar(value="1")
        self.entry_from = ttk.Spinbox(fr_range, from_=1, to=9999, textvariable=self.var_print_from, width=4, bootstyle="primary")
        self.entry_from.pack(side=LEFT)
        
        ttk.Label(fr_range, text="Đến:", style='MisaToolbar.TLabel').pack(side=LEFT)
        self.var_print_to = tk.StringVar(value="")
        self.entry_to = ttk.Spinbox(fr_range, from_=1, to=9999, textvariable=self.var_print_to, width=4, bootstyle="primary")
        self.entry_to.pack(side=LEFT)

        fr_paper = ttk.Frame(row1, style='Misa.TFrame')
        fr_paper.pack(side=LEFT)

        # KHỔ GIẤY
        ttk.Label(fr_paper, text="Khổ:", style='MisaToolbar.TLabel').pack(side=LEFT)
        self.var_paper_size = tk.StringVar(value="A6") 
        cbb_size = ttk.Combobox(fr_paper, textvariable=self.var_paper_size, values=["A4", "A5", "A6"], 
                                width=5, state="disabled", bootstyle="primary") 
        cbb_size.pack(side=LEFT, padx=2)
        cbb_size.bind("<<ComboboxSelected>>", self.router.on_paper_config_change)

        # HƯỚNG GIẤY
        self.var_orientation = tk.StringVar(value="Ngang")
        self.cbb_orientation = ttk.Combobox(fr_paper, textvariable=self.var_orientation, 
                                            values=["Dọc", "Ngang"], 
                                            state="disabled", width=6, bootstyle="primary") 
        self.cbb_orientation.pack(side=LEFT, padx=5)
        self.cbb_orientation.bind("<<ComboboxSelected>>", self.router.on_orientation_change)

        self.fr_rotate_border = ttk.Frame(fr_paper, bootstyle="primary")
        self.fr_rotate_border.pack(side=LEFT, padx=5)

        self.btn_rotate = create_button(
            self.fr_rotate_border, 
            "↻ Ảnh", 
            self.router.rotate_template_right, 
            width=6,
            style="secondary",  
            state="disabled"    
        )
        self.btn_rotate.pack(padx=1, pady=1)

        # ============================================================
        # [HÀNG 2] CODE MỚI: TÙY CHỈNH STYLE
        # ============================================================
        # [SỬA ĐỔI] Dùng ttk.Frame thay vì Labelframe để bỏ viền và chữ tiêu đề
        # Lúc này 2 hàng sẽ nhìn "đều nhau"
        self.fr_style_toolbar = ttk.Frame(self.tb_frame, style='Misa.TFrame')
        self.fr_style_toolbar.pack(fill=X, side=TOP, pady=(5, 0))

        # --- Container thuộc tính TEXT ---
        self.fr_text_props = ttk.Frame(self.fr_style_toolbar, style='Misa.TFrame')
        self.fr_text_props.pack(side=LEFT, fill=X, expand=YES)

        # Font
        ttk.Label(self.fr_text_props, text="Font:", style='MisaToolbar.TLabel').pack(side=LEFT, padx=(0,2))
        self.combo_font = ttk.Combobox(self.fr_text_props, values=["Arial", "Times New Roman", "Calibri", "Segoe UI", "Tahoma"], width=15, state="readonly")
        self.combo_font.pack(side=LEFT, padx=(0, 10))
        self.combo_font.bind("<<ComboboxSelected>>", lambda e: self._require_license(self.router.on_prop_change, e))

        # Size
        ttk.Label(self.fr_text_props, text="Size:", style='MisaToolbar.TLabel').pack(side=LEFT, padx=(0,2))
        self.spin_size = ttk.Spinbox(self.fr_text_props, from_=5, to=300, width=4, command=lambda: self._require_license(self.router.on_prop_change))
        self.spin_size.pack(side=LEFT, padx=(0, 10))
        self.spin_size.bind("<Return>", lambda e: self._require_license(self.router.on_prop_change, e))

        # Bold / Upper
        self.chk_bold_var = tk.BooleanVar()
        self.chk_upper_var = tk.BooleanVar()
        ttk.Checkbutton(self.fr_text_props, text="B", variable=self.chk_bold_var, style="Toolbar.TCheckbutton", 
                        command=lambda: self._require_license(self.router.on_prop_change)).pack(side=LEFT, padx=(0, 10))
        ttk.Checkbutton(self.fr_text_props, text="AA", variable=self.chk_upper_var, style="Toolbar.TCheckbutton", 
                        command=lambda: self._require_license(self.router.on_prop_change)).pack(side=LEFT, padx=(0, 10))

        # Color
        ttk.Label(self.fr_text_props, text="Màu:", style='MisaToolbar.TLabel').pack(side=LEFT, padx=(0,2))
        self.combo_color = ttk.Combobox(self.fr_text_props, values=["Black", "Red", "Blue"], width=10, state="readonly")
        self.combo_color.pack(side=LEFT)
        self.combo_color.bind("<<ComboboxSelected>>", lambda e: self._require_license(self.router.on_prop_change, e))

        # --- Container thuộc tính IMAGE ---
        self.fr_img_props = ttk.Frame(self.fr_style_toolbar, style='Misa.TFrame')
        
        ttk.Label(self.fr_img_props, text="Kích thước:", style='MisaToolbar.TLabel').pack(side=LEFT)
        ttk.Label(self.fr_img_props, text="W:", style='MisaToolbar.TLabel').pack(side=LEFT, padx=(5,2))
        self.spin_img_w = ttk.Spinbox(self.fr_img_props, from_=1, to=1000, width=5, 
                                      command=lambda: self._require_license(self.router.on_prop_change))
        self.spin_img_w.pack(side=LEFT)
        self.spin_img_w.bind("<Return>", lambda e: self._require_license(self.router.on_prop_change, e))

        ttk.Label(self.fr_img_props, text="H:", style='MisaToolbar.TLabel').pack(side=LEFT, padx=(10,2))
        self.spin_img_h = ttk.Spinbox(self.fr_img_props, from_=1, to=1000, width=5, 
                                      command=lambda: self._require_license(self.router.on_prop_change))
        self.spin_img_h.pack(side=LEFT)
        self.spin_img_h.bind("<Return>", lambda e: self._require_license(self.router.on_prop_change, e))

        ttk.Button(self.fr_img_props, text="📂 Chọn file chữ ký khác...", 
                   command=lambda: self._require_license(self.router.pick_manual_signature), 
                   bootstyle="warning-outline", style="Toolbar.TButton").pack(side=LEFT, padx=(20, 0))

        # Nút Reset
        ttk.Button(self.fr_style_toolbar, text="↺ Mặc định", 
                   command=lambda: self._require_license(self.router.reset_current_custom), 
                   bootstyle="link").pack(side=RIGHT)

        # Label hiển thị đang chọn
        self.lbl_current_field = ttk.Label(self.fr_style_toolbar, text="(Chưa chọn)", font=("Segoe UI", 9, "bold"), foreground="blue", background=APP_BG_COLOR)
        self.lbl_current_field.pack(side=RIGHT, padx=10)
        ttk.Label(self.fr_style_toolbar, text="Đang chọn:", style='MisaToolbar.TLabel').pack(side=RIGHT)

    def update_prop_inputs(self, cfg, field_name):
        self.lbl_current_field.config(text=field_name)
        
        if field_name == "signature_img":
            self.fr_text_props.pack_forget()
            self.fr_img_props.pack(side=LEFT, fill=X, expand=YES)
            self.spin_img_w.set(cfg.get("w", 150))
            self.spin_img_h.set(cfg.get("h", 80))
        else:
            self.fr_img_props.pack_forget()
            self.fr_text_props.pack(side=LEFT, fill=X, expand=YES)
            self.combo_font.set(cfg.get("font", "Arial"))
            self.spin_size.set(cfg.get("size", 30))
            self.chk_bold_var.set(cfg.get("bold", False))
            self.chk_upper_var.set(cfg.get("upper", False))
            self.combo_color.set(cfg.get("color", "Black"))
            