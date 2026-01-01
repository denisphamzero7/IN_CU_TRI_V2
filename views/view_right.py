# views/view_right.py
import tkinter as tk
from config.settings import COLORS

class RightPanelView:
    def __init__(self, parent, router):
        # Sử dụng highlightthickness=0 để bỏ viền trắng mặc định của canvas khi focus
        self.canvas = tk.Canvas(parent, bg="#95a5a6", cursor="fleur", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Bindings cho Drag & Drop
        self.canvas.tag_bind("draggable", "<ButtonPress-1>", router.on_drag_start)
        self.canvas.tag_bind("draggable", "<B1-Motion>", router.on_drag_motion)
        self.canvas.tag_bind("draggable", "<ButtonRelease-1>", router.on_drag_end)
        
        # Binding cho Zoom
        self.canvas.bind("<Shift-MouseWheel>", router.on_shift_zoom)

        # --- THÊM DÒNG NÀY: Bắt sự kiện thay đổi kích thước cửa sổ ---
        self.canvas.bind("<Configure>", router.on_canvas_resize)