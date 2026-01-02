import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from helpers.ui_helpers import apply_window_icon 

class CustomDialog(ttk.Toplevel):
    def __init__(self, parent, title, message, msg_type="info"):
        super().__init__(parent)
        self.withdraw() # 1. Ẩn cửa sổ ngay lập tức khi vừa khởi tạo
        
        self.title(title)
        self.resizable(False, False)
        self.result = None 

        # Set Icon Title Bar
        apply_window_icon(self) 

        # Cấu hình Modal
        self.transient(parent)
        self.grab_set()

        # --- CẤU HÌNH GIAO DIỆN ---
        CONFIG = {
            "info":     {"char": "ℹ️", "color": "info",    "btn_style": "primary"},
            "warning":  {"char": "⚠️", "color": "warning", "btn_style": "warning"},
            "error":    {"char": "❌", "color": "danger",  "btn_style": "danger"},
            "question": {"char": "❓", "color": "primary", "btn_style": "primary"}
        }
        cfg = CONFIG.get(msg_type, CONFIG["info"])

        # Layout chính
        main_fr = ttk.Frame(self, padding=25) # Tăng padding lên 25 cho thoáng
        main_fr.pack(fill=BOTH, expand=YES)

        # Icon Label
        ttk.Label(
            main_fr, 
            text=cfg["char"], 
            font=("Segoe UI Emoji", 48), # Icon to hơn chút
            bootstyle=cfg["color"]
        ).pack(side=LEFT, anchor="n", padx=(0, 20))

        # Content Frame
        content_fr = ttk.Frame(main_fr)
        content_fr.pack(side=LEFT, fill=BOTH, expand=YES)

        # Message Text
        ttk.Label(
            content_fr, 
            text=message, 
            font=("Segoe UI", 11), # Font chữ nội dung to hơn chút cho dễ đọc
            wraplength=380, 
            justify=LEFT
        ).pack(anchor="w", pady=(5, 20))

        # Button Frame
        btn_fr = ttk.Frame(content_fr)
        btn_fr.pack(anchor="e", fill="x", side=BOTTOM)

        # Tạo nút
        if msg_type == "question":
            ttk.Button(btn_fr, text="Đồng ý", bootstyle="primary", width=12, command=self.on_yes).pack(side=RIGHT, padx=5)
            ttk.Button(btn_fr, text="Hủy", bootstyle="secondary", width=12, command=self.on_close).pack(side=RIGHT)
        else:
            btn_text = "Đóng" if msg_type == "error" else "OK"
            ttk.Button(btn_fr, text=btn_text, bootstyle=cfg["btn_style"], width=12, command=self.on_close).pack(side=RIGHT)

        # --- XỬ LÝ ANIMATION & HIỂN THỊ ---
        
        # 1. Tính toán vị trí ra giữa màn hình
        self.center_window(parent)
        
        # 2. Phát tiếng 'Ding' hệ thống (Tạo cảm giác phản hồi tốt)
        self.bell()
        
        # 3. Hiện lại cửa sổ (nhưng đang trong suốt alpha=0)
        self.deiconify() 
        self.attributes("-alpha", 0.0) 
        
        # 4. Bắt đầu hiệu ứng Fade-in
        self.fade_in()

        # 5. Chờ đóng
        self.wait_window()

    def fade_in(self):
        """ Hiệu ứng hiện dần dần (Fade in) """
        try:
            alpha = self.attributes("-alpha")
            if alpha < 1.0:
                alpha += 0.08  # Tốc độ hiện (càng nhỏ càng mượt nhưng chậm)
                self.attributes("-alpha", alpha)
                # Gọi lại hàm này sau 10ms
                self.after(10, self.fade_in)
            else:
                self.attributes("-alpha", 1.0) # Đảm bảo hiện rõ 100% khi kết thúc
        except:
            pass # Tránh lỗi nếu cửa sổ bị đóng đột ngột khi đang fade

    def on_yes(self):
        self.result = True
        self.destroy()

    def on_close(self):
        self.result = False
        self.destroy()

    def center_window(self, parent):
        try:
            self.update_idletasks()
            w = self.winfo_reqwidth()
            h = self.winfo_reqheight()
            
            if parent:
                # Căn giữa so với cửa sổ cha
                x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (w // 2)
                y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (h // 2)
            else:
                # Căn giữa màn hình
                sw = self.winfo_screenwidth()
                sh = self.winfo_screenheight()
                x = (sw - w) // 2
                y = (sh - h) // 2

            self.geometry(f"+{x}+{y}")
        except: pass