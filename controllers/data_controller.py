import os
from tkinter import filedialog, messagebox
# from PIL import Image # Không cần dùng PIL ở đây nữa
from helpers.msg_helper import MsgHelper
class DataController:
    def __init__(self, router):
        self.router = router
        self.model = router.model
        self.view = None

    def select_template(self):
        # Chỉ cần lưu đường dẫn, không cần tính toán resize gì cả
        path = filedialog.askopenfilename(filetypes=[("Image", "*.jpg;*.png;*.jpeg")])
        if path:
            self.model.template_path = path
            self.router.ctrl_canvas.render()

    def select_signature_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.model.signature_folder = folder
            MsgHelper.show_info("Tuyệt vời", f"Đã chọn folder chữ ký:\n{folder}")

    def select_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx;*.xls")])
        if path:
            try:
                self.model.load_excel(path)
                
                total_count = len(self.model.df) if self.model.df is not None else 0
                
                if self.router.view and hasattr(self.router.view, 'p_mid'):
                    self.router.view.p_mid.set_total_count(total_count)

                self.router.view.p_left.refresh_field_list(self.model.df.columns, self.model.global_config)
                self.router.refresh_mid_table()
                self.router.ctrl_canvas.render()
                self.router.deselect_all()
                
            except Exception as e:
                messagebox.showerror("Lỗi", str(e))