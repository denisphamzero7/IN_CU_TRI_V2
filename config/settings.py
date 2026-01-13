# config/settings.py

CONFIG_FILE = "cau_hinh_v12_final.json"
STATIC_FIELDS_LIST = [
    "Tên đơn vị", 
    "Người ký", 
    "Khu vực bỏ phiếu", 
    "Xã/phường/đặc khu"
]
# --- [MỚI] CẤU HÌNH MÀU SẮC GIAO DIỆN MISA ---
# 1. Màu nền chính (Xanh tím nhạt)
APP_BG_COLOR = "#D9E1F2"

# 2. Màu chữ tiêu đề (Xanh đen Navy)
APP_TEXT_COLOR = "#002B5E"

# 3. Màu nền danh sách trắng (Giấy tờ)
LIST_BG_COLOR = "#FFFFFF"

# 4. Cấu hình màu Nút bấm (Style MISA)
MISA_BG_COLOR = "#dae6f3"       # Nền xanh nhạt
MISA_BORDER_COLOR = "#004085"   # Viền & Chữ xanh đậm
MISA_TEXT_NORMAL = "#000000"    # Chữ đen
MISA_WHITE = "#ffffff"

# --- (Các phần cũ giữ nguyên) ---
COLORS = {
    "primary": "#3498db", "success": "#2ecc71", "danger": "#e74c3c",
    "warning": "#f39c12", "purple": "#9b59b6", "dark": "#D9E1F2",
    "light": "#ecf0f1", "grey": "#bdc3c7", "text": "#D9E1F2", "white": "#ffffff"
}

# --- BẢNG MÀU CHUẨN MISA / WINDOWS CLASSIC (Dựa trên hình ảnh) ---
MISA_BG_COLOR = "#dae6f3"       # Màu nền xanh nhạt (giống trong ảnh)
MISA_BORDER_COLOR = "#004085"   # Màu viền xanh dương đậm (cho nút và khung)
MISA_TEXT_COLOR = "#004085"     # Màu chữ xanh dương đậm
MISA_TEXT_NORMAL = "#000000"    # Màu chữ đen thường
MISA_WHITE = "#ffffff"

# Cấu hình Header dùng lại màu này cho đồng bộ
APP_BG_COLOR = MISA_BG_COLOR
APP_TEXT_COLOR = MISA_TEXT_COLOR

FONT_MAP = {
    "Arial": {"normal": "arial.ttf", "bold": "arialbd.ttf"},
    "Times New Roman": {"normal": "times.ttf", "bold": "timesbd.ttf"},
    "Calibri": {"normal": "calibri.ttf", "bold": "calibrib.ttf"}
}

STYLES = {
    "primary": "primary", "secondary": "secondary", "success": "success",
    "danger": "danger", "warning": "warning", "info": "info",
    "light": "light", "dark": "dark"
}

APP_ICON_NAME = "image.ico" 
APP_TITLE = "ỦY BAN BAN BẦU CỬ THÀNH PHỐ ĐÀ NẴNG - PHẦN MỀM IN THẺ CỬ TRI"
APP_HEADER = "ỦY BAN BẦU CỬ THÀNH PHỐ ĐÀ NẴNG"
APP_CONTACT_INFO = "Điện thoại: (0236) 3827853   |   Thư điện tử: ubbctp@danang.gov.vn"
APP_ADDRESS = "Tầng 10, Trung tâm hành chính, 24 Trần Phú, Hải Châu, Đà Nẵng"
APP_PHONE = "(0236) 3827853"
APP_EMAIL = "ubbctp@danang.gov.vn"

APP_SUPPORT = "Hỗ trợ phần mềm: 0911.02.12.87"
APP_CREDIT = "Thiết kế bởi Danatec"