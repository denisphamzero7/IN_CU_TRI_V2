# config/settings.py

CONFIG_FILE = "cau_hinh_v12_final.json"

COLORS = {
    "primary": "#3498db", "success": "#2ecc71", "danger": "#e74c3c",
    "warning": "#f39c12", "purple": "#9b59b6", "dark": "#2c3e50",
    "light": "#ecf0f1", "grey": "#bdc3c7", "text": "#2c3e50", "white": "#ffffff"
}


# 1. Danh sách các Theme có sẵn trong ttkbootstrap để bạn tham khảo/lựa chọn
# Bạn có thể lưu tên theme này vào file json để đổi giao diện
AVAILABLE_THEMES = {
    "light": [
        "cosmo", "flatly", "journal", "litera", "lumen", "minty", 
        "pulse", "sandstone", "united", "yeti", "morph", "simplex", "cerculean"
    ],
    "dark": [
        "superhero", "darkly", "cyborg", "vapor", "solar"
    ]
}

# 2. Cấu hình mặc định
DEFAULT_THEME = "superhero"  # Chọn theme mặc định (Ví dụ: 'superhero' là dark mode, 'litera' là light mode)

# 3. Font map (Vẫn giữ nguyên để load font hệ thống nếu cần)
FONT_MAP = {
    "Arial": {"normal": "arial.ttf", "bold": "arialbd.ttf"},
    "Times New Roman": {"normal": "times.ttf", "bold": "timesbd.ttf"},
    "Calibri": {"normal": "calibri.ttf", "bold": "calibrib.ttf"}
}

# 4. Các hằng số ngữ nghĩa (Semantic Constants)
# Dùng để gợi nhớ các keywords của ttkbootstrap
STYLES = {
    "primary": "primary",
    "secondary": "secondary",
    "success": "success",
    "danger": "danger",
    "warning": "warning",
    "info": "info",
    "light": "light",
    "dark": "dark"
}

APP_ICON_NAME = "image.ico" 
APP_TITLE = "HỆ THỐNG IN THẺ CỬ TRI"