import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from helpers.ui_helpers import create_button 

class MidPanelView(ttk.Frame):
    def __init__(self, parent, router):
        super().__init__(parent, padding=10)
        self.pack(fill=BOTH, expand=YES)
        
        self.parent = parent
        self.router = router
        
        # --- 1. TOOLBAR (SỬ DỤNG GRID LAYOUT) ---
        self._setup_toolbar()

        # --- 2. TREEVIEW CONTAINER ---
        self.tree_container = ttk.Frame(self)
        self.tree_container.pack(fill=BOTH, expand=YES, pady=5)

        self.tree_container.rowconfigure(0, weight=1)
        self.tree_container.columnconfigure(0, weight=1)

        self.cols_def = [
            ("stt", "STT", 40), 
            ("name", "Họ và Tên", 180), 
            ("gender", "Giới", 60), 
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
        # Tạo Container chính cho toolbar
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=X, pady=(0, 10))
        
        # --- CẤU HÌNH LƯỚI (GRID CONFIGURATION) ---
        # Cột 4 (Bộ lọc) sẽ có weight=1 để tự động co giãn chiếm chỗ trống
        # Các cột khác sẽ giữ nguyên kích thước
        toolbar.columnconfigure(4, weight=1) 

        # --- CỘT 0: NHÓM CHỌN ---
        fr_select = ttk.Frame(toolbar)
        fr_select.grid(row=0, column=0, sticky="w", padx=(0, 5))
        
        # Bỏ width cứng, dùng padding nội bộ (ipadx) để nút tự đẹp
        create_button(fr_select, "☑ Tất cả", self.router.select_all, style="primary-outline").pack(side=LEFT, padx=(0, 2))
        create_button(fr_select, "☐ Bỏ", self.router.deselect_all, style="secondary-outline").pack(side=LEFT)

        # --- CỘT 1: VÁCH NGĂN ---
        ttk.Separator(toolbar, orient=VERTICAL).grid(row=0, column=1, sticky="ns", padx=5)

        # --- CỘT 2: CẤU HÌNH GIẤY ---
        fr_config = ttk.Frame(toolbar)
        fr_config.grid(row=0, column=2, sticky="w", padx=5)

        ttk.Label(fr_config, text="Khổ:").pack(side=LEFT)
        self.var_paper_size = tk.StringVar(value="A4")
        self.cbb_paper_size = ttk.Combobox(
            fr_config, 
            textvariable=self.var_paper_size,
            values=["A4", "A5", "A6"], 
            width=3, # Nhỏ gọn
            state="readonly",
            bootstyle="warning"
        )
        self.cbb_paper_size.pack(side=LEFT, padx=(2, 5))
        self.cbb_paper_size.bind("<<ComboboxSelected>>", self.router.on_paper_config_change)

        # Nút Xoay Ảnh (Đặt ngay đây cho gọn)
        create_button(
            fr_config, 
            "↻ Xoay", 
            self.router.rotate_template_right, 
            style="info-outline"
        ).pack(side=LEFT, padx=0)

        # --- CỘT 3: VÁCH NGĂN ---
        ttk.Separator(toolbar, orient=VERTICAL).grid(row=0, column=3, sticky="ns", padx=5)

        # --- CỘT 4: BỘ LỌC (CO GIÃN LINH HOẠT) ---
        # sticky="ew" giúp combobox kéo dài ra hết mức có thể
        self.cbb_filter = ttk.Combobox(toolbar, state="readonly") 
        self.cbb_filter.grid(row=0, column=4, sticky="ew", padx=5)
        self.cbb_filter.set("Lọc theo khu vực...") 
        self.cbb_filter.bind("<<ComboboxSelected>>", self.router.on_filter_change)

        # --- CỘT 5: VÁCH NGĂN ---
        ttk.Separator(toolbar, orient=VERTICAL).grid(row=0, column=5, sticky="ns", padx=5)

        # --- CỘT 6: PHÂN TRANG ---
        fr_page = ttk.Frame(toolbar)
        fr_page.grid(row=0, column=6, sticky="e", padx=5)

        create_button(fr_page, "❮", self.router.prev_page, style="secondary-outline", width=2).pack(side=LEFT)
        self.lbl_page_info = ttk.Label(fr_page, text="0/0", width=8, anchor="center", font=("Segoe UI", 9, "bold"))
        self.lbl_page_info.pack(side=LEFT)
        create_button(fr_page, "❯", self.router.next_page, style="secondary-outline", width=2).pack(side=LEFT)

        # --- CỘT 7: NÚT IN (LUÔN HIỆN Ở CÙNG BÊN PHẢI) ---
        # Nút In quan trọng nên để riêng, không bị các nút khác chen lấn
        self.btn_print = create_button(toolbar, "🖨️ IN NGAY", self.router.start_print, style="danger")
        self.btn_print.grid(row=0, column=7, sticky="e", padx=(5, 0))

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