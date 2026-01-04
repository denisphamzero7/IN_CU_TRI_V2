import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from helpers.ui_helpers import create_button 
from views.view_search import SearchView

class MidPanelView(ttk.Frame):
    def __init__(self, parent, router):
        super().__init__(parent, padding=10)
        self.pack(fill=BOTH, expand=YES)
        self.parent = parent
        self.router = router
        
        # --- 1. TOOLBAR ---
        self._setup_toolbar()

        # --- 2. TREEVIEW ---
        self.tree_container = ttk.Frame(self)
        self.tree_container.pack(fill=BOTH, expand=YES, pady=5)
        self.tree_container.rowconfigure(0, weight=1)
        self.tree_container.columnconfigure(0, weight=1)

        self.cols_def = [
            ("stt", "STT", 40), 
            ("name", "Họ và Tên", 180), 
            ("gender", "Giới Tính", 60), 
            ("cccd", "CCCD/CMND", 110), 
            ("area", "Khu vực bỏ phiếu", 150)
        ]
        
        self.tree = ttk.Treeview(
            self.tree_container, 
            columns=[c[0] for c in self.cols_def], 
            show="headings", 
            selectmode="extended",
            bootstyle="primary"
        )
        
        # --- GẮN SỰ KIỆN CLICK HEADER (GIỮ NGUYÊN TỪ CODE CŨ) ---
        for c_id, c_name, c_width in self.cols_def:
            if c_id in ["stt", "name"]:
                # Click vào tiêu đề để gọi hàm sắp xếp bên Router
                self.tree.heading(c_id, text=c_name, command=lambda c=c_id: router.on_header_click(c))
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
            text="", 
            font=("Segoe UI", 12, "italic"),
            justify="center",
            anchor="center"
        )

    def _setup_toolbar(self):
        # --- TOOLBAR CŨ (KHÔNG CÓ NÚT SẮP XẾP) ---
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=X, pady=(0, 10))
        
        # Grid 4 Cột: Filter | Search | Page | Total
        toolbar.columnconfigure(0, weight=0)
        toolbar.columnconfigure(1, weight=1) # Search giãn ra
        toolbar.columnconfigure(2, weight=0)
        toolbar.columnconfigure(3, weight=0)

        # 1. COL 0: BỘ LỌC
        container_filter = ttk.Frame(toolbar)
        container_filter.grid(row=0, column=0, sticky="w", padx=(0, 10))
        
        ttk.Label(container_filter, font=("Segoe UI", 9)).pack(side=LEFT, padx=(0, 5))
        
        self.cbb_filter = ttk.Combobox(container_filter, state="readonly", justify="left", width=15) 
        self.cbb_filter.pack(side=LEFT)
        self.cbb_filter.set("Chưa chọn khu vực") 
        self.cbb_filter.bind("<<ComboboxSelected>>", self.router.on_filter_change)

        # 2. COL 1: SEARCH
        self.search_view = SearchView(toolbar, self.router)
        self.search_view.grid(row=0, column=1, sticky="ew", padx=(0, 10))

        # 3. COL 2: PHÂN TRANG
        fr_page = ttk.Frame(toolbar)
        fr_page.grid(row=0, column=2, sticky="e", padx=(0, 10))
        
        create_button(fr_page, "❮", self.router.prev_page, style="secondary-outline", width=3).pack(side=LEFT)
        self.lbl_page_info = ttk.Label(fr_page, text="0/0", width=8, anchor="center", font=("Segoe UI", 9, "bold"))
        self.lbl_page_info.pack(side=LEFT, padx=2)
        create_button(fr_page, "❯", self.router.next_page, style="secondary-outline", width=3).pack(side=LEFT)

        # 4. COL 3: TỔNG SỐ
        container_total = ttk.Frame(toolbar)
        container_total.grid(row=0, column=3, sticky="e")
        
        ttk.Label(container_total, text="Tổng số:", font=("Segoe UI", 9)).pack(side=LEFT)
        self.lbl_total_val = ttk.Label(container_total, text="0", font=("Segoe UI", 9, "bold"), bootstyle="primary")
        self.lbl_total_val.pack(side=LEFT, padx=(5, 0))

    def update_pagination_label(self, current, total):
        self.lbl_page_info.config(text=f"{current} / {total}")

    def update_data(self, df, custom_configs):
        for i in self.tree.get_children(): 
            self.tree.delete(i)
            
        if df is None:
            self.lbl_placeholder.config(
                text="📂 Vui lòng chọn File Excel dữ liệu",
                bootstyle="secondary",
                font=("Segoe UI", 14, "italic")
            )
            self.lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")
            self.lbl_total_val.config(text="0")
            return
            
        elif df.empty:
            self.lbl_placeholder.config(
                text="🔍 Không tìm thấy người nào trong danh sách.\nVui lòng kiểm tra lại từ khóa hoặc bộ lọc!",
                bootstyle="warning",
                font=("Segoe UI", 13)
            )
            self.lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")
            self.lbl_total_val.config(text="0")
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