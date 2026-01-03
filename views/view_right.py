# views/view_right.py
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class RightPanelView(ttk.Frame):
    def __init__(self, parent, router):
        # 1. Kế thừa ttk.Frame để đồng bộ layout
        super().__init__(parent)
        self.pack(fill=BOTH, expand=YES)
        
        # 2. Tạo Canvas
        # Lưu ý: Canvas không có "bootstyle". 
        # Ta set bg="#57606f" (Xám đậm) để làm nền "Workplace" (giống Photoshop).
        # Màu này giúp tờ giấy trắng (Template) nổi bật lên dù ở giao diện Sáng hay Tối.
        self.canvas = tk.Canvas(
            self, 
            # bg="#57606f",      # Màu nền khu vực làm việc (Neutral Dark Grey)
            cursor="fleur",    # Con trỏ dạng di chuyển
            highlightthickness=0 # Bỏ viền trắng khi focus
        )
        self.canvas.pack(fill=BOTH, expand=YES, padx=5, pady=5)
        
        # --- 3. BINDINGS (Sự kiện chuột) ---
        
        # Drag & Drop (Kéo thả)
        self.canvas.tag_bind("draggable", "<ButtonPress-1>", router.on_drag_start)
        self.canvas.tag_bind("draggable", "<B1-Motion>", router.on_drag_motion)
        self.canvas.tag_bind("draggable", "<ButtonRelease-1>", router.on_drag_end)
        
        # Zoom (Phóng to/Nhỏ)
        self.canvas.bind("<Shift-MouseWheel>", router.on_shift_zoom)
        # Hỗ trợ thêm Control-MouseWheel cho quen tay người dùng Windows
        self.canvas.bind("<Control-MouseWheel>", router.on_shift_zoom) 

        # Resize Window (Tự động chỉnh lại khung hình khi kéo to cửa sổ)
        self.canvas.bind("<Configure>", router.on_canvas_resize)