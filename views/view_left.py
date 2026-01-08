import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from tkinter import filedialog 

# --- IMPORT HEADER & SETTINGS ---
from views.view_header import HeaderView 
from config.settings import (
    APP_SUPPORT, APP_CREDIT, 
    MISA_BG_COLOR, MISA_BORDER_COLOR, 
    MISA_TEXT_NORMAL, MISA_WHITE
)

# --- MÀU CỐ ĐỊNH ---
LIST_ITEM_BG = "#ffffff"       # Nền hộp chữ màu TRẮNG
LIST_SELECTED_BG = MISA_BORDER_COLOR # Nền hộp chữ màu XANH ĐẬM

class LeftPanelView(ttk.Frame):
    def __init__(self, master, router):
        
        # --- 1. THIẾT LẬP STYLE ---
        style = ttk.Style()
        
        # A. Style nền Panel chính
        style.configure('TFrame', background=MISA_BG_COLOR)
        style.configure('TLabel', background=MISA_BG_COLOR, foreground=MISA_TEXT_NORMAL, font=("Segoe UI", 9))
        
        # B. Checkbox (Luôn nền MISA để tệp với cột bên trái)
        style.configure('Misa.TCheckbutton', 
                        background=MISA_BG_COLOR, 
                        foreground=MISA_TEXT_NORMAL,
                        font=("Segoe UI", 9))
        
        style.map('Misa.TCheckbutton',
                  background=[('active', MISA_BG_COLOR), ('!disabled', MISA_BG_COLOR)],
                  foreground=[('active', 'black')])

        # C. Các style khác
        style.configure('TLabelframe', background=MISA_BG_COLOR, bordercolor=MISA_BORDER_COLOR, borderwidth=1, relief="solid")
        style.configure('TLabelframe.Label', background=MISA_BG_COLOR, foreground=MISA_BORDER_COLOR, font=("Segoe UI", 9, "bold"))
        style.configure('Misa.TButton', background=MISA_BG_COLOR, foreground=MISA_BORDER_COLOR, bordercolor=MISA_BORDER_COLOR, borderwidth=1, relief="solid", focusthickness=0, font=("Segoe UI", 9, "bold"), anchor="center", padding=6)
        style.map('Misa.TButton', background=[('pressed', '#bac8e0'), ('active', '#ffffff')], foreground=[('pressed', MISA_BORDER_COLOR), ('active', '#005082')], bordercolor=[('active', '#005082')]) 
        style.configure('Section.TLabel', background=MISA_BG_COLOR, foreground=MISA_BORDER_COLOR, font=("Segoe UI", 10, "bold"))

        # ---------------------------------------------------------
        
        super().__init__(master, padding=10)
        self.pack(fill=BOTH, expand=YES)
        
        self.router = router
        self.field_vars = {}    
        self.field_labels = {} 
        self.field_content_frames = {} 

        # --- 0. HEADER ---
        self.header = HeaderView(self)
        self.header.pack(fill=X, pady=(0, 15)) 
        
        # --- 1. DỮ LIỆU ĐẦU VÀO ---
        ttk.Label(self, text="1. DỮ LIỆU ĐẦU VÀO", style="Section.TLabel").pack(anchor="w", pady=(10, 5))
        
        fr_buttons = ttk.Frame(self)
        fr_buttons.pack(fill=X, pady=5)
        
        btn_opts = {"width": 20, "style": "Misa.TButton", "cursor": "hand2"}
        ttk.Button(fr_buttons, text="📂 Chọn Ảnh Phôi", command=router.select_template, **btn_opts).pack(fill=X, pady=2)
        ttk.Button(fr_buttons, text="📊 Chọn File Excel", command=router.select_excel, **btn_opts).pack(fill=X, pady=2)
        ttk.Button(fr_buttons, text="📂 Folder Chữ Ký", command=router.select_signature_folder, **btn_opts).pack(fill=X, pady=2)
        
        # --- 2. CẤU HÌNH TRƯỜNG ---
        ttk.Label(self, text="2. CẤU HÌNH TRƯỜNG", style="Section.TLabel").pack(anchor="w", pady=(15, 5))
        
        # Container danh sách
        self.scroll_container = ScrolledFrame(self, autohide=True, height=200, bootstyle="round")
        self.scroll_container.pack(fill=BOTH, expand=YES, pady=5)
        
        # [FIX] Ép màu nền MISA cho Canvas (vùng cuộn)
        for child in self.scroll_container.winfo_children():
            if isinstance(child, tk.Canvas):
                child.configure(bg=MISA_BG_COLOR, highlightthickness=0)
        
        # [FIX QUAN TRỌNG] Dùng STYLE để set màu nền cho Container (thay vì background=...)
        # Điều này giúp tạo ra nền MISA, làm lộ ra các đường kẻ hở giữa các dòng
        style.configure('ListContainer.TFrame', background=MISA_BG_COLOR)
        self.scroll_container.container.configure(style='ListContainer.TFrame')

        # --- 5. FOOTER ---
        self._setup_footer()

        # --- 4. TÙY CHỈNH STYLE ---
        self._setup_style_controls()

    def _setup_footer(self):
        fr_footer = ttk.Labelframe(self, text="Thông tin liên hệ", padding=5)
        fr_footer.pack(side=BOTTOM, fill=X, pady=(10, 0))

        lbl_credit = ttk.Label(fr_footer, text=APP_CREDIT, font=("Segoe UI", 9, "bold", "italic"), foreground="#d35400", anchor="center")
        lbl_credit.pack(fill=X)

        lbl_support = ttk.Label(fr_footer, text=APP_SUPPORT, font=("Segoe UI", 9), foreground=MISA_TEXT_NORMAL, anchor="center")
        lbl_support.pack(fill=X)

    def _setup_style_controls(self):
        group = ttk.Labelframe(self, text="3. TÙY CHỈNH STYLE", padding=10)
        group.pack(fill=X, side=BOTTOM, pady=10)
        
        fr_info = ttk.Frame(group)
        fr_info.pack(fill=X)
        ttk.Label(fr_info, text="Đang chọn:").pack(side=LEFT)
        
        self.lbl_current_field = tk.Label(fr_info, text="(Chưa chọn)", font=("Segoe UI", 9, "bold"), 
                                          bg=MISA_BORDER_COLOR, fg=MISA_WHITE, padx=5)
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
        
        ttk.Checkbutton(r_attr, text="B", variable=self.chk_bold_var, style="Misa.TCheckbutton", command=self.router.on_prop_change).pack(side=LEFT)
        ttk.Checkbutton(r_attr, text="AA", variable=self.chk_upper_var, style="Misa.TCheckbutton", command=self.router.on_prop_change).pack(side=LEFT, padx=5)
        
        self.combo_color = ttk.Combobox(r_attr, values=["Black", "Red", "Blue", "#2c3e50", "#e74c3c", "#16a085", "#8e44ad"], width=8, state="readonly")
        self.combo_color.pack(side=RIGHT, fill=X, expand=YES)
        self.combo_color.bind("<<ComboboxSelected>>", self.router.on_prop_change)
        
        self.fr_img_props = ttk.Frame(group)
        ttk.Button(self.fr_img_props, text="📂 File chữ ký riêng", command=self.router.pick_manual_signature, style="Misa.TButton", width=100).pack(fill=X, pady=5)
        
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

        ttk.Button(group, text="↺ Mặc định", command=self.router.reset_current_custom, style="Link.TButton").pack(fill=X, pady=(5,0))

    def refresh_field_list(self, cols, global_config):
        for widget in self.scroll_container.winfo_children():
            widget.destroy()
            
        self.field_vars = {}
        self.field_labels = {}
        self.field_content_frames = {} 
        
        display_cols = list(cols)
        if "signature_img" not in display_cols: display_cols.append("signature_img")
        
        for col in display_cols:
            # 1. CONTAINER DÒNG (Row): Nền MISA
            # pady=1 -> Tạo đường kẻ hở màu MISA giữa các dòng
            row_fr = tk.Frame(self.scroll_container, bg=MISA_BG_COLOR)
            row_fr.pack(fill=X, pady=1, padx=2) 
            
            is_enabled = global_config.get(col, {}).get("enable", False)
            var = tk.BooleanVar(value=is_enabled)
            self.field_vars[col] = var
            
            # 2. CHECKBOX: Nằm trực tiếp trên row_fr (Nền MISA)
            # Không bị bọc bởi frame trắng -> Luôn tệp màu nền
            chk = ttk.Checkbutton(row_fr, variable=var, style='Misa.TCheckbutton', command=lambda c=col: self.router.on_field_toggle(c))
            chk.pack(side=LEFT, padx=(5,0))
            
            # 3. CONTENT FRAME (Hộp chứa chữ): Nền TRẮNG
            # Đây là phần sẽ đổi màu khi click
            content_fr = tk.Frame(row_fr, bg=LIST_ITEM_BG)
            content_fr.pack(side=LEFT, fill=BOTH, expand=YES, padx=(5, 0)) 
            
            self.field_content_frames[col] = content_fr
            
            display_text = "📷 ẢNH CHỮ KÝ" if col == "signature_img" else col
            
            # 4. LABEL: Nằm trong Content Frame
            lbl = tk.Label(content_fr, text=display_text, padx=5, pady=4, 
                           bg=LIST_ITEM_BG, fg=MISA_TEXT_NORMAL, 
                           anchor="w", font=("Segoe UI", 9))
            lbl.pack(fill=BOTH, expand=YES)
            
            # Binding click
            lbl.bind("<Button-1>", lambda e, c=col: self.router.select_field(c))
            content_fr.bind("<Button-1>", lambda e, c=col: self.router.select_field(c))
            
            self.field_labels[col] = lbl

    def update_prop_inputs(self, cfg, field_name):
        self.lbl_current_field.config(text=field_name)
        
        for f, lbl in self.field_labels.items():
            content_fr = self.field_content_frames.get(f)
            
            if f == field_name:
                # --- CHỌN: ĐỔI MÀU HỘP CHỮ ---
                # Checkbox và nền dòng bên ngoài vẫn giữ màu Misa
                if content_fr: content_fr.configure(bg=LIST_SELECTED_BG) 
                lbl.configure(bg=LIST_SELECTED_BG, fg=MISA_WHITE, font=("Segoe UI", 9, "bold"))
            else:
                # --- KHÔNG CHỌN: VỀ MÀU TRẮNG ---
                if content_fr: content_fr.configure(bg=LIST_ITEM_BG) 
                lbl.configure(bg=LIST_ITEM_BG, fg=MISA_TEXT_NORMAL, font=("Segoe UI", 9))
        
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