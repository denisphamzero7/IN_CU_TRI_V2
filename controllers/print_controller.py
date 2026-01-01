# controllers/print_controller.py
import os
import threading
import time
import gc  # Thư viện quản lý bộ nhớ
import tkinter as tk
from tkinter import messagebox, Toplevel, Button, Label, ttk
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
from helpers.font_manager import FontManager

class PrintController:
    def __init__(self, router):
        self.router = router
        self.model = router.model
        self.selected_size = None
        self.stop_event = threading.Event()  # Cờ để dừng tiến trình

    def print_batch(self):
        # 1. Kiểm tra danh sách in
        if not self.model.selected_indices:
            return messagebox.showwarning("Chú ý", "Chưa chọn người để in!")
        
        # Chuyển set thành list và sắp xếp
        selection = sorted(list(self.model.selected_indices))
        count = len(selection)

        # 2. Kiểm tra ảnh phôi
        if not self.model.template_path:
            return messagebox.showwarning("Lỗi", "Chưa chọn ảnh phôi!")

        # 3. Cảnh báo nếu số lượng quá lớn (> 5000)
        if count > 5000:
            confirm = messagebox.askyesno(
                "Cảnh báo", 
                f"Bạn đang in {count:,} bản ghi.\nViệc này sẽ tốn nhiều thời gian.\nBạn có chắc chắn muốn tiếp tục?"
            )
            if not confirm: return

        # 4. Hỏi khổ giấy (Hàm này trước đó bị thiếu)
        self.ask_paper_size_dialog(count)
        if not self.selected_size: return

        # 5. Thiết lập thông số
        SIZE_MAP = {
            "A3": (3508, 4961), "A4": (2480, 3508),
            "A5": (1748, 2480), "A6": (1240, 1748)
        }
        target_w, target_h = SIZE_MAP.get(self.selected_size, (1748, 2480))

        output_dir = os.path.abspath("ket_qua_in_lon")
        if not os.path.exists(output_dir): os.makedirs(output_dir)

        # Reset cờ dừng và hiển thị loading
        self.stop_event.clear()
        self.show_progress_window(count)

        # 6. Chạy luồng xử lý
        thread = threading.Thread(
            target=self._run_high_performance_print,
            args=(selection, target_w, target_h, output_dir)
        )
        thread.daemon = True
        thread.start()

    def ask_paper_size_dialog(self, count):
        """Hàm hiển thị cửa sổ chọn khổ giấy"""
        self.selected_size = None
        try:
            root_window = self.router.view.winfo_toplevel()
        except AttributeError:
            root_window = self.router.view.master

        dialog = Toplevel(root_window)
        dialog.title("Chọn khổ giấy in")
        dialog.geometry("300x250")
        
        # Căn giữa dialog
        try:
            x = root_window.winfo_x() + (root_window.winfo_width() // 2) - 150
            y = root_window.winfo_y() + (root_window.winfo_height() // 2) - 125
            dialog.geometry(f"+{x}+{y}")
        except: pass

        dialog.transient(root_window)
        dialog.grab_set()
        
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

    def show_progress_window(self, total):
        """Hiển thị cửa sổ tiến trình có nút Hủy"""
        root = self.router.view.winfo_toplevel()
        self.prog_win = Toplevel(root)
        self.prog_win.title("Đang xử lý dữ liệu lớn...")
        self.prog_win.geometry("400x200")
        self.prog_win.transient(root)
        self.prog_win.grab_set()
        
        try:
            x = root.winfo_x() + (root.winfo_width() // 2) - 200
            y = root.winfo_y() + (root.winfo_height() // 2) - 100
            self.prog_win.geometry(f"+{x}+{y}")
        except: pass

        Label(self.prog_win, text="Đang tạo file PDF (Chế độ tối ưu RAM)", font=("Arial", 10, "bold")).pack(pady=10)
        
        self.progress_bar = ttk.Progressbar(self.prog_win, orient="horizontal", length=350, mode="determinate")
        self.progress_bar.pack(pady=5)
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = 0
        
        self.lbl_status = Label(self.prog_win, text=f"0 / {total}")
        self.lbl_status.pack()

        self.lbl_eta = Label(self.prog_win, text="Thời gian còn lại: Đang tính...", fg="blue")
        self.lbl_eta.pack(pady=5)

        def on_cancel():
            if messagebox.askyesno("Hủy", "Bạn có muốn dừng quá trình in không?"):
                self.stop_event.set()
                self.lbl_status.config(text="Đang dừng... vui lòng đợi...")
        
        Button(self.prog_win, text="Dừng lại (Hủy)", command=on_cancel, bg="#e74c3c", fg="white").pack(pady=10)

    def _run_high_performance_print(self, selection, target_w, target_h, output_folder):
        """Hàm xử lý in tối ưu bộ nhớ"""
        BATCH_SIZE = 50 
        pages_buffer = []
        count = len(selection)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        start_time = time.time()
        
        chunk_index = 1
        
        try:
            base_template = Image.open(self.model.template_path).convert("RGB")
            
            for i, idx in enumerate(selection):
                if self.stop_event.is_set():
                    self._finish_print(False, "Người dùng đã hủy bỏ.")
                    return

                try:
                    # Tạo ảnh
                    img = base_template.copy()
                    self._draw_data_on_image(img, int(idx))
                    
                    # Resize
                    cur_w, cur_h = img.size
                    if cur_w > cur_h:
                        final_w, final_h = max(target_w, target_h), min(target_w, target_h)
                    else:
                        final_w, final_h = min(target_w, target_h), max(target_w, target_h)
                    
                    img_resized = img.resize((final_w, final_h), Image.Resampling.LANCZOS)
                    pages_buffer.append(img_resized)
                    
                except Exception as e:
                    print(f"Lỗi data {idx}: {e}")

                # Cập nhật UI mỗi 5 items (cho mượt)
                if i % 5 == 0:
                    elapsed = time.time() - start_time
                    avg_time_per_item = elapsed / (i + 1)
                    remaining_items = count - (i + 1)
                    remaining_time = remaining_items * avg_time_per_item
                    eta_str = str(timedelta(seconds=int(remaining_time)))
                    self.prog_win.after(0, lambda c=i+1, t=eta_str: self._update_ui_safe(c, count, t))

                # Lưu Batch
                if len(pages_buffer) >= BATCH_SIZE or (i == count - 1):
                    part_name = f"Batch_{chunk_index:03d}_{timestamp}.pdf"
                    save_path = os.path.join(output_folder, part_name)
                    
                    if pages_buffer:
                        pages_buffer[0].save(
                            save_path, "PDF", resolution=300.0, 
                            save_all=True, append_images=pages_buffer[1:]
                        )
                    
                    pages_buffer.clear()
                    del pages_buffer
                    pages_buffer = []
                    gc.collect() # Quan trọng: Dọn rác bộ nhớ
                    
                    chunk_index += 1

            self._finish_print(True, output_folder)
            
        except Exception as e:
            self._finish_print(False, str(e))

    def _draw_data_on_image(self, img, idx):
        """Hàm vẽ dữ liệu lên ảnh"""
        draw = ImageDraw.Draw(img)
        row = self.model.df.iloc[idx]
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

    def _update_ui_safe(self, current, total, eta):
        if hasattr(self, 'prog_win') and self.prog_win.winfo_exists():
            self.progress_bar["value"] = current
            self.lbl_status.config(text=f"Đã xử lý: {current} / {total}")
            self.lbl_eta.config(text=f"Còn lại khoảng: {eta}")

    def _finish_print(self, success, message):
        if hasattr(self, 'prog_win') and self.prog_win.winfo_exists():
            self.prog_win.destroy()
        
        if success:
            messagebox.showinfo("Hoàn tất", f"Đã xuất xong!\nThư mục: {message}")
            try: os.startfile(message)
            except: pass
        else:
            if message != "Người dùng đã hủy bỏ.":
                messagebox.showerror("Lỗi", message)
            else:
                messagebox.showinfo("Đã hủy", "Đã dừng quá trình in.")