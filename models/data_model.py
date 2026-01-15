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
        
        # --- [THAY ĐỔI] Danh sách cột để chọn tìm kiếm ---
        self.searchable_columns = [] 
        self.current_search_column = "Tất cả" # Mặc định tìm tất cả
        # -------------------------------------------------
        
        self.current_search_keyword = "" 
        self.current_page = 1
        self.page_size = 100   
        self.total_pages = 1
        self.selected_indices = set()
        self._load_config()

    # ... (Giữ nguyên _load_config và save_config) ...
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
        try:
            self.df = pd.read_excel(path, engine="calamine",dtype=str).fillna("")
        except ImportError:
            print("Chưa cài 'python-calamine'. Đang dùng engine mặc định...")
            self.df = pd.read_excel(path).fillna("")
        except Exception as e:
            self.df = pd.read_excel(path).fillna("")
        # Sau khi đọc xong, xóa các chữ "nan" vô nghĩa nếu có
        self.df = self.df.replace(["nan", "NaN"], "", regex=True)
        self.df.columns = self.df.columns.str.strip()
        
        # --- [THAY ĐỔI] Lấy danh sách Header cho ComboBox ---
        # Thêm tùy chọn "Tất cả" ở đầu
        self.searchable_columns = ["Tất cả"] + list(self.df.columns)
        self.current_search_column = "Tất cả"
        self.current_search_keyword = ""
        # ----------------------------------------------------
        
        self.apply_filters()
        
        # Khởi tạo config (Giữ nguyên)
        for col in self.df.columns:
            if col not in self.global_config:
                self.global_config[col] = {"x": 50, "y": 50, "size": 21, "enable": False, "font": "Times New Roman", "color": "Black", "type": "text","bold": True,}
        if "signature_img" not in self.global_config:
             self.global_config["signature_img"] = {"x": 300, "y": 300, "w": 150, "h": 80, "enable": True, "type": "image"} 
        self.save_config()

    def apply_filters(self):
        if self.df is None or self.df.empty: 
            self.df_filtered = pd.DataFrame()
            return

        temp_df = self.df.copy()
        kw = self.current_search_keyword.lower().strip()

        # --- [THAY ĐỔI] Logic lọc theo Cột đã chọn ---
        if kw:
            # 1. Nếu chọn "Tất cả": Tìm trong các cột quan trọng (Tên, CCCD) hoặc toàn bộ
            if self.current_search_column == "Tất cả":
                col_name = next((c for c in self.df.columns if "họ tên" in c.lower() or "name" in c.lower()), None)
                col_cccd = next((c for c in self.df.columns if "cccd" in c.lower() or "cmnd" in c.lower()), None)
                
                conditions = []
                if col_name: conditions.append(temp_df[col_name].astype(str).str.lower().str.contains(kw))
                if col_cccd: conditions.append(temp_df[col_cccd].astype(str).str.lower().str.contains(kw))
                
                # Nếu không tìm thấy cột Tên/CCCD thì tìm trên toàn bộ bảng (chậm hơn xíu nhưng chắc chắn)
                if not conditions:
                    mask = temp_df.astype(str).apply(lambda x: x.str.lower().str.contains(kw)).any(axis=1)
                    temp_df = temp_df[mask]
                else:
                    final_condition = conditions[0]
                    for cond in conditions[1:]: final_condition = final_condition | cond
                    temp_df = temp_df[final_condition]
            
            # 2. Nếu chọn CỘT CỤ THỂ (Ví dụ: Số Căn Cước)
            elif self.current_search_column in temp_df.columns:
                # Chỉ lọc đúng cột đó
                temp_df = temp_df[temp_df[self.current_search_column].astype(str).str.lower().str.contains(kw)]
        
        # ---------------------------------------------

        self.df_filtered = temp_df

        if not self.df_filtered.empty:
            self.total_pages = math.ceil(len(self.df_filtered) / self.page_size)
        else:
            self.total_pages = 1
        self.current_page = 1 

    # [THAY ĐỔI] Hàm này đổi tên từ filter_data thành set_search_column cho rõ nghĩa
    def set_search_column(self, col_name):
        self.current_search_column = col_name
        # Khi đổi cột, ta áp dụng filter lại ngay (nếu đang có từ khóa)
        self.apply_filters()

    def search_data(self, keyword):
        self.current_search_keyword = keyword
        self.apply_filters()
        
    # ... (Các hàm sort_data, get_effective_config... giữ nguyên) ...
    def sort_data(self, col_key, reverse=False):
        if self.df_filtered is None or self.df_filtered.empty: return
        
        target_col = None
        
        # 1. Xác định tên cột thực tế trong DataFrame dựa trên col_key (col0, col1...)
        if col_key.startswith("col"):
            try:
                # Lấy số thứ tự từ chuỗi "col1" -> 1
                idx = int(col_key.replace("col", ""))
                # Kiểm tra xem index có nằm trong danh sách cột của Excel không
                if 0 <= idx < len(self.df.columns):
                    target_col = self.df.columns[idx]
            except ValueError:
                pass
        
        # (Fallback) Hỗ trợ logic cũ nếu truyền vào "stt" hoặc "name"
        if not target_col:
            if col_key == "stt": target_col = self.df.columns[0]
            elif col_key == "name": 
                 target_col = next((c for c in self.df.columns if "họ tên" in c.lower() or "name" in c.lower()), None)

        # 2. Thực hiện sắp xếp
        if target_col:
            # A. Nếu là cột TÊN (Họ và tên): Sắp xếp theo Tên (từ cuối cùng)
            is_name_col = "họ tên" in target_col.lower() or "name" in target_col.lower()
            
            if is_name_col:
                try:
                    # Tạo cột tạm chứa Tên (tách từ Họ và Tên) để sort
                    self.df_filtered['_sort_key'] = self.df_filtered[target_col].astype(str).apply(lambda x: x.strip().split(' ')[-1])
                    # Sort theo Tên trước, sau đó đến cả cụm Họ Tên
                    self.df_filtered = self.df_filtered.sort_values(by=['_sort_key', target_col], ascending=not reverse)
                    self.df_filtered.drop(columns=['_sort_key'], inplace=True)
                except:
                    self.df_filtered = self.df_filtered.sort_values(by=target_col, ascending=not reverse)
            
            # B. Nếu không phải cột Tên, kiểm tra xem có phải cột SỐ không (STT, Năm sinh...)
            else:
                try:
                    # Thử chuyển sang số để sort (để tránh lỗi 1, 10, 2...)
                    self.df_filtered['_sort_tmp'] = pd.to_numeric(self.df_filtered[target_col])
                    self.df_filtered = self.df_filtered.sort_values(by='_sort_tmp', ascending=not reverse)
                    self.df_filtered.drop(columns=['_sort_tmp'], inplace=True)
                except:
                    # C. Nếu không phải số, sort theo Text bình thường
                    self.df_filtered = self.df_filtered.sort_values(by=target_col, ascending=not reverse)

        # Reset về trang 1 sau khi sort
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
        if idx in self.custom_configs and "signature_img" in self.custom_configs[idx]:
            p = self.custom_configs[idx]["signature_img"].get("path")
            if p and os.path.exists(p): return Image.open(p).convert("RGBA")

        if "signature_img" in self.global_config:
            global_p = self.global_config["signature_img"].get("path")
            if global_p and os.path.exists(global_p): 
                return Image.open(global_p).convert("RGBA")

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
        """Xóa trường khỏi config và LƯU NGAY vào file JSON"""
        is_changed = False
        
        # 1. Xóa khỏi cấu hình Global (Cấu hình chung)
        # [SỬA LỖI]: Dùng đúng biến self.global_config
        if field_name in self.global_config:
            del self.global_config[field_name]
            is_changed = True
            
        # 2. Xóa khỏi các cấu hình Custom (Cấu hình riêng lẻ)
        # [SỬA LỖI]: Dùng đúng biến self.custom_configs
        for idx in self.custom_configs:
            if field_name in self.custom_configs[idx]:
                del self.custom_configs[idx][field_name]
                is_changed = True
        
        # 3. Lưu lại vào CONFIG_FILE
        if is_changed:
            try:
                # Gọi lại hàm save_config() có sẵn để ghi vào CONFIG_FILE an toàn
                self.save_config()
                print(f"Đã xóa vĩnh viễn trường '{field_name}' trong CONFIG_FILE")
                return True
            except Exception as e:
                print(f"Lỗi không lưu được file JSON: {e}")
                return False
        return False