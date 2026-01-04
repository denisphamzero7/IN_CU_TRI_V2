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
       
        # --- [MỚI] Biến phục vụ bộ lọc & Tìm kiếm ---
        self.df_filtered = None  # DataFrame lưu kết quả sau khi xử lý
        self.unique_areas = []   
        self.current_area_filter = "Tất cả"
        self.current_search_keyword = "" 
        # --------------------------------------------

        # --- Pagination State ---
        self.current_page = 1
        self.page_size = 100   
        self.total_pages = 1
        
        # --- Lưu trạng thái chọn ---
        self.selected_indices = set()
        
        self._load_config()

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
        
        # Reset bộ lọc khi nạp file mới
        self.current_area_filter = "Tất cả"
        self.current_search_keyword = ""
        
        # Tìm cột "Khu vực" để lấy danh sách
        col_area = None
        for col in self.df.columns:
            if "Khu vực" in col or "Thôn" in col or "Xã" in col:
                col_area = col
                break
        
        if col_area:
            raw = self.df[col_area].unique()
            clean_areas = [str(x) for x in raw if str(x) != "nan" and str(x) != ""]
            self.unique_areas = ["Tất cả"] + sorted(clean_areas)
        else:
            self.unique_areas = ["Tất cả"]
            
        # Áp dụng bộ lọc khởi tạo (để tạo df_filtered ban đầu)
        self.apply_filters()

        # Init config mặc định
        for col in self.df.columns:
            if col not in self.global_config:
                self.global_config[col] = {"x": 50, "y": 50, "size": 30, "enable": False, "font": "Arial", "color": "Black", "type": "text"}
        
        if "signature_img" not in self.global_config:
             self.global_config["signature_img"] = {"x": 300, "y": 300, "w": 150, "h": 80, "enable": True, "type": "image"}
             
        self.save_config()

    def apply_filters(self):
        """
        [QUAN TRỌNG] Hàm lọc trung tâm:
        Kết hợp logic: (Khu vực == X) VÀ (Tên hoặc CCCD chứa từ khóa)
        """
        if self.df is None or self.df.empty: 
            self.df_filtered = pd.DataFrame()
            return

        # B1: Lấy dữ liệu gốc
        temp_df = self.df.copy()

        # B2: Lọc theo Khu Vực
        if self.current_area_filter and self.current_area_filter != "Tất cả":
            col_area = None
            for col in self.df.columns:
                if "Khu vực" in col or "Thôn" in col or "Xã" in col:
                    col_area = col
                    break
            if col_area:
                temp_df = temp_df[temp_df[col_area].astype(str) == self.current_area_filter]

        # B3: Lọc theo Từ Khóa (Search)
        kw = self.current_search_keyword.lower().strip()
        if kw:
            # Tìm tên cột Tên và CCCD
            col_name = next((c for c in self.df.columns if "họ tên" in c.lower() or "name" in c.lower()), None)
            col_cccd = next((c for c in self.df.columns if "cccd" in c.lower() or "cmnd" in c.lower()), None)
            
            conditions = []
            if col_name:
                conditions.append(temp_df[col_name].astype(str).str.lower().str.contains(kw))
            if col_cccd:
                conditions.append(temp_df[col_cccd].astype(str).str.lower().str.contains(kw))
            
            if conditions:
                # Gộp điều kiện bằng OR (|)
                final_condition = conditions[0]
                for cond in conditions[1:]:
                    final_condition = final_condition | cond
                temp_df = temp_df[final_condition]

        # B4: Cập nhật kết quả
        self.df_filtered = temp_df

        # B5: Tính lại phân trang
        if not self.df_filtered.empty:
            self.total_pages = math.ceil(len(self.df_filtered) / self.page_size)
        else:
            self.total_pages = 1
        
        self.current_page = 1 # Luôn về trang 1 khi lọc

    def filter_data(self, area_name):
        """Gọi khi chọn Combobox"""
        self.current_area_filter = area_name
        self.apply_filters()

    def search_data(self, keyword):
        """Gọi khi nhập tìm kiếm"""
        self.current_search_keyword = keyword
        self.apply_filters()

    def sort_data(self, col_key, reverse=False):
        if self.df_filtered is None or self.df_filtered.empty: return

        target_col = None
        if col_key == "stt":
            for col in self.df.columns:
                if "stt" in col.lower():
                    target_col = col
                    break
            if not target_col: target_col = self.df.columns[0]
            self.df_filtered = self.df_filtered.sort_values(by=target_col, ascending=not reverse)

        elif col_key == "name":
            for col in self.df.columns:
                if "họ tên" in col.lower() or "name" in col.lower():
                    target_col = col
                    break
            
            if target_col:
                try:
                    self.df_filtered['_sort_key'] = self.df_filtered[target_col].astype(str).apply(lambda x: x.strip().split(' ')[-1])
                    self.df_filtered = self.df_filtered.sort_values(by=['_sort_key', target_col], ascending=not reverse)
                    self.df_filtered.drop(columns=['_sort_key'], inplace=True)
                except:
                    self.df_filtered = self.df_filtered.sort_values(by=target_col, ascending=not reverse)

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
            if col not in self.global_config:
                self.global_config[col] = {}
            self.global_config[col][key] = value
            
            if key in ["size", "font", "bold", "upper", "color"]:
                if idx in self.custom_configs and col in self.custom_configs[idx]:
                    if key in self.custom_configs[idx][col]:
                        del self.custom_configs[idx][col][key] 

            self.save_config()
        else:
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

    def get_current_page_data(self):
        if self.df_filtered is None or self.df_filtered.empty:
            return pd.DataFrame()
            
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        return self.df_filtered.iloc[start:end]

    def set_page(self, page):
        if 1 <= page <= self.total_pages:
            self.current_page = page
            return True
        return False