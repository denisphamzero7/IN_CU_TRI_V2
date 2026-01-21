import threading
from tkinter import filedialog, messagebox
# from PIL import Image # Không cần dùng PIL ở đây nữa
from helpers.msg_helper import MsgHelper

class DataController:
    def __init__(self, router):
        self.router = router
        self.model = router.model
        self.view = None

    def select_template(self):
        # 1. Mở hộp thoại chọn file
        path = filedialog.askopenfilename(filetypes=[("Image", "*.jpg;*.png;*.jpeg")])
        
        if path:
            # 2. Lưu đường dẫn vào Model
            self.model.template_path = path
            
            # 3. [QUAN TRỌNG] Gọi lệnh Fit to Window
            # Cần update_idletasks để Tkinter kịp cập nhật kích thước khung Canvas trước khi tính toán
            if self.router.view:
                self.router.view.update_idletasks()
            
            # Gọi hàm tự động zoom vừa màn hình (đã thêm ở bước trước)
            self.router.ctrl_canvas.fit_to_window()

    def select_signature_folder(self):
        folder = filedialog.askdirectory(title="Chọn thư mục chứa chữ ký")
        if folder:
            self.model.signature_folder = folder
            MsgHelper.show_info("Thành công", f"Đã chọn folder chữ ký:\n{folder}")

    def select_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx;*.xls;*.xlsb")])
        if path:
            # 1. Bật trạng thái Loading (Đổi con trỏ chuột thành đồng hồ cát)
            if self.router.view:
                self.router.view.master.config(cursor="watch")
            
            # 2. Chạy việc nặng trong luồng riêng (Thread)
            thread = threading.Thread(target=self._load_excel_thread, args=(path,))
            thread.daemon = True # Tự đóng khi app đóng
            thread.start()

    def _load_excel_thread(self, path):
        """Hàm này chạy ngầm, không được chạm trực tiếp vào UI ở đây"""
        try:
            # Gọi hàm load trong Model (đã tối ưu engine)
            self.model.load_excel(path)
            
            # 3. Sau khi xong, gửi tín hiệu về Luồng Chính (Main Thread) để cập nhật UI
            if self.router.view:
                self.router.view.after(0, self._on_load_success)
        except Exception as e:
            if self.router.view:
                self.router.view.after(0, lambda: self._on_load_error(str(e)))

    def _on_load_success(self):
        try:
            total_count = len(self.model.df) if self.model.df is not None else 0
            
            # Update UI cơ bản
            if self.router.view and hasattr(self.router.view, 'p_mid'):
                self.router.view.p_mid.set_total_count(total_count)
            self.router.view.p_left.refresh_field_list(self.model.df.columns, self.model.global_config)
            
            # --- [MỚI] NẠP DỮ LIỆU CHO 2 BỘ LỌC ---
            
            # 1. Nạp bộ lọc Ngày sinh
            date_opts = self.model.get_date_options() # [("Text", "key"), ...]
            self.router.view.p_mid.cbb_date['values'] = [opt[0] for opt in date_opts]
            self.router.view.p_mid.cbb_date.current(0)
            self.router.map_date = {opt[0]: opt[1] for opt in date_opts} # Lưu map

            # 2. Nạp bộ lọc CCCD
            cccd_opts = self.model.get_cccd_options()
            self.router.view.p_mid.cbb_cccd['values'] = [opt[0] for opt in cccd_opts]
            self.router.view.p_mid.cbb_cccd.current(0)
            self.router.map_cccd = {opt[0]: opt[1] for opt in cccd_opts} # Lưu map
            # --------------------------------------

            self.router.refresh_mid_table()
            self.router.ctrl_canvas.render()
            self.router.deselect_all()
            
            MsgHelper.show_info(f"Đã tải {total_count:,} dòng dữ liệu.", "Thành công")

        except Exception as e:
            MsgHelper.show_error(str(e), title="Lỗi hiển thị")
        finally:
            if self.router.view:
                self.router.view.master.config(cursor="")

    def _on_load_error(self, error_msg):
        """Hàm báo lỗi chạy trên Main Thread"""
        if self.router.view:
            self.router.view.master.config(cursor="")
        # [SỬA]: Dùng MsgHelper
        MsgHelper.show_error(error_msg, title="Lỗi đọc file")