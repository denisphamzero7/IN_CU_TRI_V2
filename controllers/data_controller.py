from tkinter import filedialog, messagebox

class DataController:
    def __init__(self, router):
        self.router = router
        self.model = router.model
        self.view = None 

    def select_template(self):
        path = filedialog.askopenfilename(filetypes=[("Image", "*.jpg;*.png")])
        if path:
            self.model.template_path = path
            self.router.ctrl_canvas.render()

    def select_signature_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.model.signature_folder = folder
            messagebox.showinfo("OK", f"Đã chọn folder chữ ký:\n{folder}")

    def select_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx;*.xls")])
        if path:
            try:
                self.model.load_excel(path)
                
                # --- [SỬA LỖI TẠI ĐÂY] ---
                # Lấy tổng số dòng
                total_count = len(self.model.df) if self.model.df is not None else 0
                
                # Truy cập đúng đường dẫn: router -> view -> p_mid
                if self.router.view and hasattr(self.router.view, 'p_mid'):
                    self.router.view.p_mid.set_total_count(total_count)
                # -------------------------

                # Cập nhật Left View
                self.router.view.p_left.refresh_field_list(self.model.df.columns, self.model.global_config)
                
                # Refresh bảng dữ liệu
                self.router.refresh_mid_table()
                
                self.router.ctrl_canvas.render()
                self.router.select_all()
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))