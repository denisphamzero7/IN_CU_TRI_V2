import hashlib
import os
import subprocess
import re

class LicenseManager:
    def __init__(self):
        # KHÓA BÍ MẬT - Không được đổi
        self.SECRET_SALT = "MISA_APP_2026_SECRET_KEY" 
        self.LICENSE_FILE = "license.key"
        
    def _run_cmd(self, cmd):
        """Hàm chạy lệnh CMD an toàn, ẩn cửa sổ đen"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            output = subprocess.check_output(
                cmd, 
                startupinfo=startupinfo, 
                stderr=subprocess.DEVNULL, 
                stdin=subprocess.DEVNULL
            )
            return output.decode('utf-8', errors='ignore').strip()
        except Exception:
            return ""

    def get_stable_disk_serial(self):
        """
        Hàm lấy Serial ổ cứng TỐI ƯU HÓA ĐỘ ỔN ĐỊNH.
        Chỉ sử dụng WMIC (User thường cũng chạy được).
        """
        serial = ""
        
        # --- CÁCH 1: WMIC (Chuẩn nhất - Không cần Admin) ---
        # Lấy Serial của ổ đĩa vật lý số 0 (Luôn là ổ Boot Win)
        # Cách này tránh được việc user cắm USB làm đổi mã máy
        wmic_cmd = "wmic path Win32_DiskDrive where \"Index=0\" get SerialNumber"
        
        try:
            raw = self._run_cmd(wmic_cmd)
            lines = raw.split('\n')
            for line in lines:
                clean = line.strip()
                # Bỏ dòng tiêu đề "SerialNumber" và dòng trống
                if clean and "SerialNumber" not in clean:
                    serial = clean
                    break
        except:
            pass

        # --- CÁCH 2: Fallback WMIC (Nếu cách 1 lỗi cú pháp) ---
        # Lấy serial của tất cả ổ Fixed (Gắn trong), chọn cái đầu tiên
        if not serial:
            try:
                wmic_cmd_2 = "wmic path Win32_DiskDrive where \"MediaType='Fixed hard disk media'\" get SerialNumber"
                raw = self._run_cmd(wmic_cmd_2)
                lines = raw.split('\n')
                for line in lines:
                    clean = line.strip()
                    if clean and "SerialNumber" not in clean:
                        serial = clean
                        break
            except:
                pass

        # --- CÁCH 3: Volume Serial (Dự phòng cuối cùng) ---
        # Chỉ dùng khi máy bị hỏng WMI (Rất hiếm).
        # Nhược điểm: Format ổ C sẽ đổi key.
        if not serial:
            try:
                raw = self._run_cmd("vol c:")
                for line in raw.split('\n'):
                    if "Serial Number" in line: 
                        # Lấy chuỗi cuối cùng (VD: A1B2-C3D4)
                        serial = "VOL-" + line.split()[-1].strip()
            except:
                pass

        # --- QUAN TRỌNG: LÀM SẠCH SERIAL ---
        # Nhiều ổ cứng trả về mã Hex hoặc có khoảng trắng thừa
        if serial:
            serial = serial.upper()
            # Chỉ giữ lại Chữ và Số (A-Z, 0-9). Bỏ hết dấu cách, gạch ngang.
            serial = re.sub(r'[^A-Z0-9]', '', serial)
            
        # Nếu vẫn rỗng (Không thể xảy ra), trả về Unknown
        if not serial:
            return "UNKNOWN_DISK"

        return serial

    def get_hwid(self):
        """Tạo Mã Máy"""
        disk_serial = self.get_stable_disk_serial()
        # Prefix "HDD"
        raw_id = f"HDD-{disk_serial}-{self.SECRET_SALT}"
        return hashlib.md5(raw_id.encode()).hexdigest().upper()

    def generate_expected_key(self, hwid):
        raw_data = f"{hwid}::{self.SECRET_SALT}::PRO"
        return hashlib.sha256(raw_data.encode()).hexdigest()[:20].upper()

    def validate(self):
        hwid = self.get_hwid()
        expected = self.generate_expected_key(hwid)

        if not os.path.exists(self.LICENSE_FILE):
            return False, hwid

        try:
            with open(self.LICENSE_FILE, "r", encoding="utf-8") as f:
                user_key = f.read().strip()
            return (user_key == expected), hwid
        except:
            return False, hwid

    def save_license(self, key):
        with open(self.LICENSE_FILE, "w") as f:
            f.write(key.strip())

# # --- TEST ---
# if __name__ == "__main__":
#     app = LicenseManager()
    
#     print("-" * 30)
#     print("KIỂM TRA ĐỘ ỔN ĐỊNH")
#     print("-" * 30)
    
#     serial = app.get_stable_disk_serial()
#     print(f"Serial Gốc (Đã Clean): {serial}")
    
#     hwid = app.get_hwid()
#     print(f"Mã Máy (HWID): {hwid}")
#     print("-" * 30)
#     print("Note: Thử chạy code này bằng quyền Admin và")
#     print("quyền thường. Nếu HWID giống hệt nhau là OK.")