
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
        """Hàm này chạy trên Main Thread để update UI"""
        try:
            total_count = len(self.model.df) if self.model.df is not None else 0
            
            if self.router.view and hasattr(self.router.view, 'p_mid'):
                self.router.view.p_mid.set_total_count(total_count)

            self.router.view.p_left.refresh_field_list(self.model.df.columns, self.model.global_config)
            self.router.refresh_mid_table()
            
            # Render lại canvas (nếu đã có phôi thì render đè dữ liệu lên)
            self.router.ctrl_canvas.render()
            self.router.deselect_all()
            
            MsgHelper.show_info(f"Đã tải xong {total_count:,} dòng dữ liệu!", "Thành công")
            
        except Exception as e:
            messagebox.showerror("Lỗi hiển thị", str(e))
        finally:
            # Tắt trạng thái Loading
            if self.router.view:
                self.router.view.master.config(cursor="")

    def _on_load_error(self, error_msg):
        """Hàm báo lỗi chạy trên Main Thread"""
        if self.router.view:
            self.router.view.master.config(cursor="")
        messagebox.showerror("Lỗi đọc file", error_msg)
