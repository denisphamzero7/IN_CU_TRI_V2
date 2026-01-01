# views/view_mid.py
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
# 1. Import hàm helper chuẩn của bạn
from helpers.ui_helpers import create_button 

class MidPanelView(ttk.Frame):
    def __init__(self, parent, router):
        super().__init__(parent, padding=10)
        self.pack(fill=BOTH, expand=YES)
        
        self.parent = parent
        self.router = router
        
        # --- 1. TOOLBAR ---
        self._setup_toolbar()

        # --- 2. TREEVIEW CONTAINER ---
        self.tree_container = ttk.Frame(self)
        self.tree_container.pack(fill=BOTH, expand=YES, pady=5)

        self.tree_container.rowconfigure(0, weight=1)
        self.tree_container.columnconfigure(0, weight=1)

        self.cols_def = [
            ("stt", "STT", 50), 
            ("name", "Họ và Tên", 200), 
            ("gender", "Giới", 70), 
            ("cccd", "CCCD/CMND", 120), 
            ("area", "Khu vực bỏ phiếu", 150)
        ]
        
        # Treeview vẫn giữ nguyên vì create_button chỉ dùng cho nút
        self.tree = ttk.Treeview(
            self.tree_container, 
            columns=[c[0] for c in self.cols_def], 
            show="headings", 
            selectmode="extended",
            bootstyle="primary"
        )
        
        for c_id, c_name, c_width in self.cols_def:
            if c_id in ["stt", "name"]:
                self.tree.heading(c_id, text=c_name, command=lambda c=c_id: router.on_header_click(c))
            else:
                self.tree.heading(c_id, text=c_name)
            
            anchor_val = "center" if c_id in ["stt", "gender"] else "w"
            self.tree.column(c_id, width=c_width, anchor=anchor_val)
            
        self.tree.tag_configure('custom', foreground='#e74c3c') 
        
        ysb = ttk.Scrollbar(self.tree_container, orient="vertical", command=self.tree.yview, bootstyle="round")
        xsb = ttk.Scrollbar(self.tree_container, orient="horizontal", command=self.tree.xview, bootstyle="round")
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        
        self.tree.bind("<<TreeviewSelect>>", router.on_user_select_change)

        # --- 3. FOOTER ---
        self.lbl_count = ttk.Label(self, text="Đã chọn: 0 người", font=("Segoe UI", 10, "italic"), bootstyle="danger")
        self.lbl_count.pack(fill=X, pady=(5, 0), anchor="e")

        self.lbl_placeholder = ttk.Label(
            self.tree, 
            text="📂 Vui lòng chọn File Excel dữ liệu", 
            font=("Segoe UI", 14, "italic"), 
            bootstyle="secondary"
        )
        self.lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")

    def _setup_toolbar(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=X, pady=(0, 10))
        
        # -- NHÓM TRÁI --
        # 2. SỬ DỤNG HÀM create_button
        # Code gọn hơn, dễ đọc hơn
        create_button(toolbar, "☑ Tất cả", self.router.select_all, style="primary-outline").pack(side=LEFT, padx=(0, 5))
        create_button(toolbar, "☐ Bỏ chọn", self.router.deselect_all, style="secondary-outline").pack(side=LEFT)
        
        ttk.Separator(toolbar, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=10)

        # Bộ lọc
        ttk.Label(toolbar, text="Khu vực:").pack(side=LEFT)
        self.cbb_filter = ttk.Combobox(toolbar, state="readonly", width=15)
        self.cbb_filter.pack(side=LEFT, padx=5)
        self.cbb_filter.bind("<<ComboboxSelected>>", self.router.on_filter_change)

        ttk.Separator(toolbar, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=10)

        # Phân trang
        create_button(toolbar, "❮", self.router.prev_page, style="secondary-outline", width=3).pack(side=LEFT)
        
        self.lbl_page_info = ttk.Label(toolbar, text="0 / 0", width=10, anchor="center", font=("Segoe UI", 9, "bold"))
        self.lbl_page_info.pack(side=LEFT, padx=5)
        
        create_button(toolbar, "❯", self.router.next_page, style="secondary-outline", width=3).pack(side=LEFT)

        # -- NHÓM PHẢI (Nút IN) --
        # Nút IN dùng style="danger"
        create_button(toolbar, "🖨️ IN NGAY", self.router.start_print, style="danger", width=15).pack(side=RIGHT)

    # ... (Các hàm update_pagination_label, update_data, update_header_arrow giữ nguyên) ...
    def update_pagination_label(self, current, total):
        self.lbl_page_info.config(text=f"{current} / {total}")

    def update_data(self, df, custom_configs):
        for i in self.tree.get_children(): 
            self.tree.delete(i)
        if df is None or df.empty:
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