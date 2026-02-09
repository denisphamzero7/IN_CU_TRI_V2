import hashlib
import os
import subprocess

class LicenseManager:
    def __init__(self):
        # MẬT KHẨU BÍ MẬT (Giữ nguyên như cũ)
        self.SECRET_SALT = "MISA_APP_2026_SECRET_KEY" 
        self.LICENSE_FILE = "license.key"
        
    def _run_hidden_command(self, cmd):
        """
        Hàm chạy lệnh CMD 'tàng hình' (VIP feature: Không nháy cửa sổ đen)
        """
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            
            # Chạy lệnh và ẩn luôn console
            output = subprocess.check_output(
                cmd, 
                startupinfo=startupinfo, 
                stderr=subprocess.DEVNULL, 
                stdin=subprocess.DEVNULL
            )
            return output.decode('utf-8', errors='ignore').strip()
        except Exception:
            return ""

    def get_stable_serial(self):
        """
        Lấy Serial Mainboard.
        Ưu tiên PowerShell (Chuẩn mới) -> WMIC (Chuẩn cũ)
        """
        serial = ""
        
        # 1. Thử PowerShell trước (Chính xác hơn trên Win 10/11)
        ps_cmd = ['powershell', '-command', 'Get-CimInstance -ClassName Win32_BaseBoard | Select-Object -ExpandProperty SerialNumber']
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            output = subprocess.check_output(ps_cmd, startupinfo=startupinfo, stderr=subprocess.DEVNULL)
            serial = output.decode('utf-8', errors='ignore').strip()
        except:
            pass

        # 2. Fallback sang WMIC nếu PowerShell lỗi
        if not serial:
            wmic_cmd = "wmic baseboard get serialnumber"
            raw = self._run_hidden_command(wmic_cmd)
            lines = raw.split('\n')
            if len(lines) > 1:
                serial = lines[1].strip()

        # Danh sách Serial rác cần loại bỏ
        bad_serials = [
            "", "None", "Default String", "To be filled by O.E.M.", 
            "0", "System Serial Number", "To be filled by O.E.M"
        ]
        
        if not serial or serial in bad_serials or len(serial) < 3:
            return None 
            
        return serial

    def get_cpu_id(self):
        """Lấy CPU ID để dự phòng"""
        cmd = "wmic cpu get processorid"
        raw = self._run_hidden_command(cmd)
        lines = raw.split('\n')
        if len(lines) > 1:
            return lines[1].strip()
        return "UNKNOWN_CPU"

    def get_hwid(self):
        """
        Tạo mã máy (Logic chuẩn: Mainboard -> CPU)
        Đã loại bỏ hoàn toàn MAC Address (uuid) để tránh đổi key khi đổi mạng.
        """
        main_serial = self.get_stable_serial()
        
        if main_serial:
            # Máy xịn: Dùng Serial Mainboard
            raw_id = f"{main_serial}-{self.SECRET_SALT}"
        else:
            # Máy Mainboard lỗi serial: Dùng CPU ID thay thế
            # Để đảm bảo tính duy nhất
            cpu_id = self.get_cpu_id()
            raw_id = f"CPU-{cpu_id}-{self.SECRET_SALT}"

        # Trả về MD5 (32 ký tự) như format cũ của bạn
        return hashlib.md5(raw_id.encode()).hexdigest().upper()

    def generate_expected_key(self, hwid):
        """
        Tạo Key đúng dựa trên HWID.
        GIỮ NGUYÊN FORMAT CŨ CỦA BẠN (20 ký tự đầu của SHA256)
        """
        raw_data = f"{hwid}::{self.SECRET_SALT}::PRO"
        # Cắt lấy 20 ký tự đầu
        return hashlib.sha256(raw_data.encode()).hexdigest()[:20].upper()

    def validate(self):
        """Kiểm tra file license"""
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
        with open(self.LICENSE_FILE, "w") as f:
            f.write(key.strip())

# --- TEST NHANH ---
if __name__ == "__main__":
    app = LicenseManager()
    hwid = app.get_hwid()
    key = app.generate_expected_key(hwid)
    print(f"HWID (MD5): {hwid}")
    print(f"KEY (Old Format): {key}")