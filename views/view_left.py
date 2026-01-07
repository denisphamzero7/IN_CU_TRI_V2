# views/view_left.py
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from tkinter import filedialog 

# --- [MỚI] IMPORT HEADER ---
from views.view_header import HeaderView 
from config.settings import APP_SUPPORT, APP_CREDIT
# ---------------------------

class LeftPanelView(ttk.Frame):
    def __init__(self, master, router):
        super().__init__(master, padding=10)
        self.pack(fill=BOTH, expand=YES)
        
        self.router = router
        self.field_vars = {}    
        self.field_labels = {} 

        # --- [MỚI] 0. HEADER THÔNG TIN (ĐẶT TRÊN CÙNG) ---
        self.header = HeaderView(self)
        self.header.pack(fill=X, pady=(0, 15)) 
        
        # --- 1. CẤU HÌNH GIAO DIỆN (THEME) ---
        self._setup_theme_toggle()
        
        ttk.Separator(self, orient=HORIZONTAL).pack(fill=X, pady=10)

        # --- 2. DỮ LIỆU ĐẦU VÀO ---
        ttk.Label(self, text="1. DỮ LIỆU ĐẦU VÀO", font=("Segoe UI", 10, "bold"), bootstyle="primary").pack(anchor="w", pady=(0, 5))
        
        btn_opts = {"width": 20}
        
        ttk.Button(self, text="📂 Chọn Ảnh Phôi", command=router.select_template, bootstyle="primary", **btn_opts).pack(fill=X, pady=2)
        ttk.Button(self, text="📊 Chọn File Excel", command=router.select_excel, bootstyle="success", **btn_opts).pack(fill=X, pady=2)
        ttk.Button(self, text="📂 Folder Chữ Ký", command=router.select_signature_folder, bootstyle="info", **btn_opts).pack(fill=X, pady=2)
        
        # --- 3. DANH SÁCH TRƯỜNG ---
        ttk.Label(self, text="2. CẤU HÌNH TRƯỜNG", font=("Segoe UI", 10, "bold"), bootstyle="primary").pack(anchor="w", pady=(15, 5))
        
        self.scroll_container = ScrolledFrame(self, autohide=True, height=200)
        self.scroll_container.pack(fill=BOTH, expand=YES, pady=5)
        
        # --- [MỚI] 5. FOOTER (HỖ TRỢ & BẢN QUYỀN) ---
        # Lưu ý: Pack cái này TRƯỚC style_controls để nó nằm dưới cùng (do dùng side=BOTTOM)
        self._setup_footer()

        # --- 4. TÙY CHỈNH STYLE ---
        self._setup_style_controls()

    def _setup_footer(self):
        """Thiết lập phần chân trang (Support & Credit)"""

        # --- CẬP NHẬT NỘI DUNG TEXT ---
        txt_support = "Hỗ trợ kỹ thuật: 0911.02.12.87 (Anh Quân)"
        txt_credit = "Thiết kế bởi Danatec"

        # --- 1. Khung: Thiết kế bởi Danatec (Nằm dưới cùng nhất) ---
        # [MẸO] Dùng Frame lồng nhau để tạo viền màu liền mạch
        
        # Frame Ngoại: Đóng vai trò là viền (Màu vàng/warning)
        fr_credit_border = ttk.Frame(self, bootstyle="warning")
        fr_credit_border.pack(side=BOTTOM, fill=X, pady=(5, 5))
        
        # Frame Nội: Chứa nội dung, padding=1 để lộ 1px viền vàng
        fr_credit_inner = ttk.Frame(fr_credit_border)
        fr_credit_inner.pack(fill=BOTH, expand=YES, padx=1, pady=1)

        # Chữ màu vàng
        lbl_credit = ttk.Label(
            fr_credit_inner, 
            text=txt_credit, 
            font=("Segoe UI", 9, "bold", "italic"), 
            foreground="#FFD700",   # Màu vàng Gold
            anchor="center"
        )
        lbl_credit.pack(fill=X, pady=5)

        # --- 2. Khung: Hỗ trợ kỹ thuật (Nằm trên dòng Danatec) ---
        
        # Frame Ngoại: Đóng vai trò là viền (Màu xanh/info)
        fr_support_border = ttk.Frame(self, bootstyle="info")
        fr_support_border.pack(side=BOTTOM, fill=X, pady=(5, 0))
        
        # Frame Nội: Chứa nội dung, padding=1 để lộ 1px viền xanh
        fr_support_inner = ttk.Frame(fr_support_border)
        fr_support_inner.pack(fill=BOTH, expand=YES, padx=1, pady=1)
        
        ttk.Label(
            fr_support_inner, 
            text=txt_support, 
            font=("Segoe UI", 9, "bold"), 
            bootstyle="info",
            anchor="center"
        ).pack(fill=X, pady=5)

    def _setup_theme_toggle(self):
        fr = ttk.Frame(self)
        fr.pack(fill=X)
        ttk.Label(fr, text="Giao diện:").pack(side=LEFT)
        
        self.theme_map = {
            " Tối - Siêu anh hùng": "superhero",
            " Tối - Đêm đen": "darkly",
            " Tối - Công nghệ": "cyborg",
            " Tối - Ấm áp": "solar",
            "Sáng - Cơ bản": "cosmo",
            " Sáng - Tinh tế": "flatly",
            " Sáng - Cổ điển": "journal",
            " Sáng - Trang nhã": "litera",
            " Sáng - Bạc hà": "minty"
        }
        
        display_names = list(self.theme_map.keys())

        self.cb_theme = ttk.Combobox(fr, values=display_names, state="readonly", width=18)
        self.cb_theme.pack(side=RIGHT)
        
        current_sys_theme = ttk.Style().theme.name
        
        found_vn = False
        for vn_name, en_name in self.theme_map.items():
            if en_name == current_sys_theme:
                self.cb_theme.set(vn_name)
                found_vn = True
                break
        
        if not found_vn:
            self.cb_theme.current(0) 
            
        self.cb_theme.bind("<<ComboboxSelected>>", self.change_theme)

    def change_theme(self, event):
        vn_name = self.cb_theme.get()
        en_name = self.theme_map.get(vn_name, "superhero")
        style = ttk.Style()
        style.theme_use(en_name)

    def _setup_style_controls(self):
        group = ttk.Labelframe(self, text="3. TÙY CHỈNH STYLE", padding=10, bootstyle="info")
        # Lưu ý: side=BOTTOM sẽ đẩy cái này xuống dưới, nhưng nằm TRÊN footer vừa tạo
        group.pack(fill=X, side=BOTTOM, pady=10)
        
        self.var_edit_mode = tk.StringVar(value="global")
        
        r1 = ttk.Radiobutton(group, text="Chỉnh TẤT CẢ", variable=self.var_edit_mode, value="global", command=self.router.on_style_change)
        r1.pack(anchor="w")
        
        r2 = ttk.Radiobutton(group, text="Chỉnh RIÊNG người này", variable=self.var_edit_mode, value="individual", command=self.router.on_style_change, bootstyle="danger")
        r2.pack(anchor="w")
        
        ttk.Separator(group).pack(fill=X, pady=5)
        
        fr_info = ttk.Frame(group)
        fr_info.pack(fill=X)
        ttk.Label(fr_info, text="Đang chọn:").pack(side=LEFT)
        self.lbl_current_field = ttk.Label(fr_info, text="(Chưa chọn)", font=("Segoe UI", 9, "bold"), bootstyle="inverse-primary")
        self.lbl_current_field.pack(side=RIGHT)
        
        self.fr_text_props = ttk.Frame(group)
        self.fr_text_props.pack(fill=X, pady=5)
        
        r_font = ttk.Frame(self.fr_text_props)
        r_font.pack(fill=X)
        self.combo_font = ttk.Combobox(r_font, values=["Arial", "Times New Roman", "Calibri", "Segoe UI", "Tahoma"], width=13, state="readonly")
        self.combo_font.pack(side=LEFT, fill=X, expand=YES)
        self.combo_font.bind("<<ComboboxSelected>>", self.router.on_prop_change)
        
        self.spin_size = ttk.Spinbox(r_font, from_=5, to=300, width=5, command=self.router.on_prop_change)
        self.spin_size.pack(side=RIGHT, padx=(5,0))
        self.spin_size.bind("<Return>", self.router.on_prop_change)
        
        r_attr = ttk.Frame(self.fr_text_props)
        r_attr.pack(fill=X, pady=5)
        
        self.chk_bold_var = tk.BooleanVar()
        self.chk_upper_var = tk.BooleanVar()
        
        ttk.Checkbutton(r_attr, text="B", variable=self.chk_bold_var, bootstyle="toolbutton", width=3, command=self.router.on_prop_change).pack(side=LEFT)
        ttk.Checkbutton(r_attr, text="AA", variable=self.chk_upper_var, bootstyle="toolbutton", width=3, command=self.router.on_prop_change).pack(side=LEFT, padx=5)
        
        self.combo_color = ttk.Combobox(r_attr, values=["Black", "Red", "Blue", "#2c3e50", "#e74c3c", "#16a085", "#8e44ad"], width=8, state="readonly")
        self.combo_color.pack(side=RIGHT, fill=X, expand=YES)
        self.combo_color.bind("<<ComboboxSelected>>", self.router.on_prop_change)
        
        self.fr_img_props = ttk.Frame(group)
        
        ttk.Button(self.fr_img_props, text="📂 File chữ ký riêng", command=self.router.pick_manual_signature, bootstyle="warning-outline", width=100).pack(fill=X, pady=5)
        
        r_dim = ttk.Frame(self.fr_img_props)
        r_dim.pack(fill=X)
        ttk.Label(r_dim, text="W:").pack(side=LEFT)
        self.spin_img_w = ttk.Spinbox(r_dim, from_=1, to=1000, width=5, command=self.router.on_prop_change)
        self.spin_img_w.pack(side=LEFT, padx=2)
        
        ttk.Label(r_dim, text="H:").pack(side=LEFT, padx=(5,0))
        self.spin_img_h = ttk.Spinbox(r_dim, from_=1, to=1000, width=5, command=self.router.on_prop_change)
        self.spin_img_h.pack(side=LEFT, padx=2)
        
        self.spin_img_w.bind("<Return>", self.router.on_prop_change)
        self.spin_img_h.bind("<Return>", self.router.on_prop_change)

        ttk.Button(group, text="↺ Mặc định", command=self.router.reset_current_custom, bootstyle="link").pack(fill=X, pady=(5,0))

    def refresh_field_list(self, cols, global_config):
        for widget in self.scroll_container.winfo_children():
            widget.destroy()
            
        self.field_vars = {}
        self.field_labels = {}
        
        display_cols = list(cols)
        if "signature_img" not in display_cols: display_cols.append("signature_img")
        
        for col in display_cols:
            row_fr = ttk.Frame(self.scroll_container)
            row_fr.pack(fill=X, pady=1)
            
            is_enabled = global_config.get(col, {}).get("enable", False)
            var = tk.BooleanVar(value=is_enabled)
            self.field_vars[col] = var
            
            chk = ttk.Checkbutton(row_fr, variable=var, bootstyle="round-toggle", command=lambda c=col: self.router.on_field_toggle(c))
            chk.pack(side=LEFT)
            
            display_text = "📷 ẢNH CHỮ KÝ" if col == "signature_img" else col
            lbl = ttk.Label(row_fr, text=display_text, padding=(5, 2))
            lbl.pack(side=LEFT, fill=X, expand=YES)
            
            lbl.bind("<Button-1>", lambda e, c=col: self.router.select_field(c))
            self.field_labels[col] = lbl

    def update_prop_inputs(self, cfg, field_name):
        self.lbl_current_field.config(text=field_name)
        
        for f, lbl in self.field_labels.items():
            if f == field_name:
                lbl.configure(bootstyle="inverse-info") 
            else:
                lbl.configure(bootstyle="default")
        
        if field_name == "signature_img":
            self.fr_text_props.pack_forget()
            self.fr_img_props.pack(fill=X)
            self.spin_img_w.set(cfg.get("w", 150))
            self.spin_img_h.set(cfg.get("h", 80))
        else:
            self.fr_img_props.pack_forget()
            self.fr_text_props.pack(fill=X)
            self.combo_font.set(cfg.get("font", "Arial"))
            self.spin_size.set(cfg.get("size", 30))
            self.chk_bold_var.set(cfg.get("bold", False))
            self.chk_upper_var.set(cfg.get("upper", False))
            self.combo_color.set(cfg.get("color", "Black"))