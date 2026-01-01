# controllers/print_controller.py
import os
import threading  # <--- THÊM MỚI
import tkinter as tk
from tkinter import messagebox, Toplevel, Button, Label, ttk # <--- THÊM ttk
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
from helpers.font_manager import FontManager

class PrintController:
    def __init__(self, router):
        self.router = router
        self.model = router.model
        self.selected_size = None

    def print_batch(self):
        # --- [ĐOẠN MỚI - SỬA LẠI NHƯ SAU] ---
        # Lấy danh sách ID từ Model (nơi lưu trữ toàn bộ các người đã chọn ở TẤT CẢ CÁC TRANG)
        if not self.model.selected_indices:
             return messagebox.showwarning("Chú ý", "Chưa chọn người để in!")
        
        # Chuyển set thành list và sắp xếp theo thứ tự index để in đúng thứ tự
        selection = sorted(list(self.model.selected_indices))
        # ------------------------------------

        if not self.model.template_path:
            return messagebox.showwarning("Lỗi", "Chưa chọn ảnh phôi!")

        count = len(selection)
        
        # 2. Hỏi khổ giấy
        self.ask_paper_size_dialog(count)
        if not self.selected_size: return

        # 3. Chuẩn bị thông số
        SIZE_MAP = {
            "A3": (3508, 4961), "A4": (2480, 3508),
            "A5": (1748, 2480), "A6": (1240, 1748)
        }
        target_w, target_h = SIZE_MAP.get(self.selected_size, (1748, 2480))

        output_dir = os.path.abspath("ket_qua_in")
        if not os.path.exists(output_dir): os.makedirs(output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        merged_pdf_path = os.path.join(output_dir, f"In_{self.selected_size}_{timestamp}.pdf")

        # 4. TẠO CỬA SỔ LOADING (Tiến trình)
        self.show_progress_window(count)

        # 5. CHẠY IN TRÊN LUỒNG RIÊNG (Để không bị lag UI)
        # Truyền tất cả dữ liệu cần thiết vào luồng
        thread = threading.Thread(
            target=self._run_background_print,
            args=(selection, target_w, target_h, merged_pdf_path)
        )
        thread.daemon = True # Tắt thread khi tắt app
        thread.start()

    def show_progress_window(self, total):
        """Hiển thị cửa sổ loading"""
        root = self.router.view.winfo_toplevel()
        self.prog_win = Toplevel(root)
        self.prog_win.title("Đang xử lý...")
        self.prog_win.geometry("300x120")
        
        # Căn giữa
        try:
            x = root.winfo_x() + (root.winfo_width() // 2) - 150
            y = root.winfo_y() + (root.winfo_height() // 2) - 60
            self.prog_win.geometry(f"+{x}+{y}")
        except: pass

        self.prog_win.transient(root)
        self.prog_win.grab_set()
        
        Label(self.prog_win, text="Đang tạo file PDF, vui lòng đợi...", pady=10).pack()
        
        self.progress_bar = ttk.Progressbar(self.prog_win, orient="horizontal", length=250, mode="determinate")
        self.progress_bar.pack(pady=5)
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = 0
        
        self.lbl_status = Label(self.prog_win, text=f"0 / {total}")
        self.lbl_status.pack()

    def _run_background_print(self, selection, target_w, target_h, merged_pdf_path):
        """Hàm này chạy ngầm, không làm đơ giao diện"""
        pages_to_save = []
        count = len(selection)
        
        try:
            # [TỐI ƯU] Load ảnh phôi 1 lần duy nhất ở đây thay vì trong vòng lặp
            base_template = Image.open(self.model.template_path).convert("RGB")
            
            for i, idx in enumerate(selection):
                try:
                    # Copy từ bản gốc ra để vẽ (Nhanh hơn open file nhiều lần)
                    img = base_template.copy() 
                    
                    # Gọi hàm vẽ nội dung lên img
                    self._draw_data_on_image(img, int(idx)) 
                    
                    # Xử lý xoay/resize
                    cur_w, cur_h = img.size
                    if cur_w > cur_h:
                        final_w, final_h = max(target_w, target_h), min(target_w, target_h)
                    else:
                        final_w, final_h = min(target_w, target_h), max(target_w, target_h)
                    
                    img_resized = img.resize((final_w, final_h), Image.Resampling.LANCZOS)
                    pages_to_save.append(img_resized)
                    
                    # Cập nhật thanh tiến trình
                    self._update_progress(i + 1, count)
                    
                except Exception as e:
                    print(f"Lỗi trang {idx}: {e}")

            # Lưu PDF
            if pages_to_save:
                pages_to_save[0].save(
                    merged_pdf_path, "PDF", resolution=300.0, 
                    save_all=True, append_images=pages_to_save[1:]
                )
                self._finish_print(True, merged_pdf_path)
            else:
                self._finish_print(False, "Không tạo được trang nào.")
                
        except Exception as e:
            self._finish_print(False, str(e))

    def _draw_data_on_image(self, img, idx):
        """Hàm tách riêng để vẽ dữ liệu lên ảnh (đã tối ưu code cũ)"""
        draw = ImageDraw.Draw(img)
        row = self.model.df.iloc[idx] # Lưu ý: df phải index chuẩn, hoặc dùng iloc cẩn thận nếu lọc
        # Để an toàn nhất nên lấy row theo ID nếu có cột ID, ở đây giả sử index khớp
        # Nếu model.df là toàn bộ dữ liệu thì idx (từ selection) là đúng.
        
        config = self.model.get_effective_config(idx)
        
        for col, cfg in config.items():
            if not cfg.get("enable", False): continue
            x, y = cfg["x"], cfg["y"]
            
            if col == "signature_img":
                sig = self.model.get_signature_image(idx)
                if sig:
                    w, h = cfg.get("w", 150), cfg.get("h", 80)
                    sig = sig.resize((w, h), Image.Resampling.LANCZOS)
                    img.paste(sig, (int(x - w/2), int(y - h/2)), sig)
            else:
                val = str(row.get(col, "")).replace("nan", "")
                if "00:00:00" in val: val = val.split(" ")[0]
                if cfg.get("upper", False): val = val.upper()
                
                font_path = FontManager.get_path(cfg.get("font", "Arial"), cfg.get("bold", False))
                try:
                    font = ImageFont.truetype(font_path, cfg.get("size", 30))
                except:
                    font = ImageFont.load_default()
                
                draw.text((x, y), val, font=font, fill=cfg.get("color", "black"), anchor="mm")

    def _update_progress(self, current, total):
        """Cập nhật UI từ Thread (An toàn)"""
        if hasattr(self, 'prog_win') and self.prog_win.winfo_exists():
            self.progress_bar["value"] = current
            self.lbl_status.config(text=f"Đang xử lý: {current} / {total}")
            self.prog_win.update_idletasks() # Bắt buộc để UI vẽ lại ngay

    def _finish_print(self, success, message):
        """Kết thúc quá trình"""
        if hasattr(self, 'prog_win') and self.prog_win.winfo_exists():
            self.prog_win.destroy()
            
        if success:
            messagebox.showinfo("Thành công", "Xuất file PDF xong!\nBấm OK để mở.")
            try:
                os.startfile(message)
            except: pass
        else:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra:\n{message}")

    def ask_paper_size_dialog(self, count):
        # (Giữ nguyên code cũ của hàm này)
        self.selected_size = None
        try:
            root_window = self.router.view.winfo_toplevel()
        except AttributeError:
            root_window = self.router.view.master

        dialog = Toplevel(root_window)
        dialog.title("Chọn khổ giấy in")
        dialog.geometry("300x250")
        dialog.transient(root_window)
        dialog.grab_set()
        
        try:
            x = root_window.winfo_x() + 100
            y = root_window.winfo_y() + 100
            dialog.geometry(f"+{x}+{y}")
        except: pass
        
        Label(dialog, text=f"Bạn muốn in {count} thẻ theo khổ giấy nào?", font=("Segoe UI", 10), pady=10).pack()

        def set_size(size):
            self.selected_size = size
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill="both", expand=True, padx=20, pady=10)
        btn_opts = {"font": ("Segoe UI", 10, "bold"), "height": 2, "width": 20, "bg": "#ecf0f1"}

        Button(btn_frame, text="Khổ A4 (Thông dụng)", command=lambda: set_size("A4"), **btn_opts).pack(pady=2)
        Button(btn_frame, text="Khổ A5 (Vừa phải)", command=lambda: set_size("A5"), **btn_opts).pack(pady=2)
        Button(btn_frame, text="Khổ A6 (Nhỏ)", command=lambda: set_size("A6"), **btn_opts).pack(pady=2)
        
        root_window.wait_window(dialog)