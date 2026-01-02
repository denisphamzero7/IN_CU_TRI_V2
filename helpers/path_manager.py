# helpers/path_manager.py
import sys
from pathlib import Path

def resource_path(relative_path):
    """ Lấy đường dẫn tuyệt đối, fix lỗi sai đường dẫn khi chạy khác thư mục """
    try:
        # Khi đã build thành file .exe (PyInstaller)
        base_path = Path(sys._MEIPASS)
    except Exception:
        # Khi đang chạy code (Dev mode)
        # __file__ là file path_manager.py
        # .parent là folder 'helpers'
        # .parent.parent là folder gốc 'APP_IN_BAU_CU'
        base_path = Path(__file__).parent.parent

    # Trả về đường dẫn dạng string chuẩn theo hệ điều hành
    return str(base_path / relative_path)