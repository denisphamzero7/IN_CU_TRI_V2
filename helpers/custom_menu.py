import tkinter as tk
import ttkbootstrap as ttk

class CustomMenu(tk.Toplevel):
    def __init__(self, parent, x, y, title=None, width=200):
        super().__init__(parent)
        # 1. Ẩn và set trong suốt 100% ngay từ đầu
        self.withdraw()
        self.attributes('-alpha', 0.0) 
        
        # 2. Cấu hình cửa sổ không viền
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        
        # 3. Định vị trí
        self.geometry(f"{width}x1+{x}+{y}") 

        # --- CẤU HÌNH MÀU CỨNG (CHUẨN HÌNH 2) ---
        # Màu này sẽ hiển thị NGAY LẬP TỨC
        self.colors = {
            "border":    "#004085",  # Viền xanh đậm
            "bg":        "#dae6f3",  # Nền xanh nhạt (Màu bạn muốn thấy luôn)
            "fg":        "#004085",  # Chữ xanh đậm
            "hover_bg":  "#ffffff",  # Di chuột vào thì sáng lên (Trắng)
            "hover_fg":  "#005082",  # Chữ khi di chuột
            "separator": "#a0a0a0",  
            "title_fg":  "#888888"
        }

        # Set màu nền cho chính cửa sổ gốc để tránh lọt màu trắng
        self.configure(bg=self.colors["border"])

        # 4. Layout
        self.border_frame = tk.Frame(self, bg=self.colors["border"])
        self.border_frame.pack(fill="both", expand=True)

        self.inner_frame = tk.Frame(self.border_frame, bg=self.colors["bg"])
        self.inner_frame.pack(fill="both", expand=True, padx=1, pady=1)

        # 5. Tiêu đề
        if title:
            lbl_title = tk.Label(self.inner_frame, text=f" {title} ", 
                                 bg=self.colors["bg"], fg=self.colors["title_fg"], 
                                 font=("Segoe UI", 8, "italic"), anchor="w", padx=8, pady=4)
            lbl_title.pack(fill="x")
            
            div = tk.Frame(self.inner_frame, height=1, bg=self.colors["separator"])
            div.pack(fill="x", padx=2)

        # 6. Sự kiện đóng
        self.bind("<FocusOut>", self.close)
        self.bind("<Button-1>", self.close)

    def add_command(self, label, command):
        """Thêm dòng lệnh - Đảm bảo màu nền được set ngay khi tạo"""
        btn = tk.Label(self.inner_frame, 
                       text=f"  {label}", 
                       bg=self.colors["bg"], # <--- QUAN TRỌNG: Set màu xanh ngay tại đây
                       fg=self.colors["fg"],
                       font=("Segoe UI", 9, "bold"), 
                       anchor="w", 
                       padx=10, 
                       pady=6, 
                       cursor="hand2")
        
        btn.pack(fill="x")

        # --- Hiệu ứng Hover ---
        def on_enter(e):
            if btn.winfo_exists():
                btn.configure(bg=self.colors["hover_bg"], fg=self.colors["hover_fg"])

        def on_leave(e):
            if btn.winfo_exists():
                btn.configure(bg=self.colors["bg"], fg=self.colors["fg"])

        def on_click(e):
            self.destroy()
            if command:
                self.after(10, command)

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.bind("<Button-1>", on_click)

    def show(self):
        """Kỹ thuật hiển thị chống nháy màu trắng"""
        # 1. Tính toán layout
        self.update_idletasks() 
        try:
            req_h = self.border_frame.winfo_reqheight()
            geom = self.geometry().split('+')
            self.geometry(f"{geom[0].split('x')[0]}x{req_h}+{geom[1]}+{geom[2]}")
        except: pass

        # 2. Báo hệ điều hành hiển thị cửa sổ (nhưng vẫn tàng hình alpha=0)
        self.deiconify()
        
        # 3. QUAN TRỌNG: Bắt buộc vẽ xong màu sắc rồi mới chạy tiếp
        self.update() 

        # 4. Focus
        self.focus_set() 

        # 5. Hiện hình (Lúc này màu đã được tô xong nên sẽ thấy Xanh luôn)
        self.attributes("-alpha", 1.0)

    def close(self, event=None):
        self.destroy()