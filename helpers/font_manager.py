# helpers/font_manager.py
import os
import platform
from config.settings import FONT_MAP

class FontManager:
    @staticmethod
    def get_path(font_name, is_bold):
        if platform.system() == "Windows":
            style = "bold" if is_bold else "normal"
            f_file = FONT_MAP.get(font_name, FONT_MAP["Arial"]).get(style, "arial.ttf")
            # Thư mục Font chuẩn của Windows
            return os.path.join(os.environ["WINDIR"], "Fonts", f_file)
        # Fallback cho Linux/Mac (cần cài đặt font hoặc trỏ đúng đường dẫn)
        return "arial.ttf"