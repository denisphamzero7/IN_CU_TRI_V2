import os
import threading
import time
import gc
import tkinter as tk
from tkinter import Toplevel, Button, Label, ttk
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

from helpers.font_manager import FontManager
from helpers.msg_helper import MsgHelper
from helpers.ui_helpers import apply_window_icon 

class PrintController:
    def __init__(self, router):
        self.router = router
        self.model = router.model
        self.stop_event = threading.Event()
        self.errors_log = [] 

    def _get_parent_window(self):
        try:
            return self.router.view.winfo_toplevel()
        except:
            return self.router.view.master

    def print_batch(self):
        parent_ui = self._get_parent_window()

        # 1. Validate dữ liệu
        if not self.model.selected_indices:
            return MsgHelper.show_warning("Chưa chọn người để in!", parent=parent_ui)
        
        if not self.model.template_path or not os.path.exists(self.model.template_path):
            return MsgHelper.show_error("File ảnh phôi chưa được chọn!", parent=parent_ui)

        selection = sorted(list(self.model.selected_indices))
        count = len(selection)

        # 2. Lấy cấu hình khổ giấy từ MidPanel
        try:
            view_mid = self.router.view.p_mid
            paper_size = view_mid.var_paper_size.get() 
        except:
            paper_size = "A4"

        # 3. Chuẩn bị thư mục output
        timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
        session_folder = os.path.join(os.path.abspath("KetQuaIn"), f"Lan_In_{timestamp}")
        if not os.path.exists(session_folder):
            os.makedirs(session_folder)

        # 4. Tính toán kích thước (300 DPI)
        # "A3": (3508, 4961),
        SIZE_MAP = {
             "A4": (2480, 3508),
            "A5": (1748, 2480), "A6": (1240, 1748)
        }
        target_w, target_h = SIZE_MAP.get(paper_size, (2480, 3508))

        # 5. Khởi chạy tiến trình
        self.stop_event.clear()
        self.errors_log = []
        self.show_progress_window(count)

        thread = threading.Thread(
            target=self._run_print_process,
            args=(selection, target_w, target_h, session_folder)
        )
        thread.daemon = True
        thread.start()

    def show_progress_window(self, total):
        parent = self._get_parent_window()
        self.prog_win = Toplevel(parent)
        apply_window_icon(self.prog_win)
        
        self.prog_win.title("Tiến độ in ấn")
        self.prog_win.geometry("450x220")
        self.prog_win.transient(parent)
        self.prog_win.grab_set()
        
        # Căn giữa popup
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 225
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 110
            self.prog_win.geometry(f"+{x}+{y}")
        except: pass

        main_fr = tk.Frame(self.prog_win, padx=20, pady=20)
        main_fr.pack(fill="both", expand=True)

        Label(main_fr, text="Đang xuất file PDF...", font=("Segoe UI", 12, "bold"), fg="#2c3e50").pack(anchor="w")
        Label(main_fr, text="Vui lòng không tắt chương trình.", font=("Segoe UI", 9, "italic"), fg="#7f8c8d").pack(anchor="w", pady=(0, 10))

        self.progress_bar = ttk.Progressbar(main_fr, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=5, fill="x")
        self.progress_bar["maximum"] = total
        
        self.lbl_status = Label(main_fr, text=f"Đã xử lý: 0 / {total}", font=("Segoe UI", 10))
        self.lbl_status.pack(anchor="w")

        self.lbl_eta = Label(main_fr, text="Thời gian còn lại: Đang tính toán...", font=("Segoe UI", 10), fg="#e67e22")
        self.lbl_eta.pack(anchor="w")

        def on_cancel():
            if MsgHelper.ask_yes_no("Dừng quá trình in hiện tại?", title="Xác nhận", parent=self.prog_win):
                self.stop_event.set()
                self.lbl_status.config(text="⚠️ Đang dừng... vui lòng đợi...")

        Button(main_fr, text="HỦY BỎ", command=on_cancel, bg="#c0392b", fg="white", bd=0, padx=15, pady=5, cursor="hand2").pack(pady=(15, 0), anchor="e")

    def _run_print_process(self, selection, target_w, target_h, output_folder):
        BATCH_SIZE = 50 
        pages_buffer = []
        count = len(selection)
        start_time = time.time()
        chunk_index = 1
        
        try:
            base_template = Image.open(self.model.template_path).convert("RGB")
            user_angle = self.router.template_rotation

            for i, idx in enumerate(selection):
                if self.stop_event.is_set():
                    self._finish_ui(False, output_folder, "Đã hủy bởi người dùng.")
                    return

                try:
                    # Logic Vẽ và Xoay đồng bộ
                    img_draw = base_template.copy()
                    self._draw_data_on_original(img_draw, int(idx))
                    
                    # Xoay theo cấu hình hiện tại
                    if user_angle == 90: img_final = img_draw.transpose(Image.ROTATE_270)
                    elif user_angle == 180: img_final = img_draw.transpose(Image.ROTATE_180)
                    elif user_angle == 270: img_final = img_draw.transpose(Image.ROTATE_90)
                    else: img_final = img_draw

                    # Resize về khổ giấy đích
                    img_resized = img_final.resize((target_w, target_h), Image.Resampling.LANCZOS)
                    pages_buffer.append(img_resized)
                except Exception as e:
                    self.errors_log.append(f"Dòng {idx+1}: {str(e)}")

                # Tính toán thời gian (ETA) mỗi 2 bản ghi
                if i % 2 == 0 or i == count - 1:
                    elapsed = time.time() - start_time
                    if i > 0:
                        avg = elapsed / i
                        rem_sec = int((count - i) * avg)
                        eta_str = str(timedelta(seconds=rem_sec))
                    else: eta_str = "..."
                    self.prog_win.after(0, lambda c=i+1, t=eta_str: self._update_ui(c, count, t))

                # Xuất PDF theo từng Batch để tránh tràn RAM
                if len(pages_buffer) >= BATCH_SIZE or (i == count - 1):
                    if pages_buffer:
                        pdf_name = f"File_{chunk_index:03d}.pdf"
                        save_path = os.path.join(output_folder, pdf_name)
                        pages_buffer[0].save(save_path, "PDF", resolution=300.0, save_all=True, append_images=pages_buffer[1:])
                    pages_buffer.clear()
                    gc.collect() 
                    chunk_index += 1

            self._finish_ui(True, output_folder, "Hoàn thành!")

        except Exception as e:
            self._finish_ui(False, output_folder, f"Lỗi: {e}")

    def _draw_data_on_original(self, img, idx):
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
                if not val: continue 
                if "00:00:00" in val: val = val.split(" ")[0]
                if cfg.get("upper", False): val = val.upper()
                font_path = FontManager.get_path(cfg.get("font", "Arial"), cfg.get("bold", False))
                try: font = ImageFont.truetype(font_path, cfg.get("size", 30))
                except: font = ImageFont.load_default()
                draw.text((x, y), val, font=font, fill=cfg.get("color", "black"), anchor="mm")

    def _update_ui(self, current, total, eta):
        if hasattr(self, 'prog_win') and self.prog_win.winfo_exists():
            self.progress_bar["value"] = current
            self.lbl_status.config(text=f"Đã xử lý: {current} / {total}")
            self.lbl_eta.config(text=f"Thời gian còn lại: {eta}")

    def _finish_ui(self, success, output_folder, message):
        self.router.view.after(0, lambda: self._finish_process(success, output_folder, message))

    def _finish_process(self, success, output_folder, message):
        if hasattr(self, 'prog_win') and self.prog_win.winfo_exists():
            self.prog_win.destroy()
        
        if self.errors_log:
            with open(os.path.join(output_folder, "ERRORS.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(self.errors_log))

        if success:
            if MsgHelper.ask_yes_no(f"Đã xuất xong. Mở thư mục kết quả?", title="Thành công"):
                os.startfile(output_folder)
        else:
            MsgHelper.show_error(message)