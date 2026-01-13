import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config.settings import APP_BG_COLOR, APP_TEXT_COLOR

class MidPanelView(ttk.Frame):
    def __init__(self, parent, router):
        # --- CẤU HÌNH STYLE (GIỮ NGUYÊN) ---
        style = ttk.Style()
        style.configure('Misa.TFrame', background=APP_BG_COLOR)
        style.configure('Misa.TLabel', background=APP_BG_COLOR, foreground="#333333", font=("Segoe UI", 8))
        style.configure('MisaTotal.TLabel', background=APP_BG_COLOR, foreground="#333333", font=("Segoe UI", 8, "bold"))
        style.configure("Small.primary.Treeview", font=("Segoe UI", 8), rowheight=28)
        style.configure("Small.primary.Treeview.Heading", font=("Segoe UI", 8, "bold"))

        # Setup style phân trang
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

        super().__init__(parent, padding=5, style='Misa.TFrame')
        self.pack(fill=BOTH, expand=YES)
        self.parent = parent
        self.router = router
        
        # --- 1. TOOLBAR ---
        self._setup_toolbar()

        # --- 2. TABLE CONTAINER ---
        self.tree_container = ttk.Frame(self, style='Misa.TFrame')
        self.tree_container.pack(fill=BOTH, expand=YES, pady=5)
        self.tree_container.rowconfigure(0, weight=1)
        self.tree_container.columnconfigure(0, weight=1)

        # [SỬA LẠI]: Bỏ cột "stt" ảo, chỉ giữ 5 cột dữ liệu col0 -> col4
        # col0 sẽ đóng vai trò là cột STT của Excel (để width nhỏ = 40)
        # col1 sẽ là Họ tên (để width lớn = 150)
        self.cols_def = [
            ("col0", "STT", 20),   # Cột đầu tiên của Excel (Thường là STT)
            ("col1", "Họ và tên", 120),  # Cột thứ 2 (Thường là Tên)
            ("col2", "Ngày tháng năm sinh", 80), 
            ("col3", "Giới tính",  50),
            ("col4", "Số căn Cước", 80)
        ]
        
        self.tree = ttk.Treeview(
            self.tree_container, 
            columns=[c[0] for c in self.cols_def], 
            show="headings", 
            selectmode="extended",
            style="Small.primary.Treeview" 
        )
        
        # Khởi tạo Header
        for c_id, c_name, c_width in self.cols_def:
            # Cho phép click header để sort trên tất cả các cột
            self.tree.heading(c_id, text=c_name, command=lambda c=c_id: self.router.on_header_click(c))
            
            # Căn giữa cho cột đầu tiên (STT), còn lại căn trái
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
        # (Giữ nguyên phần Toolbar)
        from views.view_search import SearchView
        toolbar = ttk.Frame(self, style='Misa.TFrame')
        toolbar.pack(fill=X, pady=(0, 5)) 
        
        toolbar.columnconfigure(1, weight=1)
        toolbar.columnconfigure(0, weight=0)
        toolbar.columnconfigure(2, weight=0)

        # TRÁI
        container_left = ttk.Frame(toolbar, style='Misa.TFrame')
        container_left.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        # Combobox chọn cột
        self.cbb_filter = ttk.Combobox(
            container_left, 
            state="readonly", 
            bootstyle="info", 
            justify="left", 
            width=15,
            font=("Segoe UI", 7)
        ) 
        self.cbb_filter.pack(side=LEFT, padx=(0, 5))
        self.cbb_filter.set("Tất cả") 
        self.cbb_filter.bind("<<ComboboxSelected>>", self.router.on_filter_change)

        # Ô tìm kiếm
        self.search_view = SearchView(container_left, self.router)
        self.search_view.pack(side=LEFT, fill=X, expand=YES)


        # GIỮA
        # === 2. GROUP GIỮA (PHÂN TRANG) ===
        fr_page = ttk.Frame(toolbar, style='Misa.TFrame')
        fr_page.grid(row=0, column=1, sticky="e", padx=(0, 5))
        
        # Nút Prev
        self.btn_prev = ttk.Button(
            fr_page, 
            text="❮", 
            command=self.router.prev_page,
            width=4,
            style="Page.Custom.TButton"
        )
        self.btn_prev.pack(side=LEFT, padx=1)
        
        # Label 0/0
        self.lbl_page_info = ttk.Label(fr_page, text="0/0", width=8, anchor="center", 
                                       style='Misa.TLabel', font=("Segoe UI", 7, "bold"))
        self.lbl_page_info.pack(side=LEFT, padx=1)
        
        # Nút Next
        self.btn_next = ttk.Button(
            fr_page, 
            text="❯", 
            command=self.router.next_page, 
            width=4,
            style="Page.Custom.TButton"
        )
        self.btn_next.pack(side=LEFT, padx=(1,0))

        # PHẢI
        container_total = ttk.Frame(toolbar, style='Misa.TFrame')
        container_total.grid(row=0, column=2, sticky="e")
        ttk.Label(container_total, text="Tổng số:", style='Misa.TLabel').pack(side=LEFT)
        self.lbl_total_val = ttk.Label(container_total, text="0", style='MisaTotal.TLabel')
        self.lbl_total_val.pack(side=LEFT, padx=(5, 0))

    def update_pagination_label(self, current, total):
        self.lbl_page_info.config(text=f"{current} / {total}")
    
    def set_total_count(self, count):
        self.lbl_total_val.config(text=f"{count}")

    # =======================================================
    # [FIX] ĐÃ THÊM HÀM update_header_arrow ĐỂ SỬA LỖI
    # =======================================================
    def update_header_arrow(self, sort_col, reverse):
        """Cập nhật mũi tên chỉ thị sắp xếp trên Header"""
        for c_id in [c[0] for c in self.cols_def]:
            # Lấy text hiện tại
            try:
                current_text = self.tree.heading(c_id, "text")
                # Xóa mũi tên cũ (nếu có)
                clean_text = current_text.replace(" ▲", "").replace(" ▼", "")

                if c_id == sort_col:
                    arrow = " ▼" if reverse else " ▲"
                    self.tree.heading(c_id, text=clean_text + arrow)
                else:
                    self.tree.heading(c_id, text=clean_text)
            except:
                pass

    # =======================================================
    # HÀM UPDATE DATA (Đã có fix ngày tháng và 5 cột)
    # =======================================================
    def update_data(self, df, custom_configs):
        for i in self.tree.get_children(): 
            self.tree.delete(i)
            
        if df is None:
            self.lbl_placeholder.config(text="📂 Vui lòng chọn File Excel dữ liệu", bootstyle="secondary")
            self.lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")
            self.lbl_total_val.config(text="0") 
            return
            
        elif df.empty:
            self.lbl_placeholder.config(text="🔍 Không tìm thấy kết quả nào...", bootstyle="warning")
            self.lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")
            return
            
        else:
            self.lbl_placeholder.place_forget()
            
            # 1. Update Header theo tên cột Excel
            total_excel_cols = len(df.columns)
            limit = min(5, total_excel_cols)
            excel_headers = df.columns[:limit]
            
            for idx, header_text in enumerate(excel_headers):
                col_id = f"col{idx}" 
                self.tree.heading(col_id, text=str(header_text))

            for idx in range(limit, 5):
                self.tree.heading(f"col{idx}", text="")

            # 2. Đổ dữ liệu
            for i, row in df.iterrows():
                tag = ('custom',) if i in custom_configs else ()
                
                vals = []
                for k in range(5):
                    if k < total_excel_cols:
                        val = row.iloc[k]
                        
                        # Fix lỗi ngày tháng 00:00:00
                        str_val = str(val)
                        if " 00:00:00" in str_val:
                            str_val = str_val.replace(" 00:00:00", "")
                            
                        vals.append(str_val)
                    else:
                        vals.append("")
                
                self.tree.insert("", "end", iid=str(i), values=tuple(vals), tags=tag)