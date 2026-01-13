import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.scrolled import ScrolledFrame
from views.view_header import HeaderView 
from config.settings import APP_SUPPORT, APP_CREDIT, MISA_BG_COLOR, MISA_BORDER_COLOR, MISA_TEXT_NORMAL, MISA_WHITE, STATIC_FIELDS_LIST

# --- MÀU CỐ ĐỊNH ---
LIST_ITEM_BG = "#ffffff"       
LIST_SELECTED_BG = MISA_BORDER_COLOR 

class LeftPanelView(ttk.Frame):
    def __init__(self, master, router):
        # --- 1. THIẾT LẬP STYLE ---
        style = ttk.Style()
        style.configure('Small.info.TButton', font=("Segoe UI", 8), padding=(4, 2))
        style.configure('Small.danger.TButton', font=("Segoe UI", 8), padding=(4, 2))
        style.configure('Small.success.TButton', font=("Segoe UI", 8), padding=(4, 2))
        # Style cho Frame nền (Mặc định và Highlight)
        style.configure('TFrame', background=MISA_BG_COLOR)
        # [MỚI] Style này dùng để làm viền xanh đậm cho ô input khi được chọn
        style.configure('Highlight.TFrame', background=MISA_BORDER_COLOR) 
        
        style.configure('TLabel', background=MISA_BG_COLOR, foreground=MISA_TEXT_NORMAL, font=("Segoe UI", 7))
        
        # Checkbox & Button Style
        style.configure('Misa.TCheckbutton', background=MISA_BG_COLOR, foreground=MISA_TEXT_NORMAL, font=("Segoe UI", 7))
        style.map('Misa.TCheckbutton', background=[('active', MISA_BG_COLOR), ('!disabled', MISA_BG_COLOR)], foreground=[('active', 'black')])
        style.configure('TLabelframe', background=MISA_BG_COLOR, bordercolor=MISA_BORDER_COLOR, borderwidth=1, relief="solid")
        style.configure('TLabelframe.Label', background=MISA_BG_COLOR, foreground=MISA_BORDER_COLOR, font=("Segoe UI", 6, "bold"))
        style.configure('Misa.TButton', background=MISA_BG_COLOR, foreground=MISA_BORDER_COLOR, bordercolor=MISA_BORDER_COLOR, borderwidth=1, relief="solid", focusthickness=0, font=("Segoe UI", 6, "bold"), anchor="center", padding=6)
        style.map('Misa.TButton', background=[('pressed', '#bac8e0'), ('active', '#ffffff')], foreground=[('pressed', MISA_BORDER_COLOR), ('active', '#005082')], bordercolor=[('active', '#005082')]) 
        style.configure('Section.TLabel', background=MISA_BG_COLOR, foreground=MISA_BORDER_COLOR, font=("Segoe UI", 6, "bold"))

        super().__init__(master, padding=5)
        self.pack(fill=BOTH, expand=YES)
        
        self.router = router
        self.field_vars = {}    
        self.field_labels = {} 
        self.field_content_frames = {} 
        self.static_entries = {} # Lưu tham chiếu các ô input Entry
        self.static_frames = {}  # [MỚI] Lưu tham chiếu Frame chứa input (để đổi màu viền)

        # --- 0. HEADER ---
        self.header = HeaderView(self)
        self.header.pack(fill=X, pady=(4, 0)) 
        
        # --- 1. DỮ LIỆU ĐẦU VÀO ---
        ttk.Label(self, text="1. DỮ LIỆU ĐẦU VÀO", style="Section.TLabel").pack(anchor="w", pady=(5,5))
        
        self.fr_buttons = ttk.Frame(self) 
        self.fr_buttons.pack(fill=X, pady=0)
        
        btn_opts = {"width": 10, "style": "Misa.TButton", "cursor": "hand2"}
        self.btn_template = ttk.Button(self.fr_buttons, text="📷 Ảnh Phôi", command=router.select_template, **btn_opts)
        self.btn_template.pack(side=LEFT, padx=2) 
        self.btn_excel = ttk.Button(self.fr_buttons, text="📊 Dữ Liệu", command=router.select_excel, **btn_opts)
        self.btn_excel.pack(side=LEFT, padx=2)
        self.btn_folder = ttk.Button(self.fr_buttons, text="📂 Chữ Ký", command=router.select_signature_folder, **btn_opts)
        self.btn_folder.pack(side=LEFT, padx=2)
        
        # --- 1.5. KHU VỰC NHẬP LIỆU CỐ ĐỊNH (STATIC INPUTS) ---
        # Container chứa 4 ô input luôn hiển thị
        self.fr_static_inputs = ttk.Frame(self, style='TFrame')
        self.fr_static_inputs.pack(fill=X, pady=(8, 5))
        
        # Khởi tạo 4 ô input ngay lập tức
        self._setup_static_inputs()

        # --- 2. CẤU HÌNH TRƯỜNG ---
        ttk.Label(self, text="2. CẤU HÌNH TRƯỜNG", style="Section.TLabel").pack(anchor="w", pady=(5, 0))
        
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

    def _setup_static_inputs(self):
        """
        Tạo 4 ô input cố định.
        ĐÃ FIX LỖI: Dữ liệu bị nhảy sang trường khác do lỗi Closure trong vòng lặp.
        """
        # Xóa các widget cũ
        for widget in self.fr_static_inputs.winfo_children():
            widget.destroy()
        
        self.static_entries.clear()
        self.static_frames.clear()

        # Kiểm tra dữ liệu Excel
        has_data = (self.router.model.df is not None and not self.router.model.df.empty)

        for field in STATIC_FIELDS_LIST:
            # Tạo Frame bao ngoài
            row_frame = ttk.Frame(self.fr_static_inputs, style='TFrame')
            row_frame.pack(fill=X, pady=2)
            self.static_frames[field] = row_frame

            # Lấy dữ liệu
            if has_data:
                current_val = self.router.model.global_config.get(field, {}).get("text", "")
            else:
                current_val = "" 
            
            placeholder_text = f"{field}..." 
            placeholder_color = "gray"
            normal_color = "black"

            # Entry Widget
            ent = ttk.Entry(row_frame, font=("Segoe UI", 9))
            ent.pack(fill=X, padx=1, pady=1) 
            ent.debounce_timer = None
            
            # --- CÁC HÀM XỬ LÝ SỰ KIỆN (ĐÃ SỬA LỖI) ---
            # Lưu ý: Phải dùng _f=field trong tham số để "đóng băng" giá trị field cho từng vòng lặp
            
            def on_focus_in(event, _ent=ent, _ph=placeholder_text, _norm=normal_color, _f=field):
                # Báo cho router biết: "Tôi đang click trực tiếp vào Input, đừng ép focus lại tôi nữa"
                self.router.select_field(_f, from_input=True) 
                
                content = _ent.get()
                current_color = str(_ent.cget("foreground"))
                if content == _ph and current_color == placeholder_color:
                    _ent.delete(0, "end")
                    _ent.configure(foreground=_norm)

            def on_focus_out(event, _ent=ent, _ph=placeholder_text, _gray=placeholder_color):
                content = _ent.get()
                if not content:
                    _ent.insert(0, _ph)
                    _ent.configure(foreground=_gray)

            # [FIX QUAN TRỌNG] Đưa logic update thẳng vào đây và dùng _f=field
            def on_key_release(event, _ent=ent, _f=field, _ph=placeholder_text, _gray=placeholder_color):
                val = _ent.get()
                current_color = str(_ent.cget("foreground"))
                
                if val == _ph and current_color == _gray: 
                    val = ""
                
                if _ent.debounce_timer: 
                    self.after_cancel(_ent.debounce_timer)
                
                # Gọi router với đúng tên trường _f
                _ent.debounce_timer = self.after(300, lambda: self.router.on_static_text_change(_f, val))

            # --- GÁN SỰ KIỆN ---
            ent.bind("<FocusIn>", on_focus_in)
            ent.bind("<FocusOut>", on_focus_out)
            ent.bind("<KeyRelease>", on_key_release)

            # --- KHỞI TẠO GIÁ TRỊ ---
            if current_val and current_val.strip() != "":
                ent.insert(0, current_val)
                ent.configure(foreground=normal_color)
            else:
                ent.insert(0, placeholder_text)
                ent.configure(foreground=placeholder_color)
                
            self.static_entries[field] = ent

    def highlight_selected_field(self, field_name, focus_input=False):
        """
        Highlight trường được chọn trong danh sách VÀ ô input tương ứng.
        focus_input=True: Tự động đặt trỏ chuột vào ô nhập liệu (dùng khi click từ danh sách).
        """
        
        # 1. Highlight trong danh sách bên dưới (List)
        for f, lbl in self.field_labels.items():
            content_fr = self.field_content_frames.get(f)
            if f == field_name:
                if content_fr: content_fr.configure(bg=LIST_SELECTED_BG) 
                lbl.configure(bg=LIST_SELECTED_BG, fg=MISA_WHITE, font=("Segoe UI", 7, "bold"))
            else:
                if content_fr: content_fr.configure(bg=LIST_ITEM_BG) 
                lbl.configure(bg=LIST_ITEM_BG, fg=MISA_TEXT_NORMAL, font=("Segoe UI", 7))
        
        # 2. Highlight ô Input tĩnh & Xử lý Focus
        for f, fr in self.static_frames.items():
            if f == field_name:
                # Đổi sang style Highlight (Nền xanh đậm)
                fr.configure(style='Highlight.TFrame') 
                
                # [LOGIC MỚI] Nếu yêu cầu focus và ô input tồn tại -> Focus ngay
                if focus_input and f in self.static_entries:
                    entry_widget = self.static_entries[f]
                    entry_widget.focus_set()       # Đặt focus vào ô
                    entry_widget.icursor("end")    # Đưa con trỏ về cuối dòng cho tiện
            else:
                fr.configure(style='TFrame')

    def refresh_field_list(self, cols, global_config):
        """Load danh sách vào khung cuộn bên dưới"""
        
        # --- CẬP NHẬT INPUT TĨNH ---
        # Gọi lại hàm setup để cập nhật trạng thái text (có/không có Excel)
        self._setup_static_inputs()
        # ---------------------------

        for widget in self.scroll_container.winfo_children():
            widget.destroy()
            
        self.field_vars = {}
        self.field_labels = {}
        self.field_content_frames = {} 
        
        # Gộp danh sách: Static lên đầu, Excel xuống dưới
        excel_cols = [c for c in cols if c not in STATIC_FIELDS_LIST]
        all_cols = STATIC_FIELDS_LIST + excel_cols
        
        if "signature_img" not in all_cols: all_cols.append("signature_img")
        
        for col in all_cols:
            row_fr = tk.Frame(self.scroll_container, bg=MISA_BG_COLOR)
            row_fr.pack(fill=X, pady=1, padx=2) 
            
            # Checkbox
            is_enabled = global_config.get(col, {}).get("enable", False)
            var = tk.BooleanVar(value=is_enabled)
            self.field_vars[col] = var
            
            chk = ttk.Checkbutton(row_fr, variable=var, style='Misa.TCheckbutton', command=lambda c=col: self.router.on_field_toggle(c))
            chk.pack(side=LEFT, padx=(5,0))
            
            # Content Frame
            content_fr = tk.Frame(row_fr, bg=LIST_ITEM_BG)
            content_fr.pack(side=LEFT, fill=BOTH, expand=YES, padx=(5, 0)) 
            self.field_content_frames[col] = content_fr
            
            display_text = col
            if col == "signature_img": display_text = "📷 ẢNH CHỮ KÝ"
            elif col in STATIC_FIELDS_LIST: display_text = f"✎ {col}"
            
            lbl = tk.Label(content_fr, text=display_text, padx=5, pady=4, 
                           bg=LIST_ITEM_BG, fg=MISA_TEXT_NORMAL, 
                           anchor="w", font=("Segoe UI", 7))
            lbl.pack(fill=BOTH, expand=YES)
            
            # Sự kiện Click chọn trường
            lbl.bind("<Button-1>", lambda e, c=col: self.router.select_field(c))
            content_fr.bind("<Button-1>", lambda e, c=col: self.router.select_field(c))
            
            self.field_labels[col] = lbl

    def _setup_license_ui(self):
        self.fr_license = ttk.Labelframe(self, text="Cập nhật mã sử dụng", padding=10, bootstyle="danger")
        self.fr_license.pack(side=BOTTOM, fill=X, pady=(10, 0))
        
        # --- Dòng 1: Mã máy ---
        ttk.Label(self.fr_license, text="Mã máy:", font=("Segoe UI", 7, "bold")).pack(anchor="w")
        r1 = ttk.Frame(self.fr_license, style='TFrame')
        r1.pack(fill=X, pady=2) 
        self.ent_hwid = ttk.Entry(r1, state="readonly", font=("Consolas", 7))
        self.ent_hwid.pack(side=LEFT, fill=X, expand=YES)
        
        # Nút Copy đang có width=3
        ttk.Button(r1, text="📋", width=3, style="Small.info.TButton", command=lambda: self.router.ctrl_license.on_copy_hwid()).pack(side=RIGHT, padx=(5, 0))
        
        # --- Dòng 2: Nhập key ---
        ttk.Label(self.fr_license, text="Nhập key:", font=("Segoe UI", 7,"bold")).pack(anchor="w", pady=(5,0))
        r2 = ttk.Frame(self.fr_license, style='TFrame')
        r2.pack(fill=X, pady=2)
        self.ent_key = ttk.Entry(r2, show="*", font=("Consolas", 7))
        self.ent_key.pack(side=LEFT, fill=X, expand=YES)
        
        # [SỬA TẠI ĐÂY] Thêm width=3 để kích thước bằng nút Copy phía trên
        self.btn_activate = ttk.Button(
            r2, 
            text="⚠", 
            width=3,  # <--- THÊM DÒNG NÀY
            style="Small.danger.TButton", 
            command=lambda: self.router.ctrl_license.on_activate()
        )
        self.btn_activate.pack(side=RIGHT, padx=(5,0))

    def _setup_footer(self):
        fr_footer = ttk.Labelframe(self, text="Thông tin liên hệ", padding=5)
        fr_footer.pack(side=BOTTOM, fill=X, pady=(10, 0))
        lbl_credit = ttk.Label(fr_footer, text=APP_CREDIT, font=("Segoe UI", 7, "bold", "italic"), foreground="#d35400", anchor="center")
        lbl_credit.pack(fill=X)
        lbl_support = ttk.Label(fr_footer, text=APP_SUPPORT, font=("Segoe UI", 7), foreground=MISA_TEXT_NORMAL, anchor="center")
        lbl_support.pack(fill=X)