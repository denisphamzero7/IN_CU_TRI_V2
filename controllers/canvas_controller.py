# controllers/canvas_controller.py
from PIL import Image, ImageTk, ImageFont, ImageDraw
import tkinter as tk
from helpers.font_manager import FontManager

class CanvasController:
    def __init__(self, router):
        self.router = router
        self.model = router.model
        
        # --- QUẢN LÝ TRẠNG THÁI HIỂN THỊ (VIEW STATE) ---
        self.tk_image = None    # Biến giữ ảnh để Tkinter không bị Garbage Collection xóa mất
        self.sig_refs = {}      # Lưu tham chiếu các ảnh chữ ký nhỏ (tránh lỗi mất ảnh)
        
        # --- CÁC BIẾN TỌA ĐỘ VÀ TỶ LỆ ---
        self.scale_factor = 1.0     # Tỷ lệ thu phóng hiện tại của ảnh so với ảnh gốc (VD: 0.5 là nhỏ đi một nửa)
        self.zoom_multiplier = 1.0  # Hệ số zoom do người dùng lăn chuột
        self.img_origin_x = 0       # Tọa độ X góc trên cùng bên trái của ảnh nền trên Canvas
        self.img_origin_y = 0       # Tọa độ Y góc trên cùng bên trái của ảnh nền trên Canvas
        
        # --- TRẠNG THÁI KÉO THẢ (DRAG STATE) ---
        self.drag_data = {"x": 0, "y": 0, "item": None}

    def on_resize(self, event):
        """
        Sự kiện: Khi người dùng thay đổi kích thước cửa sổ phần mềm.
        Hành động: Vẽ lại toàn bộ để ảnh tự động co giãn vừa khung.
        """
        self.render()

    def render(self):
        """
        HÀM VẼ CHÍNH (QUAN TRỌNG NHẤT)
        Nhiệm vụ: Xóa canvas, tính toán tỷ lệ ảnh, vẽ ảnh nền và vẽ các trường dữ liệu lên trên.
        """
        canvas = self.router.view.p_right.canvas
        canvas.delete("all") # Xóa sạch màn hình trước khi vẽ mới
        
        # Nếu chưa chọn ảnh phôi thì hiện thông báo
        if not self.model.template_path:
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            canvas.create_text(w/2, h/2, text="Vui lòng chọn ảnh phôi", fill="white", font=("Segoe UI", 14))
            return

        # 1. Load ảnh gốc từ đường dẫn
        try:
            pil_img = Image.open(self.model.template_path)
        except Exception:
            return

        # Lấy kích thước khung hiển thị (Canvas)
        cw = canvas.winfo_width()
        ch = canvas.winfo_height()
        
        # Fix lỗi: Khi mới mở app, kích thước canvas có thể bị trả về 1x1, gán cứng để không lỗi chia cho 0
        if cw < 50: cw = 800
        if ch < 50: ch = 600
        
        iw, ih = pil_img.size
        
        # --- THUẬT TOÁN "FIT IMAGE": Tự động vừa khít màn hình ---
        # Tìm tỷ lệ nhỏ nhất giữa chiều rộng và chiều cao để ảnh nằm trọn trong khung
        # 0.96 là nhân hệ số để chừa lại 1 chút viền trống cho đẹp
        base_scale = min(cw/iw, ch/ih) * 0.96
        
        # Scale thực tế = Scale cơ bản (Fit) * Scale người dùng lăn chuột (Zoom)
        self.scale_factor = base_scale * self.zoom_multiplier
        
        # Kích thước mới của ảnh sau khi scale
        nw, nh = int(iw * self.scale_factor), int(ih * self.scale_factor)
        
        # Resize ảnh dùng thuật toán LANCZOS (chất lượng cao nhất, tránh răng cưa)
        self.tk_image = ImageTk.PhotoImage(pil_img.resize((nw, nh), Image.Resampling.LANCZOS))
        
        # --- TÍNH TỌA ĐỘ TRUNG TÂM ---
        # Mục đích: Luôn đặt ảnh nằm chính giữa vùng đen của Canvas
        cx, cy = cw//2, ch//2
        self.img_origin_x = cx - nw//2  # Lưu lại gốc X để dùng tính toán vị trí text sau này
        self.img_origin_y = cy - nh//2  # Lưu lại gốc Y
        
        # Vẽ ảnh nền
        canvas.create_image(cx, cy, image=self.tk_image, anchor="center")
        
        # 2. Vẽ các trường thông tin (Tên, ngày sinh, ảnh thẻ...) đè lên ảnh nền
        if self.model.df is not None and not self.model.df.empty:
            self._render_overlay(canvas)

    def _render_overlay(self, canvas):
        """
        Hàm phụ trợ: Vẽ text và ảnh con (chữ ký/ảnh thẻ) lên vị trí đã cấu hình.
        """
        idx = self.router.current_idx # Người thứ mấy trong danh sách
        row = self.model.df.iloc[idx] # Dữ liệu của người đó
        config = self.model.get_effective_config(idx) # Lấy cấu hình (ưu tiên cấu hình riêng nếu có)
        
        self.sig_refs = {} # Reset danh sách tham chiếu ảnh

        for col, cfg in config.items():
            if not cfg.get("enable", False): continue # Nếu trường này bị tắt thì bỏ qua
            
            # --- CÔNG THỨC CHUYỂN ĐỔI TỌA ĐỘ (QUAN TRỌNG) ---
            # Tọa độ màn hình = Gốc ảnh + (Tọa độ thực tế trên giấy * Tỷ lệ scale)
            sx = self.img_origin_x + cfg["x"] * self.scale_factor
            sy = self.img_origin_y + cfg["y"] * self.scale_factor
            
            # Tạo tag ID để nhận diện vật thể này thuộc cột nào (VD: "col:hoten")
            tag_id = f"col:{col}"
            
            # --- TRƯỜNG HỢP LÀ ẢNH (Chữ ký, Ảnh thẻ) ---
            if col == "signature_img":
                w = int(cfg.get("w", 150) * self.scale_factor) # Scale cả chiều rộng
                h = int(cfg.get("h", 80) * self.scale_factor)  # Scale cả chiều cao
                
                sig = self.model.get_signature_image(idx)
                if sig:
                    # Nếu có ảnh: Resize và vẽ ảnh
                    sig_resized = sig.resize((w, h), Image.Resampling.LANCZOS)
                    self.sig_refs[col] = ImageTk.PhotoImage(sig_resized)
                    
                    # Vẽ ảnh
                    canvas.create_image(sx, sy, image=self.sig_refs[col], anchor="center", tags=("draggable", tag_id))
                    # Vẽ thêm khung nét đứt màu xanh bao quanh để dễ nhìn
                    canvas.create_rectangle(sx - w/2, sy - h/2, sx + w/2, sy + h/2, outline="blue", dash=(2, 4), tags=("draggable", tag_id))
                else:
                    # Nếu KHÔNG có ảnh: Vẽ khung đỏ báo hiệu "Chỗ để ảnh"
                    canvas.create_rectangle(sx - w/2, sy - h/2, sx + w/2, sy + h/2, outline="red", width=2, dash=(5, 2), tags=("draggable", tag_id))
                    canvas.create_text(sx, sy, text="CHỖ ĐỂ ẢNH", fill="red", font=("Segoe UI", 8, "bold"), tags=("draggable", tag_id))
            
            # --- TRƯỜNG HỢP LÀ TEXT (Họ tên, ngày sinh...) ---
            else:
                val = str(row.get(col, "")).replace("nan", "")
                if "00:00:00" in val: val = val.split(" ")[0] # Cắt giờ nếu là ngày tháng
                if cfg.get("upper", False): val = val.upper() # Viết hoa nếu chọn
                
                f_sz = int(cfg.get("size", 30) * self.scale_factor) # Scale cỡ chữ
                if f_sz < 1: f_sz = 1

                # Tạo font Tkinter
                tk_font = (cfg.get("font", "Arial"), -f_sz, "bold" if cfg.get("bold", False) else "normal")
                
                # Kiểm tra xem trường này có đang bị "Chỉnh riêng" không
                is_custom = (idx in self.model.custom_configs and col in self.model.custom_configs[idx])
                
                # Logic màu sắc: Nếu đang ở chế độ chỉnh từng người VÀ trường này đã bị sửa riêng -> hiện màu đỏ để cảnh báo
                text_color = cfg.get("color", "black")
                # if is_custom and self.router.edit_mode.get() == "individual":
                #     text_color = "red"

                canvas.create_text(sx, sy, text=val, font=tk_font, fill=text_color, anchor="center", tags=("draggable", tag_id))

    def handle_zoom(self, event):
        """Xử lý lăn chuột để zoom ra/vào"""
        if not self.tk_image: return
        
        if event.delta > 0: self.zoom_multiplier *= 1.1 # Lăn lên: Phóng to
        else: self.zoom_multiplier /= 1.1               # Lăn xuống: Thu nhỏ
        
        # Giới hạn zoom (không quá nhỏ, không quá to)
        if self.zoom_multiplier < 0.1: self.zoom_multiplier = 0.1
        if self.zoom_multiplier > 5.0: self.zoom_multiplier = 5.0
        self.render() # Vẽ lại với tỷ lệ mới

    def drag_start(self, event):
        """Bắt đầu bấm chuột vào vật thể để kéo"""
        canvas = self.router.view.p_right.canvas
        # Tìm vật thể gần nhất tại vị trí chuột click
        items = canvas.find_closest(event.x, event.y)
        if items:
            tags = canvas.gettags(items[0])
            if "draggable" in tags: # Chỉ cho kéo những vật có tag "draggable"
                self.drag_data = {"x": event.x, "y": event.y, "item": items[0]}
                
                # Tìm xem vật thể đó ứng với cột dữ liệu nào (dựa vào tag "col:...")
                for t in tags:
                    if t.startswith("col:"):
                        col_name = t.split(":")[1]
                        self.router.select_field(col_name) # Báo cho menu bên trái biết đang chọn trường nào
                        break

    def drag_motion(self, event):
        """Di chuyển chuột (Đang giữ nút click)"""
        if self.drag_data["item"]:
            # Tính khoảng cách chuột đã di chuyển so với vị trí cũ
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            canvas = self.router.view.p_right.canvas
            
            # --- FIX LOGIC DI CHUYỂN ---
            # Thay vì chỉ di chuyển `item` (ví dụ chỉ cái khung hình chữ nhật), 
            # ta tìm `tag_id` để di chuyển TOÀN BỘ nhóm liên quan (cả khung lẫn ảnh bên trong).
            if self.router.selected_field:
                tag_id = f"col:{self.router.selected_field}"
                canvas.move(tag_id, dx, dy) # Di chuyển cả nhóm
            else:
                canvas.move(self.drag_data["item"], dx, dy) # Fallback
                
            # Cập nhật lại vị trí chuột hiện tại để tính toán cho bước tiếp theo
            self.drag_data.update({"x": event.x, "y": event.y})

    def drag_end(self, event):
        """
        Thả chuột ra (Kết thúc kéo) -> Quan trọng nhất để lưu tọa độ
        """
        if self.drag_data["item"]:
            canvas = self.router.view.p_right.canvas
            coords = canvas.coords(self.drag_data["item"])
            
            # Lấy tọa độ tâm của vật thể sau khi thả
            # Nếu là Text/Image (2 tọa độ x,y) hoặc Rectangle (4 tọa độ x1,y1,x2,y2)
            if len(coords) == 2: cx, cy = coords
            elif len(coords) == 4: cx, cy = (coords[0]+coords[2])/2, (coords[1]+coords[3])/2
            else: cx, cy = 0, 0
            
            # Chỉ lưu nếu đang chọn một trường cụ thể
            if self.router.selected_field and self.scale_factor > 0:
                
                # --- TÍNH TOÁN NGƯỢC (Màn hình -> Thực tế) ---
                # Real_X = (Màn hình - Gốc ảnh) / Tỷ lệ scale
                real_x = int((cx - self.img_origin_x) / self.scale_factor)
                real_y = int((cy - self.img_origin_y) / self.scale_factor)
                
                col_name = self.router.selected_field

                # 1. Lưu vào Router (Router sẽ quyết định lưu vào Global hay Individual config)
                self.router.update_field_config("x", real_x)
                self.router.update_field_config("y", real_y)
                
                # 2. --- BUG FIX: CHỐNG NHẢY VỊ TRÍ (SNAP-BACK) ---
                # Vấn đề: Nếu ta đang chỉnh "Tất cả" (Global), nhưng trang hiện tại đã lỡ có cấu hình riêng (Individual),
                # thì hàm render() sẽ ưu tiên lấy cấu hình riêng cũ -> Vật thể nhảy lại chỗ cũ.
                # Giải pháp: Ép buộc cập nhật luôn cấu hình riêng của trang hiện tại (nếu có) bằng tọa độ mới.
                try:
                    current_idx = self.router.current_idx
                    # Kiểm tra: Nếu trang này ĐANG có config riêng
                    if current_idx in self.model.custom_configs:
                        if col_name in self.model.custom_configs[current_idx]:
                            # Ghi đè tọa độ mới vào config riêng ngay lập tức
                            self.model.custom_configs[current_idx][col_name]['x'] = real_x
                            self.model.custom_configs[current_idx][col_name]['y'] = real_y
                            print(f"Đã cập nhật nóng vị trí (Hot-fix) cho index {current_idx}")
                except Exception as e:
                    print(f"Lỗi cập nhật local config: {e}")
                
                # 3. Vẽ lại toàn bộ để đảm bảo mọi thứ đồng bộ hiển thị
                self.render()
                
        self.drag_data["item"] = None