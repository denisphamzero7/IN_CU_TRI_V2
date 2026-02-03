import uuid
import hashlib
import os
import subprocess
class LicenseManager:
    def __init__(self):
        # MẬT KHẨU BÍ MẬT (Phải giống hệt tool tạo key của Admin)
        self.SECRET_SALT = "MISA_APP_2026_SECRET_KEY" 
        self.LICENSE_FILE = "license.key"
        
    def get_mainboard_serial(self):
        """Hàm riêng để lấy Serial Mainboard trên Windows"""
        try:
            # Lệnh CMD lấy Serial Number của Baseboard
            cmd = "wmic baseboard get serialnumber"
            
            # Chạy lệnh và lấy kết quả
            output = subprocess.check_output(cmd, shell=True)
            
            # Kết quả trả về dạng bytes, cần decode ra string
            # Format trả về thường là:
            # SerialNumber \r\n
            # [MÃ_SERIAL]  \r\n
            lines = output.decode().split('\n')
            
            # Lấy dòng thứ 2 (index 1) và xóa khoảng trắng thừa
            serial = lines[1].strip()
            
            # Kiểm tra nếu serial rỗng (trường hợp hiếm), quay về dùng MAC
            if not serial:
                return str(uuid.getnode())
                
            return serial
        except Exception:
            return str(uuid.getnode())

    def get_hwid(self):
        """Lấy mã máy duy nhất (Dựa trên MAC Address)"""
        node = self.get_mainboard_serial()
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
            with open(self.LICENSE_FILE, "r", encoding="utf-8") as f:
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