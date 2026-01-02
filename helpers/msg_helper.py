# helpers/msg_helper.py
from views.custom_dialog import CustomDialog

class MsgHelper:
    """ 
    Helper trung gian:
    Thay vì gọi Messagebox mặc định, nó sẽ gọi CustomDialog (có Logo xịn).
    """

    @staticmethod
    def show_info(message, title="Thông báo", parent=None):
        # Gọi CustomDialog với type="info"
        CustomDialog(parent, title, message, msg_type="info")

    @staticmethod
    def show_warning(message, title="Cảnh báo", parent=None):
        # Gọi CustomDialog với type="warning" -> Hiện logo thay vì tam giác vàng
        CustomDialog(parent, title, message, msg_type="warning")
    
    @staticmethod
    def show_error(message, title="Lỗi", parent=None):
        CustomDialog(parent, title, message, msg_type="error")

    @staticmethod
    def ask_yes_no(message, title="Xác nhận", parent=None):
        # Với câu hỏi Yes/No, ta cần lấy kết quả trả về (True/False)
        dialog = CustomDialog(parent, title, message, msg_type="question")
        return dialog.result