from PIL import Image, ImageTk, ImageFont, ImageDraw
import tkinter as tk
import ttkbootstrap as ttk
from helpers.font_manager import FontManager
from helpers.image_utils import rotate_pil_image, get_column_from_tags, create_text_image

# --- IMPORT HELPER ---
from helpers.date_helpers import format_date_text_vn
from helpers.text_helper import format_cccd
from helpers.msg_helper import MsgHelper
class CanvasController:
    def __init__(self, router):
     

        self.router = router
        self.model = router.model
        
        self.tk_image = None    
        self.sig_refs = {}      
        self.scale_factor = 1.0     
        self.zoom_multiplier = 0.65  
        
        self.img_origin_x = 0       
        self.img_origin_y = 0       
        self.pan_offset_x = 0
        self.pan_offset_y = 0

        self.orig_w = 0
        self.orig_h = 0

        self.view = None 
        self.drag_data = {"x": 0, "y": 0, "item": None, "mode": None}
        self.text_img_refs = [] 

    def screen_to_data_coords(self, screen_x, screen_y):
        rel_x = screen_x - self.img_origin_x
        rel_y = screen_y - self.img_origin_y
        if self.scale_factor == 0: return 0, 0
        data_x = rel_x / self.scale_factor
        data_y = rel_y / self.scale_factor
        return data_x, data_y

    def on_resize(self, event):
        self.render()

    def render(self):
        if not self.router.view: return
        canvas = self.router.view.p_right.canvas
        canvas.delete("all")
        self.text_img_refs = []
        
        try:
            is_landscape_mode = getattr(self.router, 'is_paper_landscape', False)
        except:
            is_landscape_mode = False
        
        STD_W, STD_H = 595, 842 
        if is_landscape_mode:
            paper_w, paper_h = STD_H, STD_W  
        else:
            paper_w, paper_h = STD_W, STD_H  

        self.orig_w = paper_w
        self.orig_h = paper_h

        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        cx, cy = cw // 2, ch // 2
        
        self.scale_factor = self.zoom_multiplier
        
        disp_w = int(paper_w * self.scale_factor)
        disp_h = int(paper_h * self.scale_factor)
        
        paper_x1 = cx + self.pan_offset_x - disp_w // 2
        paper_y1 = cy + self.pan_offset_y - disp_h // 2
        
        self.img_origin_x = paper_x1
        self.img_origin_y = paper_y1

        canvas.create_rectangle(paper_x1, paper_y1, paper_x1 + disp_w, paper_y1 + disp_h, fill="white", outline="#bdc3c7", width=2, tags="draggable_paper")

        if self.model.template_path:
            try:
                pil_img = Image.open(self.model.template_path)
                pil_img = rotate_pil_image(pil_img, self.router.template_rotation)
                pil_img = pil_img.resize((int(paper_w), int(paper_h)), Image.Resampling.LANCZOS)
                
                if disp_w > 0 and disp_h > 0:
                    img_display = pil_img.resize((disp_w, disp_h), Image.Resampling.LANCZOS)
                    self.tk_image = ImageTk.PhotoImage(img_display)
                    canvas.create_image(paper_x1, paper_y1, image=self.tk_image, anchor="nw", tags="draggable_paper")
            except Exception as e:
                print(f"Render Error: {e}")
        else:
             canvas.create_text(cx, cy, text="Chưa chọn ảnh phôi", fill="#bdc3c7", font=("Arial", 14))

        if self.model.df is not None and not self.model.df.empty:
            self._render_overlay(canvas)

    def _render_overlay(self, canvas):
        idx = self.router.current_idx
        if idx >= len(self.model.df): return

        row = self.model.df.iloc[idx]
        config = self.model.get_effective_config(idx)
        self.sig_refs = {}
        
        limit_w = self.orig_w 
        limit_h = self.orig_h 

        # Tạo dummy draw để đo chiều rộng text
        dummy_img = Image.new("RGBA", (1, 1))
        dummy_draw = ImageDraw.Draw(dummy_img)

        for col, cfg in config.items():
            if not cfg.get("enable", False): continue
            
            raw_x, raw_y = cfg["x"], cfg["y"]
            safe_x = max(0, min(raw_x, limit_w))
            safe_y = max(0, min(raw_y, limit_h))
            
            sx = self.img_origin_x + safe_x * self.scale_factor
            sy = self.img_origin_y + safe_y * self.scale_factor
            
            tag_id = f"col:{col}"
            
            # --- 1. XỬ LÝ ẢNH (CHỮ KÝ) ---
            if col == "signature_img":
                w = int(cfg.get("w", 150) * self.scale_factor)
                h = int(cfg.get("h", 80) * self.scale_factor)
                sig_img = self.model.get_signature_image(idx)
                
                if not sig_img:
                    sig_img = self._create_placeholder_image(w, h, text="Chữ ký")
                else:
                    sig_img = sig_img.resize((w, h), Image.Resampling.LANCZOS)

                self.sig_refs[col] = ImageTk.PhotoImage(sig_img)
                # Ảnh dùng anchor="nw" (Góc trái trên) là chuẩn nhất cho ảnh
                canvas.create_image(sx, sy, image=self.sig_refs[col], anchor="nw", tags=("draggable", tag_id))
                canvas.create_rectangle(sx, sy, sx + w, sy + h, outline="#3498db", dash=(2, 4), tags=("draggable", tag_id))

            # --- 2. XỬ LÝ TEXT (DÙNG FONT METRICS ĐỂ FIX LỆCH) ---
            else:
                raw_val = row.get(col, "")
                val = ""
                
                col_idx = -1
                if self.model.df is not None:
                    try: col_idx = self.model.df.columns.get_loc(col)
                    except: pass
                
                if col_idx == 2: val = format_date_text_vn(raw_val) 
                elif col_idx == 4: val = format_cccd(raw_val)         
                else:
                    if str(raw_val).lower() == "nan": val = ""
                    else: val = str(raw_val)

                if cfg.get("upper", False): val = val.upper()
                
                display_val = val if val.strip() != "" else f"[{col}]"
                is_placeholder = (val.strip() == "")

                f_size = max(1, int(cfg.get("size", 21) * self.scale_factor)) 
                font_path = FontManager.get_path(cfg.get("font", "Times New Roman"), cfg.get("bold", True))
                try: pil_font = ImageFont.truetype(font_path, f_size)
                except: pil_font = ImageFont.load_default()

                # fill_color = cfg.get("color", "black")
                # Logic mới:
                if is_placeholder:
                    fill_color = "#bdc3c7"  # Màu xám (khi không có dữ liệu)
                else:
                    fill_color = cfg.get("color", "Black") # Màu cấu hình (khi có dữ liệu)
                # -------------------------------------
                # [LOGIC MỚI - TỐI ƯU]: Lấy chiều cao chuẩn của Font (Ascent + Descent)
                # Thay vì đo chiều cao của chữ cái cụ thể.
                try:
                    ascent, descent = pil_font.getmetrics()
                except:
                    ascent, descent = f_size, f_size // 3 # Fallback
                
                std_height = ascent + descent
                
                # Đo chiều rộng text
                txt_w = dummy_draw.textlength(display_val, font=pil_font)
                
                # Tạo ảnh trong suốt đủ chứa
                txt_img = Image.new("RGBA", (int(txt_w) + 10, std_height), (255, 255, 255, 0))
                d = ImageDraw.Draw(txt_img)
                
                # [QUAN TRỌNG]: anchor="la" (Left-Ascender)
                # Đảm bảo đỉnh của dòng chữ (Ascender line) luôn nằm ở y=0 của ảnh
                d.text((0, 0), display_val, font=pil_font, fill=fill_color, anchor="la")
                
                tk_txt_img = ImageTk.PhotoImage(txt_img)
                self.text_img_refs.append(tk_txt_img)
                
                # Vẽ ảnh lên Canvas tại toạ độ (sx, sy)
                # Lúc này (sx, sy) sẽ khớp với đỉnh dòng chữ (Ascender line)
                canvas.create_image(sx, sy, image=tk_txt_img, anchor="nw", tags=("draggable", tag_id))
                
                if is_placeholder:
                    canvas.create_rectangle(sx, sy, sx+txt_w, sy+std_height, outline="#bdc3c7", dash=(1, 4), tags=("draggable", tag_id))



    def drag_start(self, event):
        canvas = self.router.view.p_right.canvas
        self.drag_data = {"x": event.x, "y": event.y, "item": None, "mode": None}
        items = canvas.find_closest(event.x, event.y)
        if items:
            item_id = items[0]
            tags = canvas.gettags(item_id)
            if "draggable" in tags:
                self.drag_data["item"] = item_id
                self.drag_data["mode"] = "item"
                col_name = get_column_from_tags(tags)
                if col_name and self.router.selected_field != col_name:
                    self.router.select_field(col_name)
                    new_items = canvas.find_withtag(f"col:{col_name}")
                    if new_items: self.drag_data["item"] = new_items[0]
                return
            items_under = canvas.find_overlapping(event.x, event.y, event.x, event.y)
            for i in items_under:
                t = canvas.gettags(i)
                if "draggable_paper" in t or "bg_shadow" in t:
                    self.drag_data["mode"] = "pan"
                    return

    def drag_motion(self, event):
        mode = self.drag_data.get("mode")
        if not mode: return
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        canvas = self.router.view.p_right.canvas
        if mode == "pan":
            self.pan_offset_x += dx
            self.pan_offset_y += dy
            self.render() 
        elif mode == "item":
            if self.router.selected_field:
                tag_id = f"col:{self.router.selected_field}"
                canvas.move(tag_id, dx, dy)
            elif self.drag_data["item"]:
                canvas.move(self.drag_data["item"], dx, dy)
        self.drag_data.update({"x": event.x, "y": event.y})

    def drag_end(self, event):
        mode = self.drag_data.get("mode")
        if mode == "pan" or not self.drag_data["item"]:
            self.drag_data["item"] = None
            return
            
        item_id = self.drag_data["item"]
        canvas = self.router.view.p_right.canvas
        try: 
            tags = canvas.gettags(item_id)
        except: return
            
        col_name = get_column_from_tags(tags)
        if col_name:
            try:
                # Dùng bbox để luôn lấy góc Trái-Trên của item làm chuẩn
                bbox = canvas.bbox(item_id)
                if bbox:
                    screen_x, screen_y = bbox[0], bbox[1]
                    raw_x, raw_y = self.screen_to_data_coords(screen_x, screen_y)
                    
                    self.router.update_field_config("x", int(round(raw_x)))
                    self.router.update_field_config("y", int(round(raw_y)))

                    if self.router.selected_field == col_name: 
                        self.router.load_field_props_to_ui()
            except Exception as e: 
                print(f"Lỗi drag_end: {e}")
        
        self.render()
        self.drag_data["item"] = None

    def handle_zoom(self, event):
        if event.delta > 0: self.zoom_multiplier *= 1.1
        else: self.zoom_multiplier /= 1.1
        self.zoom_multiplier = max(0.2, min(self.zoom_multiplier, 3.0))
        self.render()

    def _create_placeholder_image(self, w, h, text=""):
        img = Image.new("RGBA", (w, h), (200, 200, 200, 100))
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, w-1, h-1], outline="red", width=2)
        try: f = ImageFont.truetype("arial.ttf", 20)
        except: f = ImageFont.load_default()
        bbox = draw.textbbox((0,0), text, font=f)
        tw = bbox[2]-bbox[0]
        th = bbox[3]-bbox[1]
        draw.text(((w-tw)/2, (h-th)/2), text, font=f, fill="red")
        return img
    
    def visual_move_selection(self, dx, dy):
        if not self.router.selected_field: return
        canvas = self.router.view.p_right.canvas
        tag_id = f"col:{self.router.selected_field}"
        canvas.move(tag_id, dx, dy)

    def commit_selection_position(self):
        if not self.router.selected_field: return
        canvas = self.router.view.p_right.canvas
        tag_id = f"col:{self.router.selected_field}"
        items = canvas.find_withtag(tag_id)
        if not items: return
        
        # Lấy item đầu tiên (thường là Image/Text)
        cur_coords = canvas.coords(items[0])
        
        screen_x, screen_y = 0, 0
        if len(cur_coords) == 2: 
            screen_x, screen_y = cur_coords[0], cur_coords[1]
        elif len(cur_coords) == 4: 
            screen_x, screen_y = (cur_coords[0]+cur_coords[2])/2, (cur_coords[1]+cur_coords[3])/2
        else: 
            return
            
        raw_x, raw_y = self.screen_to_data_coords(screen_x, screen_y)
        
        # --- [FIX QUAN TRỌNG] ---
        self.router.update_field_config("x", int(round(raw_x)))
        self.router.update_field_config("y", int(round(raw_y)))
        # ------------------------
        
        self.router.load_field_props_to_ui()
        self.render()


    def fit_to_window(self):
        if not self.router.view: return
        canvas = self.router.view.p_right.canvas
        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        if cw < 50 or ch < 50: return
        STD_W, STD_H = 595, 842 
        is_landscape_mode = getattr(self.router, 'is_paper_landscape', False)
        if is_landscape_mode: paper_w, paper_h = STD_H, STD_W  
        else: paper_w, paper_h = STD_W, STD_H
        ratio_w = cw / paper_w
        ratio_h = ch / paper_h
        new_zoom = min(ratio_w, ratio_h) * 0.9
        self.zoom_multiplier = new_zoom
        self.pan_offset_x = 0
        self.pan_offset_y = 0
        self.render()

    def handle_right_click(self, event):
        canvas = self.router.view.p_right.canvas
        
        # 1. Quét vùng chạm 4x4 pixel (tìm tất cả layer tại điểm click)
        items = canvas.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)
        items = list(items)
        
        # 2. Đảo ngược để duyệt từ TRÊN CÙNG xuống DƯỚI CÙNG
        # (Ưu tiên xử lý cái mắt người dùng đang nhìn thấy trước)
        items.reverse() 

        target_to_delete = None

        for item_id in items:
            tags = canvas.gettags(item_id)
            
            # --- [CHUẨN] CHẶN XÓA ẢNH PHÔI ---
            if "draggable_paper" in tags:
                continue 
            # ---------------------------------

            col_name = get_column_from_tags(tags)
            if not col_name: continue 
            # 2. [MỚI] CHẶN XÓA CHỮ KÝ (Nếu bạn muốn cấm tiệt việc xóa khung chữ ký bằng chuột phải)
            if col_name == "signature_img":
                continue
            
            # --- KIỂM TRA DỮ LIỆU ---
            is_protected = False
            
            # Check chữ ký
            if col_name == "signature_img":
                if self.model.get_signature_image(self.router.current_idx):
                    is_protected = True
            # Check text
            else:
                try:
                    if self.model.df is not None and not self.model.df.empty:
                        raw_val = self.model.df.iloc[self.router.current_idx].get(col_name, "")
                        if str(raw_val).strip().lower() not in ("nan", "none", ""):
                            is_protected = True
                except: pass

            # --- QUYẾT ĐỊNH ---
            if is_protected:
                # [QUAN TRỌNG] Gặp thằng có dữ liệu -> Bỏ qua, đi xuyên xuống thằng dưới
                continue 
            else:
                # Tìm thấy thằng Rỗng -> Bắt dính ngay!
                target_to_delete = col_name
                break # Dừng lại, không xóa tiếp các thằng rỗng khác bên dưới (nếu có)

        # 3. THỰC HIỆN HÀNH ĐỘNG
        if target_to_delete:
            question = f"CẢNH BÁO: Bạn có muốn XÓA VĨNH VIỄN trường '{target_to_delete}' khỏi file cấu hình không?"
            
            if MsgHelper.ask_yes_no(question, title="Xóa dữ liệu", parent=self.router.view):
                # Gọi Router để xóa key trong JSON và xóa checkbox
                self.router.disable_field(target_to_delete)