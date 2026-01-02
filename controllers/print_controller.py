import os
import threading
import time
import gc
import sys
import tkinter as tk
from tkinter import Toplevel, Button, Label, ttk
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

from helpers.font_manager import FontManager
from helpers.msg_helper import MsgHelper
# --- THÊM IMPORT NÀY ĐỂ SET LOGO CHO CỬA SỔ CON ---
from helpers.ui_helpers import apply_window_icon 

class PrintController:
    def __init__(self, router):
        self.router = router
        self.model = router.model
        self.selected_size = None
        self.stop_event = threading.Event()
        self.errors_log = [] 

    # --- Lấy cửa sổ giao diện chính ---
    def _get_parent_window(self):
        try:
            return self.router.view.winfo_toplevel()
        except:
            return self.router.view.master

    def print_batch(self):
        # 1. Lấy parent UI
        parent_ui = self._get_parent_window()

        # 2. Validate dữ liệu (Truyền parent vào đây để hiện CustomDialog có Logo)
        if not self.model.selected_indices:
            return MsgHelper.show_warning("Chưa chọn người để in!", parent=parent_ui)
        
        if not self.model.template_path or not os.path.exists(self.model.template_path):
            return MsgHelper.show_error("File ảnh phôi không tồn tại hoặc chưa chọn!", parent=parent_ui)

        selection = sorted(list(self.model.selected_indices))
        count = len(selection)

        # 3. Cảnh báo số lượng lớn
        if count > 2000:
            msg = f"Bạn đang in {count:,} thẻ.\nQuá trình này có thể mất vài phút.\nBạn có muốn tiếp tục?"
            if not MsgHelper.ask_yes_no(msg, title="Xác nhận", parent=parent_ui):
                return

        # 4. Chọn khổ giấy
        self.ask_paper_size_dialog(count)
        if not self.selected_size: return

        # 5. Chuẩn bị thư mục
        timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
        root_output = os.path.abspath("KetQuaIn")
        session_folder = os.path.join(root_output, f"Lan_In_{timestamp}")
        
        if not os.path.exists(session_folder):
            os.makedirs(session_folder)

        # 6. Chạy luồng in
        SIZE_MAP = {
            "A3": (3508, 4961), "A4": (2480, 3508),
            "A5": (1748, 2480), "A6": (1240, 1748)
        }
        target_w, target_h = SIZE_MAP.get(self.selected_size, (1748, 2480))

        self.stop_event.clear()
        self.errors_log = []
        self.show_progress_window(count)

        thread = threading.Thread(
            target=self._run_print_process,
            args=(selection, target_w, target_h, session_folder)
        )
        thread.daemon = True
        thread.start()

    def ask_paper_size_dialog(self, count):
        self.selected_size = None
        parent = self._get_parent_window() # Lấy parent

        dialog = Toplevel(parent)
        
        # --- CẬP NHẬT: Set Logo cho cửa sổ này ---
        apply_window_icon(dialog)
        # -----------------------------------------
        
        dialog.title("Chọn Khổ Giấy")
        dialog.geometry("350x280")
        
        # Căn giữa popup theo parent
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 175
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 140
            dialog.geometry(f"+{x}+{y}")
        except: pass
        
        dialog.transient(parent)
        dialog.grab_set()

        Label(dialog, text="CẤU HÌNH IN", font=("Segoe UI", 12, "bold"), fg="#2980b9").pack(pady=(15, 5))
        Label(dialog, text=f"Tổng số lượng: {count} thẻ", font=("Segoe UI", 10)).pack()
        Label(dialog, text="Vui lòng chọn khổ giấy đầu ra:", font=("Segoe UI", 10)).pack(pady=5)

        def set_size(size):
            self.selected_size = size
            dialog.destroy()

        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill="both", expand=True, padx=30, pady=10)
        
        btns = [
            ("Khổ A4 (Thông dụng nhất)", "A4", "#2ecc71"),
            ("Khổ A5 (Vừa vặn)", "A5", "#3498db"),
            ("Khổ A6 (Nhỏ - Tiết kiệm)", "A6", "#95a5a6")
        ]

        for text, val, color in btns:
            btn = Button(btn_frame, text=text, command=lambda v=val: set_size(v),
                         bg=color, fg="white", font=("Segoe UI", 10, "bold"), height=2, bd=0, cursor="hand2")
            btn.pack(fill="x", pady=3)
        
        parent.wait_window(dialog)

    def show_progress_window(self, total):
        parent = self._get_parent_window()
        self.prog_win = Toplevel(parent)
        
        # --- CẬP NHẬT: Set Logo cho cửa sổ tiến trình ---
        apply_window_icon(self.prog_win)
        # -----------------------------------------------
        
        self.prog_win.title("Đang Xử Lý...")
        self.prog_win.geometry("450x220")
        
        self.prog_win.transient(parent)
        self.prog_win.grab_set()
        
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 225
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 110
            self.prog_win.geometry(f"+{x}+{y}")
        except: pass

        main_fr = tk.Frame(self.prog_win, padx=20, pady=20)
        main_fr.pack(fill="both", expand=True)

        Label(main_fr, text="Đang xuất file PDF...", font=("Segoe UI", 12, "bold"), fg="#2c3e50").pack(anchor="w")
        Label(main_fr, text="Vui lòng không tắt phần mềm.", font=("Segoe UI", 9, "italic"), fg="#7f8c8d").pack(anchor="w", pady=(0, 10))

        self.progress_bar = ttk.Progressbar(main_fr, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=5, fill="x")
        self.progress_bar["maximum"] = total
        
        self.lbl_status = Label(main_fr, text=f"Tiến độ: 0 / {total}", font=("Segoe UI", 10))
        self.lbl_status.pack(anchor="w")

        self.lbl_eta = Label(main_fr, text="Thời gian còn lại: Đang tính toán...", font=("Segoe UI", 10), fg="#e67e22")
        self.lbl_eta.pack(anchor="w")

        def on_cancel():
            # Truyền self.prog_win làm parent để hiện popup CustomDialog đè lên thanh tiến trình
            if MsgHelper.ask_yes_no("Bạn có chắc chắn muốn hủy?", title="Xác nhận Hủy", parent=self.prog_win):
                self.stop_event.set()
                self.lbl_status.config(text="⚠️ Đang dừng tiến trình... vui lòng đợi...")

        Button(main_fr, text="HỦY QUÁ TRÌNH", command=on_cancel, bg="#c0392b", fg="white", bd=0, padx=15, pady=5, cursor="hand2").pack(pady=(15, 0), anchor="e")

    def _run_print_process(self, selection, target_w, target_h, output_folder):
        BATCH_SIZE = 50 
        pages_buffer = []
        count = len(selection)
        start_time = time.time()
        chunk_index = 1
        
        try:
            base_template = Image.open(self.model.template_path).convert("RGB")
            
            for i, idx in enumerate(selection):
                if self.stop_event.is_set():
                    self._finish(False, output_folder, "Người dùng đã hủy bỏ.")
                    return

                try:
                    img = base_template.copy()
                    self._draw_data(img, int(idx))
                    
                    cur_w, cur_h = img.size
                    if (cur_w > cur_h) != (target_w > target_h):
                         t_w, t_h = max(target_w, target_h), min(target_w, target_h)
                    else:
                         t_w, t_h = target_w, target_h

                    img_resized = img.resize((t_w, t_h), Image.Resampling.LANCZOS)
                    pages_buffer.append(img_resized)
                    
                except Exception as e:
                    self.errors_log.append(f"Dòng {idx+1}: {str(e)}")

                if i % 2 == 0:
                    elapsed = time.time() - start_time
                    if i > 0:
                        avg = elapsed / i
                        rem_sec = int((count - i) * avg)
                        eta_str = str(timedelta(seconds=rem_sec))
                    else:
                        eta_str = "..."
                    self.prog_win.after(0, lambda c=i+1, t=eta_str: self._update_ui(c, count, t))

                if len(pages_buffer) >= BATCH_SIZE or (i == count - 1):
                    if pages_buffer:
                        pdf_name = f"File_{chunk_index:03d}_(Dong_{i-len(pages_buffer)+2}-{i+1}).pdf"
                        save_path = os.path.join(output_folder, pdf_name)
                        pages_buffer[0].save(save_path, "PDF", resolution=300.0, save_all=True, append_images=pages_buffer[1:])
                    pages_buffer.clear()
                    gc.collect() 
                    chunk_index += 1

            self._finish(True, output_folder, "Hoàn thành!")

        except Exception as e:
            self._finish(False, output_folder, f"Lỗi nghiêm trọng: {e}")

    def _draw_data(self, img, idx):
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
            self.lbl_status.config(text=f"Tiến độ: {current} / {total}")
            self.lbl_eta.config(text=f"Còn lại khoảng: {eta}")

    def _finish(self, success, output_folder, message):
        if threading.current_thread() is not threading.main_thread():
            self.router.view.after(0, lambda: self._finish(success, output_folder, message))
            return

        if hasattr(self, 'prog_win') and self.prog_win.winfo_exists():
            self.prog_win.destroy()
        
        parent_ui = self._get_parent_window()

        if self.errors_log:
            log_path = os.path.join(output_folder, "ERRORS_LOG.txt")
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("\n".join(self.errors_log))
            
            if success:
                MsgHelper.show_warning(f"Đã xuất xong kèm {len(self.errors_log)} lỗi.\nXem: {output_folder}", title="Cảnh báo", parent=parent_ui)
            else:
                MsgHelper.show_error(message, title="Thất bại", parent=parent_ui)
        else:
            if success:
                if MsgHelper.ask_yes_no(f"Xuất xong.\nMở thư mục ngay?", title="Thành công", parent=parent_ui):
                    try: os.startfile(output_folder)
                    except: pass
            else:
                MsgHelper.show_error(message, parent=parent_ui)