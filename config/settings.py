# config/settings.py

CONFIG_FILE = "cau_hinh_v12_final.json"

COLORS = {
    "primary": "#3498db", "success": "#2ecc71", "danger": "#e74c3c",
    "warning": "#f39c12", "purple": "#9b59b6", "dark": "#2c3e50",
    "light": "#ecf0f1", "grey": "#bdc3c7", "text": "#2c3e50", "white": "#ffffff"
}

# 1. Danh sách các Theme...
AVAILABLE_THEMES = {
    "light": ["cosmo", "flatly", "journal", "litera", "lumen", "minty", "pulse", "sandstone", "united", "yeti", "morph", "simplex", "cerculean"],
    "dark": ["superhero", "darkly", "cyborg", "vapor", "solar"]
}

# 2. Cấu hình mặc định
DEFAULT_THEME = "superhero"

# 3. Font map
FONT_MAP = {
    "Arial": {"normal": "arial.ttf", "bold": "arialbd.ttf"},
    "Times New Roman": {"normal": "times.ttf", "bold": "timesbd.ttf"},
    "Calibri": {"normal": "calibri.ttf", "bold": "calibrib.ttf"}
}

# 4. Các hằng số ngữ nghĩa
STYLES = {
    "primary": "primary", "secondary": "secondary", "success": "success",
    "danger": "danger", "warning": "warning", "info": "info",
    "light": "light", "dark": "dark"
}

APP_ICON_NAME = "image.ico" 
APP_TITLE = "ỦY BAN BAN BẦU CỬ THÀNH PHỐ ĐÀ NẴNG - PHẦN MỀM IN THẺ CỬ TRI"
APP_HEADER = "ỦY BAN BẦU CỬ THÀNH PHỐ ĐÀ NẴNG"
APP_CONTACT_INFO = "Điện thoại: (0236) 3827853   |   Thư điện tử: ubbctp@danang.gov.vn"
APP_ADDRESS = "Tầng 10, Trung tâm hành chính thành phố Đà Nẵng, 24 Trần Phú, Hải Châu"
APP_PHONE = "(0236) 3827853"
APP_EMAIL = "ubbctp@danang.gov.vn"

# --- [MỚI] THÔNG TIN HỖ TRỢ & BẢN QUYỀN ---
APP_SUPPORT = "Hỗ trợ kỹ thuật: 0911.02.12.87 (Anh Quân)"
APP_CREDIT = "Thiết kế bởi Danatec"