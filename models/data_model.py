import json
import pandas as pd
import os
import math 
import re 
import numpy as np 
from copy import deepcopy
from config.settings import CONFIG_FILE
from helpers.msg_helper import MsgHelper
import gc 
# [FIX LỖI 1]: Thêm import Image để không bị báo lỗi "Image is not defined"
from PIL import Image 

class VoterModel:
    # --- CONSTANTS (REGEX) ---
    # PAT_DATE_VN = re.compile(r"^(?:0?[1-9]|[12][0-9]|3[01])/(?:0?[1-9]|1[0-2])/\d{4}$")
    PAT_DATE_VN = re.compile(r"^(?:0?[1-9]|[12][0-9]|3[01])[./-](?:0?[1-9]|1[0-2])[./-]\d{4}$")
    PAT_DATE_ISO_PANDAS = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")
    PAT_CCCD = re.compile(r"^[\d\.]{9,20}$")

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
        
        self.cached_date_opts = None 
        self.cached_cccd_opts = None 
        
        self.filter_state = {
            "date": "all",
            "cccd": "all"   
        }
        self._load_config()
    
    def _guess_column_type(self, series):
        total_rows = len(series)
        
        # --- CHIẾN THUẬT TỐI ƯU CHO 1 TRIỆU DÒNG ---
        # Mục tiêu: Chỉ lấy khoảng 3000 mẫu để check
        TARGET_SAMPLE = 3000
        
        if total_rows > TARGET_SAMPLE:
            # Tính bước nhảy. VD: 1.000.000 / 3000 = 333
            step = total_rows // TARGET_SAMPLE
            if step < 1: step = 1
            # Cắt lát trực tiếp trên dữ liệu thô (Rất nhanh, không tốn RAM)
            raw_sample = series.iloc[::step]
        else:
            raw_sample = series

        # --- CHỈ XỬ LÝ TRÊN TẬP MẪU NHỎ (3000 dòng) ---
        # Lúc này mới dropna và convert string -> Tốc độ siêu nhanh
        sample = raw_sample.dropna().astype(str).str.replace(r'\s+', ' ', regex=True).str.strip()
        sample = sample[sample != ""]
        
        total_check = len(sample)
        if total_check == 0: return "text"
        
        # --- LOGIC NHẬN DIỆN (Giữ nguyên yêu cầu của bạn) ---
        # 1. Check ngày chuẩn dd/mm/yyyy
        count_vn = sample.str.match(self.PAT_DATE_VN).sum()
        
        # 2. Check năm sinh (yyyy hoặc yyyy.0) để tăng độ nhạy nhận diện cột
        count_year_only = sample.str.match(r"^(\d{4}|\d{4}\.0)$").sum()
        
        # 3. Check CCCD
        count_cccd = sample.str.match(self.PAT_CCCD).sum()
        
        # Ngưỡng 20%
        if ((count_vn + count_year_only) / total_check) > 0.2: return "date"
        if (count_cccd / total_check) > 0.2: return "cccd"
        
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

    def load_excel(self, path):
        # 1. Đọc file (Calamine nhanh hơn nhiều với file lớn)
        try:
            self.df = pd.read_excel(path, engine="calamine", dtype=str)
        except:
            self.df = pd.read_excel(path, dtype=str)
        
        # Xóa dòng hoàn toàn rỗng để giảm tải
        self.df.dropna(how='all', inplace=True)
        self.df = self.df.fillna("")
        
        # Làm sạch Header
        self.df.columns = self.df.columns.astype(str).str.replace(r'[\r\n\t]+', ' ', regex=True).str.strip()
        
        # Reset index ngay để tránh lỗi lệch dòng
        self.df.reset_index(drop=True, inplace=True)

        # --- XỬ LÝ DỮ LIỆU ---
        # Với 1 triệu dòng, ta xử lý vector hóa (Vectorized) từng cột
        # Không dùng apply hay loop từng dòng vì sẽ rất chậm
        for col in self.df.columns:
            # Lấy series ra, ép kiểu chuỗi 1 lần
            s = self.df[col].astype(str)
            
            # Chỉ clean những ô không rỗng (Tối ưu tốc độ)
            # Thay thế ký tự xuống dòng bằng khoảng trắng
            s = s.str.replace(r'[\r\n\t]+', ' ', regex=True).str.strip()
            
            # 1. Fix lỗi float .0 (Vectorized operation - cực nhanh)
            # Chỉ tìm những chuỗi kết thúc bằng .0 và cắt đi
            mask_float = s.str.endswith(".0")
            if mask_float.any():
                # Dùng slice vector thay vì loop
                s.loc[mask_float] = s.loc[mask_float].str[:-2]
            
            # 2. Fix lỗi Date ngược (yyyy-mm-dd)
            mask_iso = s.str.match(r"^(\d{4})-(\d{2})-(\d{2})")
            if mask_iso.any():
                s.loc[mask_iso] = s.loc[mask_iso].str.replace(
                    r"^(\d{4})-(\d{2})-(\d{2})(?:.*)", 
                    r"\3/\2/\1", 
                    regex=True
                )
            
            # Gán ngược lại dataframe
            self.df[col] = s

        # --- DETECT CỘT (Gọi hàm tối ưu mới) ---
        self.detected_cols = {"cccd": None, "date": None}
        for col in self.df.columns:
            # Hàm _guess_column_type mới chạy cực nhanh
            col_type = self._guess_column_type(self.df[col])
            
            if col_type == "cccd":
                self.detected_cols["cccd"] = col 
                # Chuẩn hóa CCCD (thêm số 0) - Chỉ chạy trên cột đã detect
                mask_11 = (self.df[col].str.len() == 11) & (self.df[col].str.isdigit())
                if mask_11.any():
                    self.df.loc[mask_11, col] = "0" + self.df.loc[mask_11, col]
            
            elif col_type == "date":
                self.detected_cols["date"] = col 

        # --- RESET UI ---
        self.searchable_columns = ["Tất cả"] + list(self.df.columns)
        self.cached_date_opts = None
        self.cached_cccd_opts = None
        self.current_page = 1
        self.current_search_keyword = ""
        self.filter_state = {"date": "all", "cccd": "all"}
        
        self.apply_filters()
        
        # --- INIT CONFIG (Giữ nguyên) ---
        default_props = {"x": 50, "y": 50, "size": 21, "enable": False, "font": "Times New Roman", "color": "Black", "bold": True}
        for col in self.df.columns:
            if col not in self.global_config:
                self.global_config[col] = default_props.copy()
            else:
                for k, v in default_props.items():
                    if k not in self.global_config[col]:
                        self.global_config[col][k] = v

        self.save_config()
        gc.collect() # Dọn rác bộ nhớ ngay sau khi load xong

    def get_date_options(self):
        if self.cached_date_opts: return self.cached_date_opts
        c_valid = 0
        c_invalid = 0
        col = self.detected_cols.get("date")
        if self.df is not None:
            c_invalid = len(self.df)
        if self.df is not None and not self.df.empty and col and col in self.df.columns:
            s = self.df[col].astype(str).str.strip()
            is_valid = s.str.match(self.PAT_DATE_VN)
            c_valid = is_valid.sum()
            c_invalid = len(self.df) - c_valid
        
        self.cached_date_opts = [
            (f"Tất cả", "all"),
            (f"Ngày sinh đúng định dạng ({c_valid})", "valid"),
            (f"Ngày sinh sai định dạng ({c_invalid})", "invalid")
        ]
        return self.cached_date_opts

    def get_cccd_options(self):
        if self.cached_cccd_opts: return self.cached_cccd_opts
        c_12 = 0
        c_other = 0
        col = self.detected_cols.get("cccd")
        if self.df is not None:
            c_other = len(self.df) 
        if self.df is not None and not self.df.empty and col and col in self.df.columns:
            s = self.df[col].astype(str).str.strip()
            is_12 = (s.str.len() == 12) & (s.str.isdigit())
            c_12 = is_12.sum()
            c_other = len(self.df) - c_12

        self.cached_cccd_opts = [
            (f"Tất cả", "all"),
            (f"Số căn cước 12 số ({c_12})", "12"),
            (f"Số căn cước Khác ({c_other})", "other")
        ]
        return self.cached_cccd_opts

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

        # Lọc Date
        date_key = self.filter_state["date"]
        col_date = self.detected_cols["date"]
        
        if date_key != "all":
            if col_date and col_date in self.df.columns:
                s_date = self.df[col_date].astype(str).str.strip()
                is_valid = s_date.str.match(self.PAT_DATE_VN)
                if date_key == "valid": final_mask &= is_valid.to_numpy()
                elif date_key == "invalid": final_mask &= (~is_valid).to_numpy()
            else:
                if date_key == "valid": final_mask[:] = False 
                elif date_key == "invalid": pass

        # Lọc CCCD
        cccd_key = self.filter_state["cccd"]
        col_cccd = self.detected_cols["cccd"]
        if cccd_key != "all":
            if col_cccd and col_cccd in self.df.columns:
                s_cccd = self.df[col_cccd].astype(str).str.strip()
                is_12 = (s_cccd.str.len() == 12) & (s_cccd.str.isdigit())
                if cccd_key == "12": final_mask &= is_12.to_numpy()
                elif cccd_key == "other": final_mask &= (~is_12).to_numpy()
            else:
                if cccd_key == "12": final_mask[:] = False
                elif cccd_key == "other": pass

        # Tìm kiếm
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
        self.df_filtered = self.df_filtered.copy()
        target_col = None
        if col_key.startswith("col"):
            try:
                idx = int(col_key.replace("col", ""))
                real_cols = list(self.df.columns)
                if 0 <= idx < len(real_cols): target_col = real_cols[idx]
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