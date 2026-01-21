import json
import pandas as pd
import os
import math 
import re 
import numpy as np  # Bắt buộc cài: pip install numpy
from PIL import Image
from copy import deepcopy
from config.settings import CONFIG_FILE
from helpers.msg_helper import MsgHelper

class VoterModel:
    # --- CONSTANTS (REGEX) ---
    PAT_DATE_VN = re.compile(r"^(?:0?[1-9]|[12][0-9]|3[01])/(?:0?[1-9]|1[0-2])/\d{4}$")
    PAT_DATE_ISO = re.compile(r"^\d{4}-(?:0?[1-9]|1[0-2])-(?:0?[1-9]|[12][0-9]|3[01])$")
    PAT_CCCD = re.compile(r"^\d{9,12}$")

    def __init__(self):
        self.df = None
        self.template_path = None
        self.global_config = {}
        self.custom_configs = {}
        self.df_filtered = None 
        self.searchable_columns = [] 
        self.current_search_column = "Tất cả" 
        self.current_search_keyword = "" 
        self.current_page = 1
        self.page_size = 100   
        self.total_pages = 1
        self.selected_indices = set()
        self.detected_cols = {"cccd": None, "date": None} 
        
        # Mặc định bộ lọc
        self.filter_state = {
            "date": "all",  # Mặc định là tất cả
            "cccd": "all"   
        }
        self._load_config()
    
    # --- HÀM ĐOÁN LOẠI CỘT (TỐI ƯU HÓA) ---
    def _guess_column_type(self, series):
        sample = series.dropna().astype(str).str.strip()
        sample = sample[sample != ""] 
        sample = sample[sample != "nan"]
        
        if sample.empty: return "text"
        if len(sample) > 1000: sample = sample.head(1000)
        
        total = len(sample)
        count_vn = sample.str.match(self.PAT_DATE_VN).sum()
        count_iso = sample.str.match(self.PAT_DATE_ISO).sum()
        count_cccd = sample.str.match(self.PAT_CCCD).sum()

        if ((count_vn + count_iso) / total) > 0.2: return "date"
        if (count_cccd / total) > 0.2: return "cccd"
        return "text"
    
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

    # --- LOAD EXCEL ---
    def load_excel(self, path):
        try:
            self.df = pd.read_excel(path, engine="calamine", dtype=str)
        except:
            self.df = pd.read_excel(path, dtype=str)

        self.df = self.df.fillna("")
        self.df = self.df.replace(["nan", "NaN", "None"], "", regex=True)
        self.df.columns = self.df.columns.str.strip()

        if not self.df.empty:
            col_1_values = self.df.iloc[:, 0].astype(str).str.strip()
            self.df = self.df[col_1_values != ""]
            
        self.df.reset_index(drop=True, inplace=True)

        # Chuẩn hóa ngày tháng
        iso_regex = r"^(\d{4})-(\d{2})-(\d{2})$"
        for col in self.df.columns:
            series_str = self.df[col].astype(str)
            mask_time = series_str.str.contains("-") & series_str.str.contains(" ")
            if mask_time.any():
                self.df.loc[mask_time, col] = series_str[mask_time].apply(lambda x: x.split(" ")[0])
                series_str = self.df[col].astype(str)
            mask_float = series_str.str.endswith(".0")
            if mask_float.any():
                self.df.loc[mask_float, col] = series_str[mask_float].str[:-2]
                series_str = self.df[col].astype(str)
            if series_str.str.match(iso_regex).any():
                self.df[col] = series_str.str.replace(iso_regex, r"\3/\2/\1", regex=True)

        # Detect cột
        self.detected_cols = {"cccd": None, "date": None}
        self.filter_state = {"date": "all", "cccd": "all"}

        for col in self.df.columns:
            col_type = self._guess_column_type(self.df[col])
            if col_type == "cccd":
                self.detected_cols["cccd"] = col 
                mask_11 = (self.df[col].str.len() == 11) & (self.df[col].str.isdigit())
                if mask_11.any():
                    self.df.loc[mask_11, col] = "0" + self.df.loc[mask_11, col]
            elif col_type == "date":
                self.detected_cols["date"] = col 

        self.searchable_columns = ["Tất cả"] + list(self.df.columns)
        self.current_search_column = "Tất cả"
        self.apply_filters()
        
        # Init Config
        for col in self.df.columns:
            if col not in self.global_config:
                self.global_config[col] = {"x": 50, "y": 50, "size": 21, "enable": False, "font": "Arial", "color": "Black", "bold": True}
        if "signature_img" not in self.global_config:
             self.global_config["signature_img"] = {"x": 300, "y": 300, "w": 150, "h": 80, "enable": True} 
        self.save_config()

    # --- OPTIONS (Đã thêm "Tất cả") ---
    def get_date_options(self):
        col = self.detected_cols["date"]
        if not col or col not in self.df.columns:
            return [("Tất cả", "all")]

        s = self.df[col].astype(str).str.strip()
        c_valid = (s.str.match(self.PAT_DATE_VN) | s.str.match(self.PAT_DATE_ISO)).sum()
        c_invalid = len(self.df) - c_valid 
        
        return [
            (f"Tất cả ", "all"),
            (f"Ngày sinh đúng định dạng ({c_valid})", "valid"),
            (f"Ngày sinh sai định dạng ({c_invalid})", "invalid")
        ]

    def get_cccd_options(self):
        col = self.detected_cols["cccd"]
        if not col or col not in self.df.columns:
            return [("Tất cả", "all")]

        s = self.df[col].astype(str).str.strip()
        c_12 = (s.str.len() == 12).sum()
        c_other = len(self.df) - c_12 

        return [
            (f"Tất cả", "all"),
            (f"Số căn cước 12 số ({c_12})", "12"),
            (f"Số căn cước Khác ({c_other})", "other")
        ]

    # --- BỘ LỌC (TỐI ƯU NUMPY + SMART SEARCH) ---
    def set_date_filter(self, key):
        self.filter_state["date"] = key
        self.apply_filters()

    def set_cccd_filter(self, key):
        self.filter_state["cccd"] = key
        self.apply_filters()

    def apply_filters(self):
        if self.df is None or self.df.empty: 
            self.df_filtered = pd.DataFrame()
            self.total_pages = 1
            return

        final_mask = np.ones(len(self.df), dtype=bool)

        # 1. Lọc Ngày sinh
        date_key = self.filter_state["date"]
        col_date = self.detected_cols["date"]
        if col_date and col_date in self.df.columns and date_key != "all":
            s_date = self.df[col_date].astype(str).str.strip()
            is_valid = (s_date.str.match(self.PAT_DATE_VN) | s_date.str.match(self.PAT_DATE_ISO))

            if date_key == "valid":
                final_mask &= is_valid.to_numpy()
            elif date_key == "invalid":
                final_mask &= (~is_valid).to_numpy()

        # 2. Lọc CCCD
        cccd_key = self.filter_state["cccd"]
        col_cccd = self.detected_cols["cccd"]
        if col_cccd and col_cccd in self.df.columns and cccd_key != "all":
            s_cccd = self.df[col_cccd].astype(str).str.strip()
            is_12 = (s_cccd.str.len() == 12)
            
            if cccd_key == "12":
                final_mask &= is_12.to_numpy()
            elif cccd_key == "other":
                final_mask &= (~is_12).to_numpy()

        # 3. Tìm kiếm thông minh (Bỏ dấu cách)
        kw = self.current_search_keyword.lower().strip()
        if kw:
            kw_nospace = kw.replace(" ", "")
            
            if self.current_search_column == "Tất cả":
                search_mask = np.zeros(len(self.df), dtype=bool)
                for col in self.searchable_columns:
                    if col == "Tất cả" or col not in self.df.columns: continue
                    s_col = self.df[col].astype(str).str.lower()
                    col_mask = (s_col.str.contains(kw, na=False, regex=False) | 
                                s_col.str.contains(kw_nospace, na=False, regex=False))
                    search_mask |= col_mask.to_numpy()
                final_mask &= search_mask
                
            elif self.current_search_column in self.df.columns:
                s_col = self.df[self.current_search_column].astype(str).str.lower()
                col_mask = (s_col.str.contains(kw, na=False, regex=False) | 
                            s_col.str.contains(kw_nospace, na=False, regex=False))
                final_mask &= col_mask.to_numpy()
        
        self.df_filtered = self.df[final_mask]

        if not self.df_filtered.empty:
            self.total_pages = math.ceil(len(self.df_filtered) / self.page_size)
        else:
            self.total_pages = 1
        self.current_page = 1

    # --- HELPERS ---
    def set_search_column(self, col_name):
        self.current_search_column = col_name
        self.apply_filters()

    def search_data(self, keyword):
        self.current_search_keyword = keyword
        self.apply_filters()
        
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
        if idx in self.custom_configs and "signature_img" in self.custom_configs[idx]:
            p = self.custom_configs[idx]["signature_img"].get("path")
            if p and os.path.exists(p): return Image.open(p).convert("RGBA")

        if "signature_img" in self.global_config:
            global_p = self.global_config["signature_img"].get("path")
            if global_p and os.path.exists(global_p): 
                return Image.open(global_p).convert("RGBA")
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
    
    def delete_field_permanently(self, field_name):
        is_changed = False
        if field_name in self.global_config:
            del self.global_config[field_name]
            is_changed = True
        for idx in self.custom_configs:
            if field_name in self.custom_configs[idx]:
                del self.custom_configs[idx][field_name]
                is_changed = True
        if is_changed:
            self.save_config()
            return True
        return False
    
    def sort_data(self, col_key, reverse=False):
        if self.df_filtered is None or self.df_filtered.empty: return
        target_col = None
        if col_key.startswith("col"):
            try:
                idx = int(col_key.replace("col", ""))
                if 0 <= idx < len(self.df.columns):
                    target_col = self.df.columns[idx]
            except ValueError: pass
        if not target_col:
            if col_key == "stt": target_col = self.df.columns[0]
            elif col_key == "name": 
                 target_col = next((c for c in self.df.columns if "họ tên" in c.lower() or "name" in c.lower()), None)
        if target_col:
            is_name_col = "họ tên" in target_col.lower() or "name" in target_col.lower()
            if is_name_col:
                try:
                    self.df_filtered['_sort_key'] = self.df_filtered[target_col].astype(str).apply(lambda x: x.strip().split(' ')[-1])
                    self.df_filtered = self.df_filtered.sort_values(by=['_sort_key', target_col], ascending=not reverse)
                    self.df_filtered.drop(columns=['_sort_key'], inplace=True)
                except:
                    self.df_filtered = self.df_filtered.sort_values(by=target_col, ascending=not reverse)
            else:
                try:
                    self.df_filtered['_sort_tmp'] = pd.to_numeric(self.df_filtered[target_col])
                    self.df_filtered = self.df_filtered.sort_values(by='_sort_tmp', ascending=not reverse)
                    self.df_filtered.drop(columns=['_sort_tmp'], inplace=True)
                except:
                    self.df_filtered = self.df_filtered.sort_values(by=target_col, ascending=not reverse)
        self.current_page = 1