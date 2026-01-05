# helpers/window_helper.py
import tkinter as tk

class WindowSizeGuard:
    """
    Helper class để tự động tính toán và khóa kích thước tối thiểu của cửa sổ (MinSize).
    Giúp ngăn chặn việc các nút bị mất (clipping) khi người dùng co màn hình.
    """
    def __init__(self, root, fixed_widgets=None, flexible_widgets=None, padding_x=50, min_height=700):
        """
        :param root: Cửa sổ gốc (thường là self.winfo_toplevel())
        :param fixed_widgets: List các widget BẮT BUỘC phải hiện đủ (ví dụ: Toolbar bên phải) -> Dùng .winfo_reqwidth()
        :param flexible_widgets: List các widget có thể co giãn (ví dụ: Left Menu, Mid List) -> Dùng .winfo_width() hiện tại
        :param padding_x: Cộng thêm một chút khoảng trống cho an toàn
        :param min_height: Chiều cao tối thiểu mặc định
        """
        self.root = root
        self.fixed_widgets = fixed_widgets if fixed_widgets else []
        self.flexible_widgets = flexible_widgets if flexible_widgets else []
        self.padding_x = padding_x
        self.min_height = min_height

        # Đợi 200ms sau khi khởi tạo để giao diện vẽ xong rồi mới khóa
        self.root.after(200, self._lock_size)

    def _lock_size(self):
        try:
            self.root.update_idletasks() # Cập nhật thông số lần cuối

            total_width = 0

            # 1. Cộng chiều rộng các thành phần CỐ ĐỊNH (Toolbar nút bấm...)
            # Dùng reqwidth: Kích thước mong muốn (đủ để chứa các nút con)
            for widget in self.fixed_widgets:
                if widget:
                    total_width += widget.winfo_reqwidth()

            # 2. Cộng chiều rộng các thành phần CO GIÃN (Cột trái, Cột giữa...)
            # Dùng width: Kích thước hiện tại đang hiển thị
            for widget in self.flexible_widgets:
                if widget:
                    total_width += widget.winfo_width()

            # 3. Cộng thêm padding an toàn
            final_min_width = total_width + self.padding_x
            
            # Đảm bảo không nhỏ hơn kích thước hiện tại của cửa sổ (tránh bị giật)
            current_w = self.root.winfo_width()
            final_min_width = max(final_min_width, current_w)

            # 4. KHÓA KÍCH THƯỚC
            self.root.minsize(final_min_width, self.min_height)
            
            # print(f"[WindowSizeGuard] Locked MinSize: {final_min_width}x{self.min_height}") # Bật dòng này để debug nếu cần
            
        except Exception as e:
            print(f"[WindowSizeGuard] Error: {e}")