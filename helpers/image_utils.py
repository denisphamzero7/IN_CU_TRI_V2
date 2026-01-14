# helpers/image_utils.py
from PIL import Image,ImageDraw

def rotate_pil_image(img, angle):
    """
    Xoay ảnh PIL theo các góc vuông (0, 90, 180, 270).
    Lưu ý: PIL xoay ngược chiều kim đồng hồ, nên cần mapping lại nếu UI của bạn quy ước khác.
    """
    if angle == 0: return img
    
    # Dùng Transpose nhanh hơn và an toàn hơn rotate() cho các góc vuông
    if angle == 90: 
        return img.transpose(Image.ROTATE_270) # 90 độ cùng chiều KĐH = 270 ngược chiều
    elif angle == 180: 
        return img.transpose(Image.ROTATE_180)
    elif angle == 270: 
        return img.transpose(Image.ROTATE_90)
    
    # Trường hợp góc lẻ (nếu sau này cần)
    return img.rotate(-angle, expand=True)
def get_column_from_tags(tags):
    """Tìm và trả về tên cột (field name) từ danh sách tags của Canvas item."""
    for t in tags:
        if t.startswith("col:"):
            return t.split(":")[1]
    return None
def create_text_image(text, font, color="black", is_placeholder=False):
    """
    Tạo ảnh trong suốt chứa text.
    ĐÃ FIX: Tự động căn chỉnh tọa độ để không bị mất chân chữ (g, y, q...) hoặc ngọn chữ.
    """
    if is_placeholder: color = "#bdc3c7"
    
    # 1. Tạo ảnh tạm để tính toán kích thước chính xác
    # Dùng mode RGBA 1x1 để khởi tạo draw
    dummy_draw = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    
    # Lấy hộp bao quanh text (left, top, right, bottom)
    bbox = dummy_draw.textbbox((0, 0), text, font=font)
    
    # Tính kích thước thực tế của nét chữ
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # 2. Thiết lập Padding (vùng đệm)
    # Tăng padding lên để an toàn cho các font thư pháp hoặc in nghiêng
    padding = 10 
    
    img_w = int(text_width + padding)
    img_h = int(text_height + padding)
    
    # 3. Tạo ảnh thật
    img = Image.new('RGBA', (img_w, img_h), (255, 255, 255, 0))
    d = ImageDraw.Draw(img)
    
    # --- [QUAN TRỌNG] TÍNH TOÁN TỌA ĐỘ VẼ ---
    # Thay vì vẽ tại (5,5), ta phải trừ đi bbox[0] và bbox[1] 
    # để đưa nội dung text về gốc tọa độ, sau đó cộng thêm nửa padding để căn giữa.
    # Công thức: x = (Padding / 2) - Left_Bbox
    #            y = (Padding / 2) - Top_Bbox
    
    draw_x = (padding / 2) - bbox[0]
    draw_y = (padding / 2) - bbox[1]
    
    d.text((draw_x, draw_y), text, font=font, fill=color)
    
    return img
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