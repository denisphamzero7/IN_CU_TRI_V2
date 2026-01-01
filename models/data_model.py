# models/data_model.py
import json
import pandas as pd
import os
import math  # <--- [QUAN TRỌNG] Phải import thư viện này để tính số trang
from PIL import Image
from copy import deepcopy
from config.settings import CONFIG_FILE

class VoterModel:
    def __init__(self):
        self.df = None
        self.template_path = None
        self.signature_folder = None
        self.global_config = {}
        self.custom_configs = {}
        self._load_config()
        # --- [MỚI] Biến phục vụ bộ lọc ---
        self.df_filtered = None  # DataFrame lưu kết quả sau khi lọc (Dùng cái này để hiển thị)
        self.unique_areas = []   # Danh sách các khu vực để hiện lên Combobox
        # --- Pagination State ---
        self.current_page = 1
        self.page_size = 50   # Số dòng mỗi trang
        self.total_pages = 1
        # --- [MỚI] Lưu trạng thái chọn (Set chứa các index) ---
        self.selected_indices = set()
    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.global_config = data.get("global", {})
                    self.custom_configs = {int(k): v for k, v in data.get("custom", {}).items()}
            except: pass
        
        if "signature_img" not in self.global_config:
            self.global_config["signature_img"] = {"x": 300, "y": 300, "w": 150, "h": 80, "enable": True, "type": "image"}

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump({"global": self.global_config, "custom": self.custom_configs}, f, indent=4, ensure_ascii=False)

    def load_excel(self, path):
        self.df = pd.read_excel(path).fillna("")
        self.df.columns = self.df.columns.str.strip()
        # --- [MỚI] Khởi tạo dữ liệu lọc bằng dữ liệu gốc ---
        self.df_filtered = self.df.copy()
        # Tìm cột "Khu vực" để lấy danh sách các xã/phường
        col_area = None
        for col in self.df.columns:
            if "Khu vực" in col or "Thôn" in col or "Xã" in col:
                col_area = col
                break
        
        if col_area:
            # Lấy danh sách duy nhất, loại bỏ ô trống, sắp xếp
            # astype(str) để tránh lỗi nếu cột có lẫn số
            raw = self.df[col_area].unique()
            clean_areas = [str(x) for x in raw if str(x) != "nan" and str(x) != ""]
            self.unique_areas = ["Tất cả"] + sorted(clean_areas)
        else:
            self.unique_areas = ["Tất cả"]
        # --- [LOGIC MỚI] Tính tổng số trang ngay khi load file ---
        if not self.df.empty:
            self.total_pages = math.ceil(len(self.df) / self.page_size)
        else:
            self.total_pages = 1
        self.current_page = 1 # Reset về trang 1
        # --------------------------------------------------------

        # Init config mặc định
        for col in self.df.columns:
            if col not in self.global_config:
                self.global_config[col] = {"x": 50, "y": 50, "size": 30, "enable": False, "font": "Arial", "color": "Black", "type": "text"}
        
        if "signature_img" not in self.global_config:
             self.global_config["signature_img"] = {"x": 300, "y": 300, "w": 150, "h": 80, "enable": True, "type": "image"}
             
        self.save_config()
        #Hàm lọc
    def filter_data(self, area_name):
        """ [MỚI] Hàm lọc dữ liệu cốt lõi """
        if self.df is None or self.df.empty: return

        if not area_name or area_name == "Tất cả":
            self.df_filtered = self.df.copy()
        else:
            # Tìm lại tên cột khu vực
            col_area = None
            for col in self.df.columns:
                if "Khu vực bỏ phiếu" in col:
                    col_area = col
                    break
            
            if col_area:
                # Lọc dữ liệu: Chỉ lấy dòng có khu vực trùng khớp
                self.df_filtered = self.df[self.df[col_area].astype(str) == area_name].copy()
            else:
                self.df_filtered = self.df.copy() # Không tìm thấy cột thì không lọc
        
        # Tính toán lại phân trang sau khi lọc
        if not self.df_filtered.empty:
            self.total_pages = math.ceil(len(self.df_filtered) / self.page_size)
        else:
            self.total_pages = 1
        self.current_page = 1 # Reset về trang 1
    def sort_data(self, col_key, reverse=False):
        """
        Hàm sắp xếp dữ liệu
        col_key: 'stt' hoặc 'name'
        reverse: False (Tăng dần - A->Z), True (Giảm dần - Z->A)
        """
        if self.df_filtered is None or self.df_filtered.empty: return

        # 1. Xác định tên cột thực tế trong Excel
        target_col = None
        
        # Tìm cột STT
        if col_key == "stt":
            # Thường là cột đầu tiên hoặc cột có chữ "Stt"
            for col in self.df.columns:
                if "stt" in col.lower():
                    target_col = col
                    break
            if not target_col: target_col = self.df.columns[0] # Mặc định cột 0
            
            # Sắp xếp số học cho STT
            self.df_filtered = self.df_filtered.sort_values(by=target_col, ascending=not reverse)

        # Tìm cột Họ Tên
        elif col_key == "name":
            for col in self.df.columns:
                if "họ tên" in col.lower() or "name" in col.lower():
                    target_col = col
                    break
            
            if target_col:
                # [NÂNG CAO] Sắp xếp theo Tên (Từ cuối cùng của chuỗi) cho đúng chuẩn Việt Nam
                # Tạo một cột tạm để sort
                try:
                    self.df_filtered['_sort_key'] = self.df_filtered[target_col].astype(str).apply(lambda x: x.strip().split(' ')[-1])
                    self.df_filtered = self.df_filtered.sort_values(by=['_sort_key', target_col], ascending=not reverse)
                    self.df_filtered.drop(columns=['_sort_key'], inplace=True)
                except:
                    # Fallback: Sắp xếp bình thường nếu lỗi
                    self.df_filtered = self.df_filtered.sort_values(by=target_col, ascending=not reverse)

        # 2. Reset về trang 1 sau khi xếp xong
        self.current_page = 1
    def get_effective_config(self, idx):
        config = deepcopy(self.global_config)
        if idx in self.custom_configs:
            for col, props in self.custom_configs[idx].items():
                if col in config: config[col].update(props)
                else: config[col] = props
        return config
    def update_config_value(self, idx, mode, col, key, value):
        if mode == "global":
            # 1. Cập nhật vào cấu hình chung
            if col not in self.global_config:
                self.global_config[col] = {}
            self.global_config[col][key] = value
            
            # --- [THÊM ĐOẠN NÀY] ---
            # Logic: Nếu đang chỉnh Global, ta kiểm tra xem người hiện tại (idx)
            # có đang bị "dính" cấu hình riêng cho thuộc tính này không? Nếu có thì xóa đi để nó ăn theo Global.
            # (Chỉ áp dụng cho các thuộc tính Style như: size, font, bold, color...)
            if key in ["size", "font", "bold", "upper", "color"]:
                if idx in self.custom_configs and col in self.custom_configs[idx]:
                    if key in self.custom_configs[idx][col]:
                        del self.custom_configs[idx][col][key] # Xóa thuộc tính riêng đi
            # -----------------------

            self.save_config()
        else:
            # Chế độ Individual (Giữ nguyên)
            if idx not in self.custom_configs: self.custom_configs[idx] = {}
            if col not in self.custom_configs[idx]:
                self.custom_configs[idx][col] = deepcopy(self.global_config.get(col, {}))
            self.custom_configs[idx][col][key] = value
            self.save_config()

    def reset_custom_config(self, idx):
        if idx in self.custom_configs:
            del self.custom_configs[idx]
            self.save_config()
            return True
        return False

    def get_signature_image(self, idx):
        if idx in self.custom_configs and "signature_img" in self.custom_configs[idx]:
            p = self.custom_configs[idx]["signature_img"].get("path")
            if p and os.path.exists(p): return Image.open(p).convert("RGBA")

        if self.signature_folder and self.df is not None:
            row = self.df.iloc[idx]
            col_cccd = None
            for col in self.df.columns:
                if "CCCD" in col.upper() or "CMND" in col.upper():
                    col_cccd = col
                    break
            cccd = str(row.get(col_cccd, "")).strip() if col_cccd else ""
            names = [cccd, str(idx+1)] if cccd else [str(idx+1)]
            for n in names:
                for ext in [".png", ".jpg", ".jpeg"]:
                    p = os.path.join(self.signature_folder, n + ext)
                    if os.path.exists(p): return Image.open(p).convert("RGBA")
        return None

    # --- [LOGIC MỚI] Các hàm hỗ trợ phân trang ---
    def get_current_page_data(self):
        """ [SỬA] Lấy dữ liệu từ df_filtered thay vì df """
        if self.df_filtered is None or self.df_filtered.empty:
            return pd.DataFrame()
            
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        
        # Trả về trang hiện tại của danh sách ĐÃ LỌC
        return self.df_filtered.iloc[start:end]

    def set_page(self, page):
        """Chuyển trang an toàn"""
        if 1 <= page <= self.total_pages:
            self.current_page = page
            return True
        return False