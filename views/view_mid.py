import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config.settings import APP_BG_COLOR, APP_TEXT_COLOR

from helpers.date_helpers import format_date_text_vn
from helpers.text_helper import format_cccd

class MidPanelView(ttk.Frame):
    def __init__(self, parent, router):
        # --- CẤU HÌNH STYLE ---
        super().__init__(parent, padding=5, style='Misa.TFrame')
        self.parent = parent
        self.router = router
        
        style = ttk.Style()
        style.configure('Misa.TFrame', background=APP_BG_COLOR)
        style.configure('Misa.TLabel', background=APP_BG_COLOR, foreground="#333333", font=("Segoe UI", 8))
        style.configure('MisaTotal.TLabel', background=APP_BG_COLOR, foreground="#333333", font=("Segoe UI", 8, "bold"))
        style.configure("Small.primary.Treeview", font=("Segoe UI", 8), rowheight=28)
        style.configure("Small.primary.Treeview.Heading", font=("Segoe UI", 8, "bold"))
        
        # Font cho Listbox của Combobox
        self.option_add('*TCombobox*Listbox.font', ("Segoe UI", 8))
        
        # Setup style phân trang (Page Button)
        BTN_BG_COLOR = "#FFFFFF"
        BTN_FG_COLOR = "#888888"
        BTN_BORDER   = "#CCCCCC"
        style.configure('Page.Custom.TButton', font=("Segoe UI", 8), padding=(4, 2), borderwidth=1, relief="solid",
                        background=BTN_BG_COLOR, foreground=BTN_FG_COLOR, bordercolor=BTN_BORDER,
                        lightcolor=BTN_BG_COLOR, darkcolor=BTN_BG_COLOR, focuscolor=BTN_BG_COLOR, focusthickness=0)
        style.map('Page.Custom.TButton',
                  bordercolor=[('active', '#999999'), ('!disabled', BTN_BORDER)],
                  foreground=[('active', '#333333'), ('!disabled', BTN_FG_COLOR)],
                  background=[('pressed', '#f2f2f2'), ('active', BTN_BG_COLOR), ('!disabled', BTN_BG_COLOR)],
                  focuscolor=[('active', BTN_BG_COLOR), ('!disabled', BTN_BG_COLOR)])

        style.configure('Small.TCombobox', font=("Segoe UI", 9))
        style.configure('TEntry', font=("Segoe UI", 9))
        
        self.pack(fill=BOTH, expand=YES)
        
        # --- 1. TOOLBAR ---
        self._setup_toolbar()

        # --- 2. TABLE CONTAINER ---
        self.tree_container = ttk.Frame(self, style='Misa.TFrame')
        self.tree_container.pack(fill=BOTH, expand=YES, pady=5)
        self.tree_container.rowconfigure(0, weight=1)
        self.tree_container.columnconfigure(0, weight=1)

        # Định nghĩa 5 cột hiển thị
        self.cols_def = [
            ("col0", "", 20),   # STT
            ("col1", "", 90),   # Họ tên
            ("col2", "", 80),   # Ngày sinh (Dự kiến)
            ("col3", "",  50),  # Giới tính (Dự kiến)
            ("col4", "", 80)    # CCCD (Dự kiến)
        ]
        
        self.tree = ttk.Treeview(
            self.tree_container, 
            columns=[c[0] for c in self.cols_def], 
            show="headings", 
            selectmode="extended",
            style="Small.primary.Treeview" 
        )
        
        # Chỉ cho phép click sort cột STT và Tên
        allowed_sort_cols = ["col0", "col1"]
        for c_id, c_name, c_width in self.cols_def:
            if c_id in allowed_sort_cols:
                self.tree.heading(c_id, text=c_name, command=lambda c=c_id: self.router.on_header_click(c))
            else:
                self.tree.heading(c_id, text=c_name)
            
            anchor_val = "center" if c_id == "col0" else "w"
            self.tree.column(c_id, width=c_width, anchor=anchor_val)
            
        self.tree.tag_configure('custom', foreground='#e74c3c') 
        
        ysb = ttk.Scrollbar(self.tree_container, orient="vertical", command=self.tree.yview, bootstyle="round")
        self.tree.configure(yscrollcommand=ysb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        
        self.tree.bind("<<TreeviewSelect>>", router.on_user_select_change)
        self.tree.bind("<Button-1>", router.on_tree_left_click)

        # --- 3. Placeholder ---
        self.lbl_placeholder = ttk.Label(
            self.tree, 
            text="📂 Vui lòng chọn File Excel dữ liệu", 
            font=("Segoe UI", 10, "italic"),
            bootstyle="secondary",
            justify="center",
            anchor="center"
        )
        self.lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")

    def _setup_toolbar(self):
        from views.view_search import SearchView
        
        toolbar_container = ttk.Frame(self, style='Misa.TFrame')
        toolbar_container.pack(fill=X, pady=(0, 5))

        # =========================================================
        # HÀNG 1: [CỘT] + [TÌM KIẾM] + [PHÂN TRANG]
        # =========================================================
        row_top = ttk.Frame(toolbar_container, style='Misa.TFrame')
        row_top.pack(fill=X, pady=(0, 5))

        # 1. CỘT
        self.cbb_filter = ttk.Combobox(row_top, state="readonly", bootstyle="info", width=10, font=("Segoe UI", 7)) 
        self.cbb_filter.pack(side=LEFT, padx=(0, 5))
        self.cbb_filter.set("Tất cả") 
        self.cbb_filter.bind("<<ComboboxSelected>>", self.router.on_filter_change)

        # 2. Ô TÌM KIẾM
        self.search_view = SearchView(row_top, self.router)
        self.search_view.pack(side=LEFT, fill=X, expand=YES, padx=(5, 0))

        # 3. PHÂN TRANG
        fr_right = ttk.Frame(row_top, style='Misa.TFrame')
        fr_right.pack(side=RIGHT, padx=(10, 0))
        
        self.btn_prev = ttk.Button(fr_right, text="❮", command=self.router.prev_page, width=4, style="Page.Custom.TButton")
        self.btn_prev.pack(side=LEFT, padx=1)
        self.lbl_page_info = ttk.Label(fr_right, text="0/0", width=8, anchor="center", style='Misa.TLabel', font=("Segoe UI", 7, "bold"))
        self.lbl_page_info.pack(side=LEFT, padx=1)
        self.btn_next = ttk.Button(fr_right, text="❯", command=self.router.next_page, width=4, style="Page.Custom.TButton")
        self.btn_next.pack(side=LEFT, padx=(1, 10))
        ttk.Label(fr_right, text="Tổng:", style='Misa.TLabel').pack(side=LEFT)
        self.lbl_total_val = ttk.Label(fr_right, text="0", style='MisaTotal.TLabel')
        self.lbl_total_val.pack(side=LEFT, padx=(5, 0))

        # =========================================================
        # HÀNG 2: [LỌC NGÀY SINH] + [LỌC CCCD]
        # =========================================================
        row_bottom = ttk.Frame(toolbar_container, style='Misa.TFrame')
        row_bottom.pack(fill=X)

        # 1. Combobox Ngày sinh
        self.cbb_date = ttk.Combobox(row_bottom, state="readonly", bootstyle="info", width=25, font=("Segoe UI", 7))
        self.cbb_date.pack(side=LEFT, padx=(0, 15))
        self.cbb_date.set("") 
        # Sự kiện này cần có trong Router
        if hasattr(self.router, 'on_date_filter_change'):
            self.cbb_date.bind("<<ComboboxSelected>>", self.router.on_date_filter_change)

        # 2. Combobox CCCD
        self.cbb_cccd = ttk.Combobox(row_bottom, state="readonly", bootstyle="info", width=25, font=("Segoe UI", 7))
        self.cbb_cccd.pack(side=LEFT)
        self.cbb_cccd.set("") 
        # Sự kiện này cần có trong Router
        if hasattr(self.router, 'on_cccd_filter_change'):
            self.cbb_cccd.bind("<<ComboboxSelected>>", self.router.on_cccd_filter_change)

    def update_pagination_label(self, current, total):
        self.lbl_page_info.config(text=f"{current} / {total}")
    
    def set_total_count(self, count):
        self.lbl_total_val.config(text=f"{count}")

    def update_header_arrow(self, sort_col, reverse):
        """Cập nhật mũi tên sort"""
        for c_id in [c[0] for c in self.cols_def]:
            try:
                current_text = self.tree.heading(c_id, "text")
                clean_text = current_text.replace(" ▲", "").replace(" ▼", "")
                if c_id == sort_col:
                    arrow = " ▼" if reverse else " ▲"
                    self.tree.heading(c_id, text=clean_text + arrow)
                else:
                    self.tree.heading(c_id, text=clean_text)
            except: pass

    # =======================================================
    # HÀM UPDATE DATA THÔNG MINH (KHÔNG SET CỨNG VỊ TRÍ)
    # =======================================================
    def update_data(self, df, custom_configs):
        # 1. Xóa dữ liệu cũ
        for i in self.tree.get_children(): self.tree.delete(i)
            
        if df is None:
            self.lbl_placeholder.config(text="📂 Vui lòng chọn File Excel dữ liệu", bootstyle="secondary")
            self.lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")
            self.lbl_total_val.config(text="0") 
            return
        elif df.empty:
            self.lbl_placeholder.config(text="🔍 Không tìm thấy kết quả nào...", bootstyle="warning")
            self.lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")
            # Vẫn cho hiện 0 kết quả
            self.lbl_total_val.config(text="0")
            return
        else:
            self.lbl_placeholder.place_forget()
            
            # --- [LOGIC MỚI] LẤY TÊN CỘT ĐÃ DETECT TỪ MODEL ---
            # Model phải có biến detected_cols = {'date': 'Ngày sinh', 'cccd': 'Số CCCD'}
            detected = getattr(self.router.model, 'detected_cols', {})
            col_date_name = detected.get("date")
            col_cccd_name = detected.get("cccd")
            # --------------------------------------------------

            # 2. Update Header Table
            total_excel_cols = len(df.columns)
            limit = min(5, total_excel_cols) # Chỉ hiện tối đa 5 cột
            excel_headers = df.columns[:limit]
            
            for idx, header_text in enumerate(excel_headers):
                self.tree.heading(f"col{idx}", text=str(header_text))
            
            # Xóa text các cột thừa (nếu file < 5 cột)
            for idx in range(limit, 5):
                self.tree.heading(f"col{idx}", text="")

            # 3. Đổ dữ liệu
            for i, row in df.iterrows():
                tag = ('custom',) if i in custom_configs else ()
                vals = []
                
                # Duyệt qua 5 cột hiển thị
                for k in range(5):
                    if k < total_excel_cols:
                        val = row.iloc[k]
                        col_name_real = df.columns[k] # Lấy tên cột thực tế trong Excel
                        
                        val_str = str(val)
                        if val_str.lower() == "nan": val_str = ""

                        # --- FORMAT DỰA TRÊN TÊN CỘT ---
                        if col_name_real == col_date_name:
                             # Format nếu cột này trùng tên với cột Ngày sinh đã detect
                             val_str = format_date_text_vn(val)
                        
                        elif col_name_real == col_cccd_name:
                             # Format nếu cột này trùng tên với cột CCCD đã detect
                             val_str = format_cccd(val)
                        # -------------------------------
                        
                        vals.append(val_str)
                    else:
                        vals.append("")
                
                self.tree.insert("", "end", iid=str(i), values=tuple(vals), tags=tag)