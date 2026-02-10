import hashlib
import os
import subprocess
import re
from functools import lru_cache

class LicenseManager:
    def __init__(self):
        self.SECRET_SALT = "MISA_APP_2026_SECRET_KEY" 
        self.LICENSE_FILE = "license.key"
        
    def _run_cmd(self, cmd):
        """Hàm chạy lệnh CMD ẩn cửa sổ"""
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            output = subprocess.check_output(
                cmd, 
                shell=True, 
                startupinfo=startupinfo, 
                stderr=subprocess.DEVNULL, 
                stdin=subprocess.DEVNULL
            )
            return output.decode('utf-8', errors='ignore').strip()
        except Exception:
            return ""

    @lru_cache(maxsize=1)
    def get_stable_disk_serial(self):
        serial = ""

        # --- CÁCH 1: PowerShell (Ưu tiên) ---
        # Lệnh này lấy ổ đĩa loại Fixed (HDD/SSD), bỏ qua USB (Removable)
        # Sắp xếp theo Number để ưu tiên ổ cài Win (thường là 0 hoặc 1)
        try:
            cmd_ps = 'powershell -Command "Get-Disk | Where-Object { $_.BusType -ne \'USB\' -and $_.MediaType -ne \'Removable\' } | Sort-Object Number | Select-Object -First 1 -ExpandProperty SerialNumber"'
            serial = self._run_cmd(cmd_ps)
        except: 
            pass

        # --- CÁCH 2: WMIC (Dự phòng) ---
        if not serial:  
            try:
                # Bỏ 'index=0' để quét toàn bộ ổ, sau đó lọc trong Python
                raw_wmi = self._run_cmd("wmic diskdrive get serialnumber, mediatype")
                
                # Lọc output để tìm dòng có Serial hợp lệ
                lines = raw_wmi.split('\n')
                for line in lines:
                    line = line.strip()
                    # Bỏ qua dòng tiêu đề và dòng trống
                    if not line or "SerialNumber" in line:
                        continue
                    
                    # WMIC thường trả về kèm khoảng trắng, lấy phần tử đầu tiên là Serial
                    parts = line.split()
                    if parts:
                        candidate = parts[0].strip()
                        # Kiểm tra sơ bộ độ dài để tránh lấy rác
                        if len(candidate) > 4: 
                            serial = candidate
                            break # Lấy được cái đầu tiên thì dừng ngay
            except: 
                pass

        # --- LÀM SẠCH ---
        if serial:
            # Chỉ giữ lại chữ và số, viết hoa
            clean_serial = re.sub(r'[^A-Z0-9]', '', serial.upper())
            if clean_serial: 
                return clean_serial
        
        # --- QUAN TRỌNG: KHÔNG DÙNG TÊN MÁY TÍNH ---
        # Nếu không tìm thấy ổ cứng, trả về lỗi cố định. 
        # Điều này có nghĩa là License sẽ KHÔNG hoạt động trên máy không đọc được ổ cứng,
        # nhưng nó đảm bảo mã máy không bao giờ tự thay đổi khi đổi tên PC.
        return "NO-DISK-SERIAL-FOUND-ERROR"
        
      
    def get_hwid(self):
        disk_serial = self.get_stable_disk_serial()
        # Nếu không lấy được Serial ổ cứng, HWID sẽ chứa chuỗi lỗi ở trên
        raw_id = f"HWID-{disk_serial}-{self.SECRET_SALT}"
        return hashlib.md5(raw_id.encode()).hexdigest().upper()

    def generate_expected_key(self, hwid):
        raw_data = f"{hwid}::{self.SECRET_SALT}::PRO"
        return hashlib.sha256(raw_data.encode()).hexdigest()[:20].upper()

    def validate(self):
        hwid = self.get_hwid()
        expected_key = self.generate_expected_key(hwid)
        if not os.path.exists(self.LICENSE_FILE): return False, hwid
        try:
            with open(self.LICENSE_FILE, "r", encoding="utf-8") as f:
                user_key = f.read().strip()
            return (user_key == expected_key), hwid
        except: return False, hwid

    def save_license(self, key):
        with open(self.LICENSE_FILE, "w", encoding="utf-8") as f:
            f.write(key.strip())