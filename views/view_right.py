import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import win32print
from helpers.ui_helpers import create_button
from config.settings import APP_BG_COLOR
from helpers.msg_helper import MsgHelper

# --- KHAI BÁO FONT CHUẨN CHO TOOLBAR ---
TB_FONT = ("Segoe UI", 7)
TB_FONT_BOLD = ("Segoe UI", 7, "bold")

class RightPanelView(ttk.Frame):
    def __init__(self, parent, router):
        # --- CẤU HÌNH STYLE ---
        style = ttk.Style()
        style.configure('Misa.TFrame', background=APP_BG_COLOR)
        
        # Lấy màu xanh chủ đạo (Primary) của theme hiện tại để dùng cho viền
        primary_color = style.colors.primary
        
        # 1. Label/Checkbox Toolbar
        style.configure('MisaToolbar.TLabel', background=APP_BG_COLOR, foreground="#333333", font=TB_FONT_BOLD)
        style.configure('Toolbar.TCheckbutton', background=APP_BG_COLOR, foreground="#333333", font=TB_FONT_BOLD)
        style.map('Toolbar.TCheckbutton', background=[('active', APP_BG_COLOR)], foreground=[('active', 'black')])

        # 2. Style Nút Gọn Thường
        style.configure('Compact.Danger.TButton', font=TB_FONT, padding=(3, 0))
        style.configure('Compact.Outline.TButton', font=TB_FONT, padding=(3, 0))
        style.configure('Compact.Link.TButton', font=TB_FONT, padding=(0, 0))

        # 3. [STYLE ĐẶC BIỆT] Nút Xoay: Viền luôn Xanh, Chữ Xám khi Disabled
        style.configure('Compact.Rotate.TButton', 
                        font=TB_FONT, 
                        padding=(2, 0),        # Ép độ cao bằng Combobox
                        borderwidth=1,         # Có viền
                        background=APP_BG_COLOR) # Nền trùng màu app

        # Map màu sắc: Chìa khóa để viền xanh nhưng chữ xám
        style.map('Compact.Rotate.TButton',
                  # Viền (bordercolor): Luôn là màu Primary (Xanh) bất kể trạng thái
                  bordercolor=[('disabled', primary_color), ('!disabled', primary_color)], 
                  
                  # Chữ (foreground): Xám khi disabled, Đen/Xanh khi active (tùy ý)
                  foreground=[('disabled', '#a0a0a0'), ('!disabled', 'black')],
                  
                  # Nền: Giữ nguyên màu nền app để nhìn như Outline
                  background=[('active', APP_BG_COLOR), ('!disabled', APP_BG_COLOR)]
        )

        # 4. Style Spinbox Gọn
        style.configure('Compact.TSpinbox', arrowsize=9, padding=(1, 0, 1, 0), font=TB_FONT)

        super().__init__(parent, style='Misa.TFrame')
        self.pack(fill=BOTH, expand=YES)
        self.router = router

        self.option_add('*TCombobox*Listbox.font', TB_FONT)
        
        self._setup_top_toolbar()
        
        # --- CANVAS ---
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
        if self.router.ctrl_license.is_licensed:
            return func(*args)
        else:
            MsgHelper.show_warning("Tính năng này chỉ dành cho bản quyền Pro!")
   
    def _bind_placeholder(self, widget, var, placeholder_text):
        """Hàm tạo hiệu ứng placeholder cho Spinbox"""
        # Gán giá trị ban đầu là placeholder
        var.set(placeholder_text)
        # Chỉnh màu chữ thành xám (giả lập placeholder)
        try: widget.configure(foreground="#888888")
        except: pass

        def on_focus_in(event):
            # Khi click vào, nếu đang là chữ placeholder thì xóa đi
            if var.get() == placeholder_text:
                var.set("")
                try: widget.configure(foreground="#333333") # Màu chữ chính (đen/xám đậm)
                except: pass

        def on_focus_out(event):
            # Khi click ra ngoài, nếu rỗng thì điền lại placeholder
            if var.get().strip() == "":
                var.set(placeholder_text)
                try: widget.configure(foreground="#888888") # Màu chữ mờ
                except: pass
        
        widget.bind("<FocusIn>", on_focus_in)
        widget.bind("<FocusOut>", on_focus_out)

    # --- CẬP NHẬT LẠI PHƯƠNG THỨC NÀY ---
    def _setup_top_toolbar(self):
        self.tb_frame = ttk.Frame(self, padding=0, style='Misa.TFrame')
        self.tb_frame.pack(fill=X, side=TOP)

        # ============================================================
        # [HÀNG 1]
        # ============================================================
        row1 = ttk.Frame(self.tb_frame, style='Misa.TFrame')
        row1.pack(fill=X, side=TOP, pady=(2, 1))

        # NÚT PRINT
        btn_print = ttk.Button(row1, text="🖨️", width=3, command=self.router.start_print, bootstyle="danger")
        btn_print.pack(side=RIGHT, padx=(3, 2))
        
        # NÚT XOAY
        self.btn_rotate = ttk.Button(
            row1, 
            text="↻ Ảnh", 
            command=self.router.rotate_template_right, 
            width=5,
            style="Compact.Rotate.TButton", 
            state="disabled"
        )
        self.btn_rotate.pack(side=RIGHT, padx=(2, 0), fill=Y)

        # --- MÁY IN (ĐÃ SỬA: Bỏ Label, đưa chữ vào Combobox) ---
        try: printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        except: printers = []
        
        # Tăng width lên để chứa đủ chữ "Chọn máy in..."
        self.cbb_printer = ttk.Combobox(row1, values=printers, state="readonly", width=15, bootstyle="primary", font=TB_FONT)
        
        if printers:
            # Nếu muốn mặc định chọn máy in đầu tiên thì dùng dòng dưới:
            # self.cbb_printer.current(0)
            
            # Nếu muốn hiển thị Placeholder "Chọn máy in..." như yêu cầu:
            self.cbb_printer.set("Chọn máy in...") 
        else:
            self.cbb_printer.set("Không có máy in")
            
        self.cbb_printer.pack(side=RIGHT, padx=1)
        
        # (Đã xóa Label "Máy in:")

        # --- TỪ - ĐẾN (Giữ nguyên logic placeholder từ bước trước) ---
        fr_range = ttk.Frame(row1, style='Misa.TFrame')
        fr_range.pack(side=RIGHT, padx=5)
        
        # Input Từ
        self.var_print_from = tk.StringVar()
        self.entry_from = ttk.Spinbox(fr_range, from_=1, to=9999, textvariable=self.var_print_from, width=5, style="Compact.TSpinbox")
        self.entry_from.pack(side=LEFT, padx=(1, 3))
        self._bind_placeholder(self.entry_from, self.var_print_from, "Từ") # Placeholder
        
        ttk.Label(fr_range, text="-", style='MisaToolbar.TLabel').pack(side=LEFT)

        # Input Đến
        self.var_print_to = tk.StringVar()
        self.entry_to = ttk.Spinbox(fr_range, from_=1, to=9999, textvariable=self.var_print_to, width=5, style="Compact.TSpinbox")
        self.entry_to.pack(side=LEFT, padx=(3, 0))
        self._bind_placeholder(self.entry_to, self.var_print_to, "Đến") # Placeholder

        # KHỔ GIẤY
        fr_paper = ttk.Frame(row1, style='Misa.TFrame')
        fr_paper.pack(side=LEFT, padx=2)

        self.var_paper_size = tk.StringVar(value="A6")
        cbb_size = ttk.Combobox(fr_paper, textvariable=self.var_paper_size, values=["A4", "A5", "A6"], width=3, state="disabled", bootstyle="primary", font=TB_FONT)
        cbb_size.pack(side=LEFT, padx=1)
        cbb_size.bind("<<ComboboxSelected>>", self.router.on_paper_config_change)

        self.var_orientation = tk.StringVar(value="Ngang")
        self.cbb_orientation = ttk.Combobox(fr_paper, textvariable=self.var_orientation, values=["Dọc", "Ngang"], state="disabled", width=5, bootstyle="primary", font=TB_FONT)
        self.cbb_orientation.pack(side=LEFT, padx=1)
        self.cbb_orientation.bind("<<ComboboxSelected>>", self.router.on_orientation_change)

        # CHẾ ĐỘ IN
        self.var_print_mode = tk.StringVar(value="Chỉ dữ liệu")
        self.cbb_print_mode = ttk.Combobox(fr_paper, textvariable=self.var_print_mode,
                                             values=["Chỉ dữ liệu", "Dữ liệu + Phôi"],
                                             state="disabled", width=9, bootstyle="primary", font=TB_FONT)
        self.cbb_print_mode.pack(side=LEFT, padx=1)

        # ============================================================
        # [HÀNG 2]
        # ============================================================
        self.fr_style_toolbar = ttk.Frame(self.tb_frame, style='Misa.TFrame')
        self.fr_style_toolbar.pack(fill=X, side=TOP, pady=(1, 2))

        # --- TEXT PROPS ---
        self.fr_text_props = ttk.Frame(self.fr_style_toolbar, style='Misa.TFrame')
        self.fr_text_props.pack(side=LEFT, fill=X, expand=YES)

        # (Đã xóa Label "Font:")
        # Combobox Font: Set text mặc định là "Font"
        self.combo_font = ttk.Combobox(self.fr_text_props, values=["Arial", "Times New Roman", "Calibri", "Segoe UI", "Tahoma"], width=20, state="readonly", font=TB_FONT)
        self.combo_font.set("Font") # Placeholder giả cho Combobox readonly
        self.combo_font.pack(side=LEFT, padx=(2, 2))
        self.combo_font.bind("<<ComboboxSelected>>", lambda e: self._require_license(self.router.on_prop_change, e))

        # (Đã xóa Label "Size:")
        # Spinbox Size: Dùng _bind_placeholder
        # Lưu ý: Spinbox lưu số, nên khi binding text vào cần cẩn thận khi get giá trị để tính toán (cần try/except int)
        self.var_font_size = tk.StringVar() # Cần biến Var riêng để bind
        self.spin_size = ttk.Spinbox(self.fr_text_props, from_=5, to=300, textvariable=self.var_font_size, width=5, command=lambda: self._require_license(self.router.on_prop_change), style="Compact.TSpinbox")
        self.spin_size.pack(side=LEFT, padx=(0, 2))
        self._bind_placeholder(self.spin_size, self.var_font_size, "Size") # Placeholder
        self.spin_size.bind("<Return>", lambda e: self._require_license(self.router.on_prop_change, e))

        # Bold / Upper
        self.chk_bold_var = tk.BooleanVar()
        self.chk_upper_var = tk.BooleanVar()
        ttk.Checkbutton(self.fr_text_props, text="B", variable=self.chk_bold_var, style="Toolbar.TCheckbutton", command=lambda: self._require_license(self.router.on_prop_change)).pack(side=LEFT, padx=(0, 2))
        ttk.Checkbutton(self.fr_text_props, text="AA", variable=self.chk_upper_var, style="Toolbar.TCheckbutton", command=lambda: self._require_license(self.router.on_prop_change)).pack(side=LEFT, padx=(0, 2))

        # Màu
        # (Đã xóa Label "Màu:") - Nếu bạn muốn bỏ luôn label Màu thì dùng dòng dưới, tôi tạm để Label Màu vì bạn chưa nhắc tới
        # Nhưng để đồng bộ phong cách, tôi sẽ đưa "Màu" vào Combobox luôn:
        ttk.Label(self.fr_text_props, text="Màu:", style='MisaToolbar.TLabel').pack(side=LEFT, padx=(0,1)) # Giữ label Màu cho rõ nghĩa hoặc bạn có thể xóa dòng này và set("Màu") cho combo_color
        self.combo_color = ttk.Combobox(self.fr_text_props, values=["Black", "Red", "Blue"], width=6, state="readonly", font=TB_FONT)
        self.combo_color.set("Black")
        self.combo_color.pack(side=LEFT)
        self.combo_color.bind("<<ComboboxSelected>>", lambda e: self._require_license(self.router.on_prop_change, e))

        # --- IMAGE PROPS (Giữ nguyên) ---
        self.fr_img_props = ttk.Frame(self.fr_style_toolbar, style='Misa.TFrame')
        
        ttk.Label(self.fr_img_props, text="Size:", style='MisaToolbar.TLabel').pack(side=LEFT)
        ttk.Label(self.fr_img_props, text="W:", style='MisaToolbar.TLabel').pack(side=LEFT, padx=(2,1))
        self.spin_img_w = ttk.Spinbox(self.fr_img_props, from_=1, to=1000, width=4, command=lambda: self._require_license(self.router.on_prop_change), style="Compact.TSpinbox")
        self.spin_img_w.pack(side=LEFT)
        self.spin_img_w.bind("<Return>", lambda e: self._require_license(self.router.on_prop_change, e))

        ttk.Label(self.fr_img_props, text="H:", style='MisaToolbar.TLabel').pack(side=LEFT, padx=(5,1))
        self.spin_img_h = ttk.Spinbox(self.fr_img_props, from_=1, to=1000, width=4, command=lambda: self._require_license(self.router.on_prop_change), style="Compact.TSpinbox")
        self.spin_img_h.pack(side=LEFT)
        self.spin_img_h.bind("<Return>", lambda e: self._require_license(self.router.on_prop_change, e))

        # NÚT CHỌN FILE
        ttk.Button(self.fr_img_props, text="📂 Chọn file...", command=lambda: self._require_license(self.router.pick_manual_signature), style="Compact.Outline.TButton", bootstyle="warning-outline").pack(side=LEFT, padx=(5, 0))

        # ============================================================
        # [PHẦN KHÔI PHỤC GỐC]
        # ============================================================
        ttk.Button(self.fr_style_toolbar, text="↺ Mặc định", command=lambda: self._require_license(self.router.reset_current_custom), style="Compact.Link.TButton", bootstyle="link").pack(side=RIGHT, padx=(0, 2))

        self.lbl_current_field = ttk.Label(self.fr_style_toolbar, text="(Chưa chọn)", font=TB_FONT_BOLD, foreground="blue", background=APP_BG_COLOR)
        self.lbl_current_field.pack(side=RIGHT, padx=5)

        ttk.Label(self.fr_style_toolbar, text="Đang chọn:", style='MisaToolbar.TLabel').pack(side=RIGHT)

    # ... (Giữ nguyên các hàm update_prop_inputs) ...
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