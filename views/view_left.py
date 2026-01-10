import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from views.view_header import HeaderView 
from config.settings import APP_SUPPORT, APP_CREDIT, MISA_BG_COLOR, MISA_BORDER_COLOR, MISA_TEXT_NORMAL, MISA_WHITE

# --- MÀU CỐ ĐỊNH ---
LIST_ITEM_BG = "#ffffff"       
LIST_SELECTED_BG = MISA_BORDER_COLOR 

class LeftPanelView(ttk.Frame):
    def __init__(self, master, router):
        
        # --- 1. THIẾT LẬP STYLE ---
        style = ttk.Style()
        style.configure('TFrame', background=MISA_BG_COLOR)
        style.configure('TLabel', background=MISA_BG_COLOR, foreground=MISA_TEXT_NORMAL, font=("Segoe UI", 9))
        
        # Checkbox
        style.configure('Misa.TCheckbutton', background=MISA_BG_COLOR, foreground=MISA_TEXT_NORMAL, font=("Segoe UI", 9))
        style.map('Misa.TCheckbutton', background=[('active', MISA_BG_COLOR), ('!disabled', MISA_BG_COLOR)], foreground=[('active', 'black')])

        # Các style khác
        style.configure('TLabelframe', background=MISA_BG_COLOR, bordercolor=MISA_BORDER_COLOR, borderwidth=1, relief="solid")
        style.configure('TLabelframe.Label', background=MISA_BG_COLOR, foreground=MISA_BORDER_COLOR, font=("Segoe UI", 9, "bold"))
        style.configure('Misa.TButton', background=MISA_BG_COLOR, foreground=MISA_BORDER_COLOR, bordercolor=MISA_BORDER_COLOR, borderwidth=1, relief="solid", focusthickness=0, font=("Segoe UI", 9, "bold"), anchor="center", padding=6)
        style.map('Misa.TButton', background=[('pressed', '#bac8e0'), ('active', '#ffffff')], foreground=[('pressed', MISA_BORDER_COLOR), ('active', '#005082')], bordercolor=[('active', '#005082')]) 
        style.configure('Section.TLabel', background=MISA_BG_COLOR, foreground=MISA_BORDER_COLOR, font=("Segoe UI", 10, "bold"))

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
        
        self.fr_buttons = ttk.Frame(self) 
        self.fr_buttons.pack(fill=X, pady=5)
        
        btn_opts = {"width": 12, "style": "Misa.TButton", "cursor": "hand2"}
        
        self.btn_template = ttk.Button(self.fr_buttons, text="📷 Ảnh Phôi", command=router.select_template, **btn_opts)
        self.btn_template.pack(side=LEFT, padx=2, expand=YES, fill=X)
        
        self.btn_excel = ttk.Button(self.fr_buttons, text="📊 Dữ Liệu", command=router.select_excel, **btn_opts)
        self.btn_excel.pack(side=LEFT, padx=2, expand=YES, fill=X)
        
        self.btn_folder = ttk.Button(self.fr_buttons, text="📂 Chữ Ký", command=router.select_signature_folder, **btn_opts)
        self.btn_folder.pack(side=LEFT, padx=2, expand=YES, fill=X)
        
        # --- 2. CẤU HÌNH TRƯỜNG ---
        ttk.Label(self, text="2. CẤU HÌNH TRƯỜNG", style="Section.TLabel").pack(anchor="w", pady=(15, 5))
        
        # Container danh sách
        self.scroll_container = ScrolledFrame(self, autohide=True, height=200, bootstyle="round")
        self.scroll_container.pack(fill=BOTH, expand=YES, pady=5)
        
        for child in self.scroll_container.winfo_children():
            if isinstance(child, tk.Canvas):
                child.configure(bg=MISA_BG_COLOR, highlightthickness=0)
        
        style.configure('ListContainer.TFrame', background=MISA_BG_COLOR)
        self.scroll_container.container.configure(style='ListContainer.TFrame')

        # --- 3. FOOTER & LICENSE ---
        self._setup_footer()
        self._setup_license_ui()

    def _setup_license_ui(self):
        """Khu vực hiển thị HWID và nhập Key"""
        self.fr_license = ttk.Labelframe(self, text="Cập nhật mã sử dụng", padding=10, bootstyle="danger")
        self.fr_license.pack(side=BOTTOM, fill=X, pady=(10, 0))

        # 1. Hiển thị HWID
        r1 = ttk.Frame(self.fr_license, style='TFrame')
        r1.pack(fill=X)
        ttk.Label(r1, text="Mã máy:", font=("Segoe UI", 9, "bold")).pack(side=LEFT)
        
        self.ent_hwid = ttk.Entry(r1, state="readonly", width=25, font=("Consolas", 9))
        self.ent_hwid.pack(side=LEFT, padx=5, fill=X, expand=YES)
        
        # Nút copy nhỏ với biểu tượng
        ttk.Button(r1, text="📋", width=3, bootstyle="info", 
                   command=lambda: self.router.ctrl_license.on_copy_hwid()).pack(side=RIGHT)

        # 2. Nhập Key
        ttk.Label(self.fr_license, text="Nhập key:", font=("Segoe UI", 9,"bold")).pack(anchor="w", pady=(5,0))
        
        r2 = ttk.Frame(self.fr_license, style='TFrame')
        r2.pack(fill=X, pady=2)
        
        self.ent_key = ttk.Entry(r2, show="*")
        self.ent_key.pack(side=LEFT, fill=X, expand=YES)
        
        # Nút Kích Hoạt
        self.btn_activate = ttk.Button(r2, text="⚠", bootstyle="danger", 
                                       command=lambda: self.router.ctrl_license.on_activate())
        self.btn_activate.pack(side=RIGHT, padx=(5,0))

        # [ĐÃ XÓA] Dòng Label trạng thái ở đây

    def _setup_footer(self):
        fr_footer = ttk.Labelframe(self, text="Thông tin liên hệ", padding=5)
        fr_footer.pack(side=BOTTOM, fill=X, pady=(10, 0))

        lbl_credit = ttk.Label(fr_footer, text=APP_CREDIT, font=("Segoe UI", 9, "bold", "italic"), foreground="#d35400", anchor="center")
        lbl_credit.pack(fill=X)

        lbl_support = ttk.Label(fr_footer, text=APP_SUPPORT, font=("Segoe UI", 9), foreground=MISA_TEXT_NORMAL, anchor="center")
        lbl_support.pack(fill=X)

    def refresh_field_list(self, cols, global_config):
        for widget in self.scroll_container.winfo_children():
            widget.destroy()
            
        self.field_vars = {}
        self.field_labels = {}
        self.field_content_frames = {} 
        
        display_cols = list(cols)
        if "signature_img" not in display_cols: display_cols.append("signature_img")
        
        for col in display_cols:
            row_fr = tk.Frame(self.scroll_container, bg=MISA_BG_COLOR)
            row_fr.pack(fill=X, pady=1, padx=2) 
            
            is_enabled = global_config.get(col, {}).get("enable", False)
            var = tk.BooleanVar(value=is_enabled)
            self.field_vars[col] = var
            
            chk = ttk.Checkbutton(row_fr, variable=var, style='Misa.TCheckbutton', command=lambda c=col: self.router.on_field_toggle(c))
            chk.pack(side=LEFT, padx=(5,0))
            
            content_fr = tk.Frame(row_fr, bg=LIST_ITEM_BG)
            content_fr.pack(side=LEFT, fill=BOTH, expand=YES, padx=(5, 0)) 
            
            self.field_content_frames[col] = content_fr
            
            display_text = "📷 ẢNH CHỮ KÝ" if col == "signature_img" else col
            
            lbl = tk.Label(content_fr, text=display_text, padx=5, pady=4, 
                           bg=LIST_ITEM_BG, fg=MISA_TEXT_NORMAL, 
                           anchor="w", font=("Segoe UI", 9))
            lbl.pack(fill=BOTH, expand=YES)
            
            lbl.bind("<Button-1>", lambda e, c=col: self.router.select_field(c))
            content_fr.bind("<Button-1>", lambda e, c=col: self.router.select_field(c))
            
            self.field_labels[col] = lbl

    def highlight_selected_field(self, field_name):
        for f, lbl in self.field_labels.items():
            content_fr = self.field_content_frames.get(f)
            
            if f == field_name:
                if content_fr: content_fr.configure(bg=LIST_SELECTED_BG) 
                lbl.configure(bg=LIST_SELECTED_BG, fg=MISA_WHITE, font=("Segoe UI", 9, "bold"))
            else:
                if content_fr: content_fr.configure(bg=LIST_ITEM_BG) 
                lbl.configure(bg=LIST_ITEM_BG, fg=MISA_TEXT_NORMAL, font=("Segoe UI", 9))