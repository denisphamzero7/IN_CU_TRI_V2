import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from config.settings import APP_BG_COLOR, APP_TEXT_COLOR

class MidPanelView(ttk.Frame):
    def __init__(self, parent, router):
        # --- CẤU HÌNH STYLE ---
        style = ttk.Style()
        style.configure('Misa.TFrame', background=APP_BG_COLOR)
        
        # 1. Label
        style.configure('Misa.TLabel', background=APP_BG_COLOR, foreground="#333333", font=("Segoe UI", 7))
        style.configure('MisaTotal.TLabel', background=APP_BG_COLOR, foreground="#333333", font=("Segoe UI", 7, "bold"))

        # 2. Treeview
        style.configure("Small.primary.Treeview", font=("Segoe UI", 7), rowheight=22)
        style.configure("Small.primary.Treeview.Heading", font=("Segoe UI", 7, "bold"))

        # =========================================================================
        # [FIX] STYLE PHÂN TRANG: KHỬ SẠCH MÀU XANH (BLUE)
        # =========================================================================
        BTN_BG_COLOR = "#FFFFFF"   # Nền Trắng
        BTN_FG_COLOR = "#888888"   # Chữ Xám
        BTN_BORDER   = "#CCCCCC"   # Viền Xám nhạt

        style.configure('Page.Custom.TButton', 
                        font=("Segoe UI", 7), 
                        padding=(2, 0),
                        borderwidth=1,
                        relief="solid",            # [QUAN TRỌNG] Ép kiểu viền đơn để ăn màu bordercolor
                        background=BTN_BG_COLOR,
                        foreground=BTN_FG_COLOR,
                        
                        # [CỰC KỲ QUAN TRỌNG ĐỂ KHỬ XANH]
                        bordercolor=BTN_BORDER,    # Màu viền tĩnh
                        lightcolor=BTN_BG_COLOR,   # Khử highlight 3D (thường bị dính màu xanh)
                        darkcolor=BTN_BG_COLOR,    # Khử shadow 3D
                        focuscolor=BTN_BG_COLOR,   # Khử viền xanh khi nút đang được chọn (focus)
                        focusthickness=0           # Tắt độ dày viền focus
        )

        style.map('Page.Custom.TButton',
                  # 1. Viền: Hover thì đậm hơn
                  bordercolor=[('active', '#999999'), ('!disabled', BTN_BORDER)],
                  
                  # 2. Chữ: Hover thì đen
                  foreground=[('active', '#333333'), ('!disabled', BTN_FG_COLOR)],
                  
                  # 3. Nền: Click (pressed) thì xám nhẹ
                  background=[('pressed', '#f2f2f2'), ('active', BTN_BG_COLOR), ('!disabled', BTN_BG_COLOR)],
                  
                  # 4. Focus: Đảm bảo khi click xong không bị nhảy về màu xanh
                  focuscolor=[('active', BTN_BG_COLOR), ('!disabled', BTN_BG_COLOR)] 
        )

        # 3. Combobox & Entry
        style.configure('Small.TCombobox', font=("Segoe UI", 2))
        style.configure('TEntry', font=("Segoe UI", 2))

        # Khởi tạo Frame
        super().__init__(parent, padding=5, style='Misa.TFrame')
        self.pack(fill=BOTH, expand=YES)
        
        self.parent = parent
        self.router = router
        
        # --- 1. TOOLBAR ---
        self._setup_toolbar()

        # ... (Phần còn lại giữ nguyên không đổi) ...
        self.tree_container = ttk.Frame(self, style='Misa.TFrame')
        self.tree_container.pack(fill=BOTH, expand=YES, pady=5)
        self.tree_container.rowconfigure(0, weight=1)
        self.tree_container.columnconfigure(0, weight=1)

        self.cols_def = [
            ("stt", "STT", 30), 
            ("name", "Họ và Tên", 120), 
            ("gender", "Giới Tính", 50), 
            ("cccd", "CCCD/CMND", 100), 
            ("area", "Khu vực bỏ phiếu", 100)
        ]
        
        self.tree = ttk.Treeview(
            self.tree_container, 
            columns=[c[0] for c in self.cols_def], 
            show="headings", 
            selectmode="extended",
            style="Small.primary.Treeview" 
        )
        
        for c_id, c_name, c_width in self.cols_def:
            if c_id in ["stt", "name"]:
                self.tree.heading(c_id, text=c_name, command=lambda c=c_id: self.router.on_header_click(c))
            else:
                self.tree.heading(c_id, text=c_name)
            
            anchor_val = "center" if c_id in ["stt", "gender"] else "w"
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
            font=("Segoe UI", 7, "italic"),
            bootstyle="secondary",
            justify="center",
            anchor="center"
        )
        self.lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")

    def _setup_toolbar(self):
        from views.view_search import SearchView

        toolbar = ttk.Frame(self, style='Misa.TFrame')
        toolbar.pack(fill=X, pady=(0, 5)) 
        
        toolbar.columnconfigure(1, weight=1)
        toolbar.columnconfigure(0, weight=0)
        toolbar.columnconfigure(2, weight=0)

        # === 1. GROUP TRÁI ===
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

        # === 3. GROUP PHẢI ===
        container_total = ttk.Frame(toolbar, style='Misa.TFrame')
        container_total.grid(row=0, column=2, sticky="e")
        
        ttk.Label(container_total, text="Tổng số:", style='Misa.TLabel').pack(side=LEFT)
        self.lbl_total_val = ttk.Label(container_total, text="0", style='MisaTotal.TLabel')
        self.lbl_total_val.pack(side=LEFT, padx=(5, 0))

    # ... (Giữ nguyên các hàm update) ...
    def update_pagination_label(self, current, total):
        self.lbl_page_info.config(text=f"{current} / {total}")

    def update_data(self, df, custom_configs):
        for i in self.tree.get_children(): 
            self.tree.delete(i)
            
        if df is None:
            self.lbl_placeholder.config(text="📂 Vui lòng chọn File Excel dữ liệu", bootstyle="secondary", font=("Segoe UI", 7, "italic"))
            self.lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")
            self.lbl_total_val.config(text="0") 
            return
            
        elif df.empty:
            self.lbl_placeholder.config(text="🔍 Không tìm thấy kết quả nào...", bootstyle="warning", font=("Segoe UI", 7))
            self.lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")
            return
            
        else:
            self.lbl_placeholder.place_forget()
            
            def find_col(keywords):
                for col in df.columns:
                    for kw in keywords:
                        if kw.lower() in col.lower(): return col
                return None

            col_name = find_col(["Họ tên", "Họ và tên", "Name"])
            col_gender = find_col(["Giới tính", "Gender"])
            col_cccd = find_col(["CCCD", "CMND"])
            col_area = find_col(["Khu vực", "Thôn"])
            if not col_name and len(df.columns) > 1: col_name = df.columns[1]

            for i, row in df.iterrows():
                tag = ('custom',) if i in custom_configs else ()
                vals = (i + 1, row.get(col_name, ""), row.get(col_gender, ""), row.get(col_cccd, ""), row.get(col_area, ""))
                self.tree.insert("", "end", iid=str(i), values=vals, tags=tag)

    def update_header_arrow(self, sort_col, reverse):
        arrow = " ▼" if reverse else " ▲"
        for c_id, c_name, _ in self.cols_def:
            if c_id == sort_col: 
                self.tree.heading(c_id, text=f"{c_name}{arrow}")
            else: 
                self.tree.heading(c_id, text=c_name)

    def set_total_count(self, count):
        self.lbl_total_val.config(text=f"{count}")