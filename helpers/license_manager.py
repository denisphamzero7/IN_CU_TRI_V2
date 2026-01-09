import uuid
import hashlib
import os

class LicenseManager:
    def __init__(self):
        # MẬT KHẨU BÍ MẬT (Phải giống hệt tool tạo key của Admin)
        self.SECRET_SALT = "MISA_APP_2026_SECRET_KEY" 
        self.LICENSE_FILE = "license.key"

    def get_hwid(self):
        """Lấy mã máy duy nhất (Dựa trên MAC Address)"""
        node = uuid.getnode()
        # Hash lại cho ngắn gọn và bảo mật
        raw = f"{node}-{self.SECRET_SALT}"
        return hashlib.md5(raw.encode()).hexdigest().upper()

    def generate_expected_key(self, hwid):
        """Tạo ra Key đúng dựa trên HWID"""
        raw_data = f"{hwid}::{self.SECRET_SALT}::PRO"
        return hashlib.sha256(raw_data.encode()).hexdigest()[:20].upper()

    def validate(self):
        """Kiểm tra xem file license.key có khớp với máy này không"""
        hwid = self.get_hwid()
        expected = self.generate_expected_key(hwid)

        if not os.path.exists(self.LICENSE_FILE):
            return False, hwid

        try:
            with open(self.LICENSE_FILE, "r") as f:
                user_key = f.read().strip()
            
            if user_key == expected:
                return True, hwid
            else:
                return False, hwid
        except:
            return False, hwid

    def save_license(self, key):
        """Lưu key vào file"""
        with open(self.LICENSE_FILE, "w") as f:
            f.write(key.strip())