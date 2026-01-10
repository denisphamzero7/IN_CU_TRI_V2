import json
import pandas as pd
import os
import math 
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
       
        self.df_filtered = None 
        self.unique_areas = []   
        
        # --- [SỬA] Đặt mặc định là từ khóa này ---
        self.current_area_filter = "Lọc theo khu vực"
        # -----------------------------------------
        
        self.current_search_keyword = "" 
        self.current_page = 1
        self.page_size = 100   
        self.total_pages = 1
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
        """
        Tối ưu hóa việc đọc file lớn
        """
        try:
            # CÁCH 1: Dùng engine 'calamine' (Siêu nhanh - Cần pip install python-calamine)
            self.df = pd.read_excel(path, engine="calamine").fillna("")
        except ImportError:
            print("Chưa cài 'python-calamine'. Đang dùng engine mặc định (chậm hơn)...")
            # CÁCH 2: Fallback về openpyxl nếu chưa cài calamine
            self.df = pd.read_excel(path).fillna("")
        except Exception as e:
            # Trường hợp file .xls cũ quá thì calamine có thể kén, thử lại mặc định
            self.df = pd.read_excel(path).fillna("")

        # Chuẩn hóa tên cột (xóa khoảng trắng thừa đầu đuôi)
        self.df.columns = self.df.columns.str.strip()
        
        # --- Logic Reset cũ giữ nguyên ---
        self.current_area_filter = "Lọc theo khu vực"
        self.current_search_keyword = ""
        # ---------------------------------
        
        # ... (Phần logic tìm cột Area và unique_areas giữ nguyên) ...
        col_area = None
        for col in self.df.columns:
            if "Khu vực" in col or "Thôn" in col or "Xã" in col:
                col_area = col
                break
        
        if col_area:
            # Tối ưu lấy unique nhanh hơn cho dữ liệu lớn
            raw = self.df[col_area].dropna().unique()
            clean_areas = [str(x) for x in raw if str(x).strip() != ""]
            self.unique_areas = ["Lọc theo khu vực"] + sorted(clean_areas)
        else:
            self.unique_areas = ["Lọc theo khu vực"]
            
        self.apply_filters()
        
        # Khởi tạo config cho các cột mới (Giữ nguyên code cũ)
        for col in self.df.columns:
            if col not in self.global_config:
                self.global_config[col] = {"x": 50, "y": 50, "size": 30, "enable": False, "font": "Arial", "color": "Black", "type": "text"}
        if "signature_img" not in self.global_config:
             self.global_config["signature_img"] = {"x": 300, "y": 300, "w": 150, "h": 80, "enable": True, "type": "image"} 
        self.save_config()

    def apply_filters(self):
        if self.df is None or self.df.empty: 
            self.df_filtered = pd.DataFrame()
            return

        temp_df = self.df.copy()

        # --- [SỬA] Logic lọc: Nếu là từ khóa mặc định thì hiện tất cả ---
        # Danh sách các từ khóa được coi là "Không lọc"
        ignore_filters = ["Tất cả", "Chưa chọn khu vực", "Lọc theo khu vực", ""]
        
        if self.current_area_filter and self.current_area_filter not in ignore_filters:
            col_area = None
            for col in self.df.columns:
                if "Khu vực" in col or "Thôn" in col or "Xã" in col:
                    col_area = col
                    break
            if col_area:
                temp_df = temp_df[temp_df[col_area].astype(str) == self.current_area_filter]
        # ---------------------------------------------------------------

        kw = self.current_search_keyword.lower().strip()
        if kw:
            col_name = next((c for c in self.df.columns if "họ tên" in c.lower() or "name" in c.lower()), None)
            col_cccd = next((c for c in self.df.columns if "cccd" in c.lower() or "cmnd" in c.lower()), None)
            conditions = []
            if col_name: conditions.append(temp_df[col_name].astype(str).str.lower().str.contains(kw))
            if col_cccd: conditions.append(temp_df[col_cccd].astype(str).str.lower().str.contains(kw))
            if conditions:
                final_condition = conditions[0]
                for cond in conditions[1:]: final_condition = final_condition | cond
                temp_df = temp_df[final_condition]

        self.df_filtered = temp_df

        if not self.df_filtered.empty:
            self.total_pages = math.ceil(len(self.df_filtered) / self.page_size)
        else:
            self.total_pages = 1
        self.current_page = 1 

    def filter_data(self, area_name):
        self.current_area_filter = area_name
        self.apply_filters()

    def search_data(self, keyword):
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
            if col not in self.global_config: self.global_config[col] = {}
            self.global_config[col][key] = value
            if key in ["size", "font", "bold", "upper", "color"]:
                if idx in self.custom_configs and col in self.custom_configs[idx]:
                    if key in self.custom_configs[idx][col]: del self.custom_configs[idx][col][key] 
            self.save_config()
        else:
            if idx not in self.custom_configs: self.custom_configs[idx] = {}
            if col not in self.custom_configs[idx]: self.custom_configs[idx][col] = deepcopy(self.global_config.get(col, {}))
            self.custom_configs[idx][col][key] = value
            self.save_config()

    def reset_custom_config(self, idx):
        if idx in self.custom_configs:
            del self.custom_configs[idx]
            self.save_config()
            return True
        return False

    def get_signature_image(self, idx):
        # 1. ƯU TIÊN CAO NHẤT: Kiểm tra cấu hình RIÊNG (Custom Config)
        if idx in self.custom_configs and "signature_img" in self.custom_configs[idx]:
            p = self.custom_configs[idx]["signature_img"].get("path")
            # Nếu có đường dẫn riêng hợp lệ -> Trả về ảnh riêng
            if p and os.path.exists(p): return Image.open(p).convert("RGBA")

        # 2. ƯU TIÊN NHÌ: Kiểm tra cấu hình CHUNG (Global Config) - [PHẦN MỚI THÊM]
        # Nếu đã chọn "Chỉnh tất cả" và chọn 1 ảnh, nó sẽ nằm ở đây
        if "signature_img" in self.global_config:
            global_p = self.global_config["signature_img"].get("path")
            # Nếu có đường dẫn chung -> Trả về ảnh chung cho tất cả mọi người
            # (Trừ những người đã có cấu hình riêng ở bước 1)
            if global_p and os.path.exists(global_p): 
                return Image.open(global_p).convert("RGBA")

        # 3. ƯU TIÊN CUỐI: Tự động tìm trong Folder Chữ ký dựa theo CCCD hoặc STT
        if self.signature_folder and self.df is not None:
            row = self.df.iloc[idx]
            col_cccd = None
            for col in self.df.columns:
                if "CCCD" in col.upper() or "CMND" in col.upper():
                    col_cccd = col
                    break
            cccd = str(row.get(col_cccd, "")).strip() if col_cccd else ""
            
            # Các tên file có thể có: CCCD.png, CCCD.jpg, STT.png...
            names = [cccd, str(idx+1)] if cccd else [str(idx+1)]
            
            for n in names:
                for ext in [".png", ".jpg", ".jpeg"]:
                    p = os.path.join(self.signature_folder, n + ext)
                    if os.path.exists(p): return Image.open(p).convert("RGBA")
        
        return None

    def get_current_page_data(self):
        if self.df_filtered is None or self.df_filtered.empty: return pd.DataFrame()
        start = (self.current_page - 1) * self.page_size
        end = start + self.page_size
        return self.df_filtered.iloc[start:end]

    def set_page(self, page):
        if 1 <= page <= self.total_pages:
            self.current_page = page
            return True
        return False