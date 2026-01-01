# views/view_mid.py
import tkinter as tk
from tkinter import ttk
from config.settings import COLORS
from helpers.ui_helpers import RoundedButton

class MidPanelView:
    def __init__(self, parent, router):
        self.parent = parent
        self.router = router
        
        # --- 1. TOOLBAR (Thanh công cụ) ---
        # Tăng pady để thanh công cụ cao hơn, thoáng hơn
        # bg="#f8f9fa": Màu xám rất nhạt làm nền cho sang trọng
        toolbar_frame = tk.Frame(parent, bg="#f8f9fa", height=50) 
        toolbar_frame.pack(side=tk.TOP, fill=tk.X, pady=0)
        toolbar_frame.pack_propagate(False) # Giữ chiều cao cố định 50px

        # --- CONTAINER CHÍNH (Dùng pack đệm để căn giữa dọc) ---
        # Một frame con nằm giữa toolbar_frame để chứa các nút
        content_frame = tk.Frame(toolbar_frame, bg="#f8f9fa")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8) # pady=8 để căn giữa theo chiều dọc

        # --- NHÓM PHẢI (Nút IN - Quan trọng nhất) ---
        right_box = tk.Frame(content_frame, bg="#f8f9fa")
        right_box.pack(side=tk.RIGHT)
        
        # Nút IN to và nổi bật
        RoundedButton(right_box, text="🖨️ IN NGAY", command=router.start_print, 
                      bg=COLORS["danger"], fg="white", width=100, height=34, radius=10, 
                      font=("Segoe UI", 10, "bold")).pack()

        # --- NHÓM TRÁI (Các công cụ khác) ---
        left_box = tk.Frame(content_frame, bg="#f8f9fa")
        left_box.pack(side=tk.LEFT, fill=tk.X)

        # 1. Chọn / Bỏ chọn (Màu xanh nhẹ nhàng)
        RoundedButton(left_box, text="☑ Tất cả", command=router.select_all, 
                      bg="#3498db", fg="white", width=70, height=30, radius=8, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=(0, 5))
        
        RoundedButton(left_box, text="☐ Bỏ chọn", command=router.deselect_all, 
                      bg="#bdc3c7", fg="#2c3e50", width=70, height=30, radius=8, font=("Segoe UI", 9)).pack(side=tk.LEFT)

        # Vách ngăn dọc
        tk.Label(left_box, text="|", bg="#f8f9fa", fg="#bdc3c7", font=("Arial", 14)).pack(side=tk.LEFT, padx=10)

        # 2. Bộ lọc (Dùng Label icon)
        tk.Label(left_box, text="Khu vực:", bg="#f8f9fa", fg="#7f8c8d", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        
        self.cbb_filter = ttk.Combobox(left_box, state="readonly", width=15, font=("Segoe UI", 9))
        self.cbb_filter.pack(side=tk.LEFT, padx=5)
        self.cbb_filter.bind("<<ComboboxSelected>>", router.on_filter_change)

        # Vách ngăn dọc
        tk.Label(left_box, text="|", bg="#f8f9fa", fg="#bdc3c7", font=("Arial", 14)).pack(side=tk.LEFT, padx=10)

        # 3. Phân trang (Thiết kế tối giản)
        # Nút Previous
        RoundedButton(left_box, text="❮", command=router.prev_page,
                      bg="white", fg="#2c3e50", width=28, height=28, radius=14, # Radius 14 -> Hình tròn
                      font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        self.lbl_page_info = tk.Label(left_box, text="0 / 0", font=("Segoe UI", 9, "bold"), bg="#f8f9fa", width=8, fg="#34495e")
        self.lbl_page_info.pack(side=tk.LEFT, padx=2)

        # Nút Next
        RoundedButton(left_box, text="❯", command=router.next_page,
                      bg="white", fg="#2c3e50", width=28, height=28, radius=14, 
                      font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        # --- Label đếm tổng số (Đưa xuống dưới treeview hoặc góc phải dưới toolbar) ---
        # (Ở đây mình giữ nguyên vị trí cũ nhưng chỉnh màu cho đẹp)
        self.lbl_count = tk.Label(parent, text="Đã chọn: 0 người", font=("Segoe UI", 10, "italic"), 
                                  fg=COLORS["danger"], bg="white", anchor="e")
        self.lbl_count.pack(fill=tk.X, padx=10, pady=(5, 0))

        # --- 2. Treeview Container (Giữ nguyên logic cũ) ---
        tree_container = tk.Frame(parent, bg="white")
        tree_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5) # Thêm padding viền cho bảng đỡ dính sát

        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        # ... (Phần cols_def và Treeview code y hệt cũ, copy lại vào đây) ...
        self.cols_def = [
            ("stt", "STT", 45), 
            ("name", "Họ và Tên", 180), 
            ("gender", "Giới", 60), 
            ("cccd", "CCCD/CMND", 100), 
            ("area", "Khu vực bỏ phiếu", 120)
        ]
        
        # Style cho Treeview Header (Cần chỉnh trong main.py hoặc settings, nhưng ở đây tạm chỉnh tag)
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Segoe UI', 9, 'bold'), rowheight=30)
        style.configure("Treeview", rowheight=28, font=('Segoe UI', 9))

        self.tree = ttk.Treeview(tree_container, columns=[c[0] for c in self.cols_def], 
                                 show="headings", selectmode="extended")
        
        for c_id, c_name, c_width in self.cols_def:
            if c_id in ["stt", "name"]:
                self.tree.heading(c_id, text=c_name, command=lambda c=c_id: router.on_header_click(c))
            else:
                self.tree.heading(c_id, text=c_name)
            
            anchor_val = "center" if c_id in ["stt", "gender"] else "w"
            self.tree.column(c_id, width=c_width, anchor=anchor_val)
            
        self.tree.tag_configure('custom', foreground='#e74c3c', font=('Segoe UI', 9, 'bold')) # Đỏ đẹp hơn
        self.tree.tag_configure('instruction', foreground='#95a5a6', font=('Segoe UI', 10, 'italic'))
        
        ysb = ttk.Scrollbar(tree_container, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(tree_container, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=ysb.set, xscrollcommand=xsb.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew")
        ysb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        
        self.tree.bind("<<TreeviewSelect>>", router.on_user_select_change)

        # Label Placeholder đẹp hơn
        self.lbl_placeholder = tk.Label(
            self.tree, 
            text="📂 Vui lòng chọn File Excel dữ liệu", 
            font=("Segoe UI", 13, "italic"), 
            fg="#bdc3c7", bg="white"
        )
        self.lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")

    # ... (Các hàm update_pagination_label, update_data, update_header_arrow GIỮ NGUYÊN) ...
    def update_pagination_label(self, current, total):
        self.lbl_page_info.config(text=f"{current} / {total}") # Thêm khoảng trắng cho thoáng

    def update_data(self, df, custom_configs):
        # (Copy y nguyên code cũ vào đây)
        for i in self.tree.get_children(): self.tree.delete(i)
        if df is None or df.empty:
            self.lbl_placeholder.place(relx=0.5, rely=0.5, anchor="center")
            return
        else:
            self.lbl_placeholder.place_forget()
            
        # ... logic insert data cũ ...
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