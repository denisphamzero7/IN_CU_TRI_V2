from PIL import Image, ImageTk, ImageFont, ImageDraw
import tkinter as tk
from helpers.font_manager import FontManager
# --- IMPORT HELPERS MỚI ---
from helpers.image_utils import rotate_pil_image, get_column_from_tags, create_text_image

class CanvasController:
    def __init__(self, router):
        self.router = router
        self.model = router.model
        
        self.tk_image = None    
        self.sig_refs = {}      
        self.scale_factor = 1.0     
        self.zoom_multiplier = 0.8  
        
        self.img_origin_x = 0       
        self.img_origin_y = 0       
        self.pan_offset_x = 0
        self.pan_offset_y = 0

        self.orig_w = 0
        self.orig_h = 0

        self.view = None 
        self.drag_data = {"x": 0, "y": 0, "item": None, "mode": None}
        self.text_img_refs = [] 

    # --- HÀM HELPER MỚI ĐƯỢC THÊM VÀO CLASS ---
    def screen_to_data_coords(self, screen_x, screen_y):
        """Chuyển tọa độ click chuột trên màn hình về tọa độ lưu trong DB (đã trừ offset, zoom, xoay)"""
        # 1. Trừ Pan và Offset gốc
        rel_x = screen_x - self.img_origin_x
        rel_y = screen_y - self.img_origin_y
        
        # 2. Chia tỉ lệ Zoom
        rot_x = rel_x / self.scale_factor
        rot_y = rel_y / self.scale_factor
        
        # 3. Đảo ngược góc xoay
        return self._get_unrotated_coords(rot_x, rot_y)

    def on_resize(self, event):
        self.render()

    def render(self):
        if not self.router.view: return
        canvas = self.router.view.p_right.canvas
        canvas.delete("all") 
        self.text_img_refs = [] 
        
        # 1. Tính toán kích thước Canvas
        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        if cw < 50: cw = 800
        if ch < 50: ch = 600
        cx, cy = cw // 2, ch // 2 

        # 2. Lấy cấu hình khổ giấy
        try:
            p_mid = self.router.view.p_mid
            paper_size = p_mid.var_paper_size.get()
            is_landscape = False 
        except:
            paper_size = "A4"
            is_landscape = False
        
        SIZE_MAP = {"A4": (595, 842), "A5": (420, 595), "A6": (298, 420)}
        w_base, h_base = SIZE_MAP.get(paper_size, (595, 842))

        if is_landscape: paper_w, paper_h = h_base, w_base
        else: paper_w, paper_h = w_base, h_base

        disp_paper_w = int(paper_w * self.zoom_multiplier)
        disp_paper_h = int(paper_h * self.zoom_multiplier)

        paper_x1 = cx + self.pan_offset_x - disp_paper_w // 2
        paper_y1 = cy + self.pan_offset_y - disp_paper_h // 2
        paper_x2 = paper_x1 + disp_paper_w
        paper_y2 = paper_y1 + disp_paper_h

        # 3. Vẽ nền giấy
        canvas.create_rectangle(paper_x1 + 5, paper_y1 + 5, paper_x2 + 5, paper_y2 + 5, fill="#2f3640", outline="", tags="bg_shadow")
        canvas.create_rectangle(paper_x1, paper_y1, paper_x2, paper_y2, fill="white", outline="#bdc3c7", width=2, tags="draggable_paper")

        self.img_origin_x = paper_x1
        self.img_origin_y = paper_y1
        self.scale_factor = self.zoom_multiplier
        self.orig_w = paper_w 
        self.orig_h = paper_h

        # 4. Vẽ ảnh phôi (Template)
        if self.model.template_path:
            try:
                pil_img = Image.open(self.model.template_path)
                self.orig_w, self.orig_h = pil_img.size 
                
                # --- UPDATE 1: DÙNG HELPER XOAY ẢNH ---
                pil_img = rotate_pil_image(pil_img, self.router.template_rotation)

                iw, ih = pil_img.size
                fit_ratio = min(paper_w / iw, paper_h / ih)
                self.scale_factor = fit_ratio * self.zoom_multiplier
                
                final_w = int(iw * self.scale_factor)
                final_h = int(ih * self.scale_factor)

                if final_w > 0 and final_h > 0:
                    img_resized = pil_img.resize((final_w, final_h), Image.Resampling.LANCZOS)
                    self.tk_image = ImageTk.PhotoImage(img_resized)
                    
                    self.img_origin_x = paper_x1 + (disp_paper_w - final_w) // 2
                    self.img_origin_y = paper_y1 + (disp_paper_h - final_h) // 2
                    
                    canvas.create_image(self.img_origin_x, self.img_origin_y, image=self.tk_image, anchor="nw", tags="draggable_paper")

            except Exception as e:
                print(f"Render Error: {e}")
        else:
            canvas.create_text(cx, cy, text="Chưa chọn ảnh phôi", fill="#bdc3c7", font=("Arial", 14), justify="center")

        # 5. Vẽ dữ liệu Overlay
        if self.model.df is not None and not self.model.df.empty:
            self._render_overlay(canvas, paper_x1, paper_y1, paper_x2, paper_y2)

    def _create_placeholder_image(self, w, h, text="Vị trí ảnh"):
        # (Hàm này bạn viết tốt rồi, giữ nguyên hoặc cũng có thể chuyển ra helper nếu thích)
        img = Image.new('RGBA', (w, h), (200, 230, 255, 100)) 
        draw = ImageDraw.Draw(img)
        draw.rectangle([0, 0, w-1, h-1], outline="#2980b9", width=2)
        try:
            font_size = int(min(w, h) / 4)
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(((w - text_w) / 2, (h - text_h) / 2), text, fill="#2980b9", font=font)
        return img

    def _render_overlay(self, canvas, px1, py1, px2, py2):
        idx = self.router.current_idx
        if idx >= len(self.model.df): return

        row = self.model.df.iloc[idx]
        config = self.model.get_effective_config(idx)
        self.sig_refs = {}
        
        angle = self.router.template_rotation

        for col, cfg in config.items():
            if not cfg.get("enable", False): continue
            
            raw_x, raw_y = cfg["x"], cfg["y"]
            rot_x, rot_y = self._get_rotated_coords(raw_x, raw_y)
            
            sx = self.img_origin_x + rot_x * self.scale_factor
            sy = self.img_origin_y + rot_y * self.scale_factor
            
            tag_id = f"col:{col}"
            
            # --- XỬ LÝ ẢNH (CHỮ KÝ / PLACEHOLDER) ---
            if col == "signature_img":
                w = int(cfg.get("w", 150) * self.scale_factor)
                h = int(cfg.get("h", 80) * self.scale_factor)
                
                sig_img = self.model.get_signature_image(idx)
                if not sig_img:
                    sig_img = self._create_placeholder_image(w, h, text="Chữ ký")
                else:
                    sig_img = sig_img.resize((w, h), Image.Resampling.LANCZOS)

                # --- UPDATE 2: DÙNG HELPER XOAY ẢNH ---
                sig_img = rotate_pil_image(sig_img, angle)

                self.sig_refs[col] = ImageTk.PhotoImage(sig_img)
                canvas.create_image(sx, sy, image=self.sig_refs[col], anchor="center", tags=("draggable", tag_id))
                
                disp_w = sig_img.width
                disp_h = sig_img.height
                canvas.create_rectangle(sx-disp_w/2, sy-disp_h/2, sx+disp_w/2, sy+disp_h/2, outline="#3498db", dash=(2, 4), tags=("draggable", tag_id))

            # --- XỬ LÝ TEXT ---
            else:
                val = str(row.get(col, "")).replace("nan", "")
                if "00:00:00" in val: val = val.split(" ")[0]
                if cfg.get("upper", False): val = val.upper()
                
                display_val = val if val.strip() != "" else f"[{col}]"
                is_placeholder = (val.strip() == "")

                f_size = cfg.get("size", 30)
                font_path = FontManager.get_path(cfg.get("font", "Arial"), cfg.get("bold", False))
                try: pil_font = ImageFont.truetype(font_path, f_size)
                except: pil_font = ImageFont.load_default()

                fill_color = cfg.get("color", "black")

                # --- UPDATE 3: DÙNG HELPER TẠO VÀ XOAY TEXT ---
                # 3a. Tạo ảnh text
                txt_img = create_text_image(display_val, pil_font, fill_color, is_placeholder)
                
                # 3b. Xoay ảnh text
                txt_img = rotate_pil_image(txt_img, angle)
                
                # 3c. Resize hiển thị
                final_w = int(txt_img.width * self.scale_factor)
                final_h = int(txt_img.height * self.scale_factor)
                
                if final_w > 0 and final_h > 0:
                    txt_img = txt_img.resize((final_w, final_h), Image.Resampling.LANCZOS)
                
                tk_txt_img = ImageTk.PhotoImage(txt_img)
                self.text_img_refs.append(tk_txt_img)
                
                canvas.create_image(sx, sy, image=tk_txt_img, anchor="center", tags=("draggable", tag_id))
                canvas.create_rectangle(sx-final_w/2, sy-final_h/2, sx+final_w/2, sy+final_h/2, outline="#bdc3c7", dash=(1, 4), tags=("draggable", tag_id), state="hidden")

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
                
                # --- UPDATE 4: DÙNG HELPER PARSE TAG ---
                col_name = get_column_from_tags(tags)
                
                if col_name and self.router.selected_field != col_name:
                    self.router.select_field(col_name)
                    # Chọn tất cả các item có tag col:name (ví dụ cả ảnh và viền)
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
        
        # --- UPDATE 5: DÙNG HELPER PARSE TAG ---
        col_name = get_column_from_tags(tags)
        
        if col_name:
            try:
                cur_coords = canvas.coords(item_id)
                if len(cur_coords) == 2:
                    screen_x, screen_y = cur_coords[0], cur_coords[1]
                elif len(cur_coords) == 4:
                    screen_x = (cur_coords[0] + cur_coords[2]) / 2
                    screen_y = (cur_coords[1] + cur_coords[3]) / 2
                else: return

                # --- UPDATE 6: DÙNG HÀM TÍNH TOÁN TỌA ĐỘ MỚI ---
                raw_x, raw_y = self.screen_to_data_coords(screen_x, screen_y)
                
                self.router.update_field_config("x", int(raw_x))
                self.router.update_field_config("y", int(raw_y))

                try:
                    current_idx = self.router.current_idx
                    if current_idx in self.model.custom_configs:
                        if col_name in self.model.custom_configs[current_idx]:
                            self.model.custom_configs[current_idx][col_name]['x'] = int(raw_x)
                            self.model.custom_configs[current_idx][col_name]['y'] = int(raw_y)
                except: pass
                
                if self.router.selected_field == col_name:
                    self.router.load_field_props_to_ui()
            except Exception as e:
                print(f"Lỗi drag_end: {e}")

        self.render()
        self.drag_data["item"] = None

    def _get_rotated_coords(self, x, y):
        angle = self.router.template_rotation
        w, h = self.orig_w, self.orig_h
        if angle == 0: return x, y
        elif angle == 90: return h - y, x
        elif angle == 180: return w - x, h - y
        elif angle == 270: return y, w - x
        return x, y

    def _get_unrotated_coords(self, rot_x, rot_y):
        angle = self.router.template_rotation
        w, h = self.orig_w, self.orig_h
        if angle == 0: return rot_x, rot_y
        elif angle == 90: return rot_y, h - rot_x
        elif angle == 180: return w - rot_x, h - rot_y
        elif angle == 270: return w - rot_y, rot_x
        return rot_x, rot_y

    def handle_zoom(self, event):
        if event.delta > 0: self.zoom_multiplier *= 1.1
        else: self.zoom_multiplier /= 1.1
        if self.zoom_multiplier < 0.2: self.zoom_multiplier = 0.2
        if self.zoom_multiplier > 3.0: self.zoom_multiplier = 3.0
        self.render()