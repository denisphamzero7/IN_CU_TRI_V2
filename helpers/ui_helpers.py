# helpers/ui_helpers.py
import tkinter as tk
import math
from config.settings import COLORS

class RoundedButton(tk.Canvas):
    def __init__(self, master, text="", command=None, width=120, height=40, radius=20, 
                 bg=COLORS["primary"], fg="white", font=("Segoe UI", 10, "bold"), 
                 border_color=None, border_width=0, **kwargs):
        
        # Lấy màu nền của parent để làm màu nền cho Canvas (tránh bị vệt trắng 4 góc)
        parent_bg = master.cget("bg") if hasattr(master, "cget") else COLORS["light"]
        
        super().__init__(master, width=width, height=height, bg=parent_bg, highlightthickness=0, **kwargs)
        
        self.command = command
        self.radius = radius
        self.text_str = text
        self.bg_color = bg
        self.fg_color = fg
        self.font_spec = font
        self.border_color = border_color if border_color else bg
        self.border_width = border_width
        
        # Màu khi di chuột vào (Sáng hơn 1 chút)
        self.hover_color = self._adjust_color_lightness(bg, 1.15)
        # Màu khi bấm xuống (Tối hơn 1 chút)
        self.click_color = self._adjust_color_lightness(bg, 0.85)
        
        self.bind("<Configure>", self._resize)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _adjust_color_lightness(self, color_hex, factor):
        """Hàm làm sáng/tối màu Hex"""
        try:
            r, g, b = int(color_hex[1:3], 16), int(color_hex[3:5], 16), int(color_hex[5:7], 16)
            r, g, b = [max(0, min(int(c * factor), 255)) for c in (r, g, b)]
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return color_hex

    def _resize(self, event):
        """Vẽ lại nút khi kích thước thay đổi"""
        self.delete("all")
        w, h = event.width, event.height
        
        # 1. Vẽ bóng đổ (Shadow) - Vẽ lệch xuống dưới 2px, màu xám nhạt
        # Bóng giúp nút trông "nổi" lên, đẹp hơn phẳng lì
        self._draw_rounded_rect(2, 2, w-2, h-2, self.radius, fill="#bdc3c7", outline="")

        # 2. Vẽ Nút chính (Button Body) - Vẽ đè lên bóng
        # Chừa lề 2px để thấy bóng bên dưới
        self._draw_rounded_rect(0, 0, w-3, h-3, self.radius, 
                                fill=self.bg_color, 
                                outline=self.border_color, 
                                width=self.border_width,
                                tags="bg")
        
        # 3. Vẽ chữ (Text) - Căn giữa
        self.create_text((w-3)/2, (h-3)/2, text=self.text_str, fill=self.fg_color, font=self.font_spec, tags="text")

    def _draw_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        """
        Thuật toán vẽ hình chữ nhật bo tròn sử dụng lượng giác (sin/cos)
        để tạo đường cong mượt mà nhất có thể trên Canvas.
        """
        points = []
        # Đảm bảo bán kính không quá lớn so với kích thước nút
        r = min(r, (x2-x1)/2, (y2-y1)/2)
        
        steps = 20 # Số điểm vẽ cho mỗi góc (càng cao càng mượt)

        # Góc 1: Đông Nam (Góc dưới phải)
        for i in range(steps + 1):
            theta = (0 + i * 90 / steps) * (math.pi / 180)
            points.append(x2 - r + r * math.cos(theta))
            points.append(y2 - r + r * math.sin(theta))

        # Góc 2: Tây Nam (Góc dưới trái)
        for i in range(steps + 1):
            theta = (90 + i * 90 / steps) * (math.pi / 180)
            points.append(x1 + r + r * math.cos(theta))
            points.append(y2 - r + r * math.sin(theta))

        # Góc 3: Tây Bắc (Góc trên trái)
        for i in range(steps + 1):
            theta = (180 + i * 90 / steps) * (math.pi / 180)
            points.append(x1 + r + r * math.cos(theta))
            points.append(y1 + r + r * math.sin(theta))

        # Góc 4: Đông Bắc (Góc trên phải)
        for i in range(steps + 1):
            theta = (270 + i * 90 / steps) * (math.pi / 180)
            points.append(x2 - r + r * math.cos(theta))
            points.append(y1 + r + r * math.sin(theta))

        return self.create_polygon(points, **kwargs, smooth=True)

    def _on_enter(self, event):
        self.itemconfig("bg", fill=self.hover_color)
        self.config(cursor="hand2") # Đổi chuột thành hình bàn tay

    def _on_leave(self, event):
        self.itemconfig("bg", fill=self.bg_color)
        self.config(cursor="")

    def _on_click(self, event):
        # Hiệu ứng nhấn xuống: đổi màu tối hơn & dịch chữ xuống 1 chút
        self.itemconfig("bg", fill=self.click_color)
        self.move("text", 1, 1) 

    def _on_release(self, event):
        # Nhả chuột: trả về màu hover & dịch chữ lại
        self.itemconfig("bg", fill=self.hover_color)
        self.move("text", -1, -1)
        if self.command:
            self.command()