import os
import threading
import time
import win32print
import win32ui
import win32con
import win32gui
import gc
from datetime import datetime, timedelta
from PIL import Image, ImageWin, ImageDraw, ImageFont, ImageFilter
import tkinter as tk
from tkinter import Toplevel, ttk

from helpers.msg_helper import MsgHelper
from helpers.ui_helpers import apply_window_icon
from helpers.font_manager import FontManager
from helpers.date_helpers import format_date_text_vn
from helpers.text_helper import format_cccd

class PrintController:
    PAPER_IDS = {"A4": 9, "A5": 11, "A6": 70}

    def __init__(self, router):
        self.router = router
        self.model = router.model
        self.stop_event = threading.Event()
        self.errors_log = []
        self.prog_win = None
        self.font_cache = {} # [TỐI ƯU] Cache font để không load lại nhiều lần

    def _get_parent_window(self):
        try: return self.router.view.winfo_toplevel()
        except: return self.router.view.master

    def print_batch(self, custom_indices=None):
        parent_ui = self._get_parent_window()
        if not custom_indices:
            return MsgHelper.show_warning("Chưa chọn hàng!", parent=parent_ui)
        
        try:
            printer = self.router.view.p_right.cbb_printer.get()
            size = self.router.view.p_right.var_paper_size.get() 
            mode = self.router.view.p_right.cbb_print_mode.get() 
            is_landscape = getattr(self.router, 'is_paper_landscape', False)
            orientation_text = "Ngang" if is_landscape else "Dọc"
        except Exception as e:
            return MsgHelper.show_error(f"Lỗi cấu hình in: {e}", parent=parent_ui)

        msg = (f"Xác nhận in {len(custom_indices)} thẻ?\n\n"
               f"- Máy in: {printer}\n"
               f"- Khổ: {size} ({orientation_text})\n"
               f"- Chế độ: {mode}")
               
        if MsgHelper.ask_yes_no(msg, title="Xác nhận in", parent=parent_ui):
            self._start_thread(custom_indices, size, is_landscape, printer, mode)

    def _start_thread(self, selection, paper_size, is_landscape, printer_name, print_mode):
        timestamp = datetime.now().strftime("%Hh%Mm%Ss")
        session_folder = os.path.abspath(f"KetQuaIn/In_{timestamp}")
        if not os.path.exists(session_folder): os.makedirs(session_folder)

        self.stop_event.clear()
        self.font_cache = {} # Reset cache trước khi in
        self.show_progress_window(len(selection))

        thread = threading.Thread(
            target=self._run_print_process,
            args=(selection, session_folder, is_landscape, printer_name, paper_size, print_mode)
        )
        thread.daemon = True
        thread.start()

    def _get_devmode(self, printer_name, paper_size, is_landscape):
        try:
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                p_info = win32print.GetPrinter(hPrinter, 2)
                devmode = p_info["pDevMode"]
            finally:
                win32print.ClosePrinter(hPrinter)
            
            if paper_size in self.PAPER_IDS:
                devmode.PaperSize = self.PAPER_IDS[paper_size]
            devmode.Orientation = 2 if is_landscape else 1
            devmode.Fields |= (win32con.DM_PAPERSIZE | win32con.DM_ORIENTATION)
            return devmode
        except Exception as e:
            print(f"Lỗi Get DevMode: {e}")
            return None

    def _run_print_process(self, selection, output_folder, is_landscape, printer_name, paper_size, print_mode):
        hDC = None
        BATCH_SIZE = 50 # Giữ nguyên batch size này là ổn
        
        try:
            # 1. Khởi tạo DC
            devmode = self._get_devmode(printer_name, paper_size, is_landscape)
            if devmode:
                hdc_handle = win32gui.CreateDC("WINSPOOL", printer_name, devmode)
                hDC = win32ui.CreateDCFromHandle(hdc_handle)
            else:
                hDC = win32ui.CreateDC()
                hDC.CreatePrinterDC(printer_name)

            # 2. Tính toán kích thước & Chuẩn bị ảnh nền
            REF_A4_W, REF_A4_H = 595, 842
            SIZE_MAP = {"A4": (595, 842), "A5": (420, 595), "A6": (298, 420), "TheCuTri": (298, 420)}
            target_base_w, target_base_h = SIZE_MAP.get(paper_size, (595, 842))

            if is_landscape:
                ref_w, ref_h = REF_A4_H, REF_A4_W
                target_w, target_h = target_base_h, target_base_w
            else:
                ref_w, ref_h = REF_A4_W, REF_A4_H
                target_w, target_h = target_base_w, target_base_h

            SCALE_RATIO = target_w / ref_w 
            DPI_SCALE = 4.0 
            TOTAL_SCALE = SCALE_RATIO * DPI_SCALE
            final_print_w = int(target_w * DPI_SCALE)
            final_print_h = int(target_h * DPI_SCALE)

            # Load Template
            try:
                original_template = Image.open(self.model.template_path).convert("RGB")
                rot = getattr(self.router, 'template_rotation', 0)
                if rot == 90: original_template = original_template.transpose(Image.ROTATE_270)
                elif rot == 180: original_template = original_template.transpose(Image.ROTATE_180)
                elif rot == 270: original_template = original_template.transpose(Image.ROTATE_90)
            except:
                original_template = Image.new("RGB", (final_print_w, final_print_h), "white")

            if "Chỉ dữ liệu" in print_mode:
                bg_img = Image.new("RGB", (final_print_w, final_print_h), "white")
            else:
                bg_img = original_template.resize((final_print_w, final_print_h), Image.Resampling.LANCZOS)
                bg_img = bg_img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))

            total = len(selection)
            start_time = time.time()
            is_job_active = False 

            # --- VÒNG LẶP CHÍNH ---
            for i, idx in enumerate(selection):
                if self.stop_event.is_set(): break
                
                # Bắt đầu Job in (Batching)
                if i % BATCH_SIZE == 0:
                    batch_num = (i // BATCH_SIZE) + 1
                    job_name = f"Job {batch_num} (Row {i+1}-{min(i+BATCH_SIZE, total)})" 
                    hDC.StartDoc(job_name)
                    is_job_active = True

                try:
                    # Render trang in
                    img_to_print = bg_img.copy() # [TỐN RAM NHẤT Ở ĐÂY NHƯNG CẦN THIẾT]
                    self._draw_data_scaled(img_to_print, int(idx), TOTAL_SCALE)
                    
                    final_img = img_to_print
                    if is_landscape and final_img.height > final_img.width:
                        final_img = final_img.transpose(Image.ROTATE_90)
                    elif not is_landscape and final_img.width > final_img.height:
                        final_img = final_img.transpose(Image.ROTATE_90)

                    self._direct_print_to_dc(hDC, final_img)
                    
                    # Giải phóng RAM ngay lập tức cho ảnh vừa in
                    del img_to_print
                    del final_img

                except Exception as e:
                    self.errors_log.append(f"Row {idx}: {e}")
                    print(f"Error Row {idx}: {e}")

                # Cập nhật UI & Tính thời gian
                elapsed = time.time() - start_time
                if i > 0:
                    avg_time = elapsed / i
                    remain_sec = int((total - i) * avg_time)
                    eta = str(timedelta(seconds=remain_sec))
                else:
                    eta = "..."
                
                # [TỐI ƯU] Cập nhật UI an toàn qua thread-safe wrapper
                self._safe_update_ui(f"Đang xử lý: {i+1}/{total} (Còn: {eta})", i+1)

                # Kết thúc Batch
                if (i + 1) % BATCH_SIZE == 0:
                    hDC.EndDoc()
                    is_job_active = False
                    gc.collect() # Dọn rác bộ nhớ sau mỗi 50 trang
                    time.sleep(0.1) # Nghỉ nhẹ để CPU thở

            if is_job_active:
                hDC.EndDoc()
                gc.collect()

            self._finish_ui(True, output_folder, f"Hoàn thành {total} thẻ!")

        except Exception as e:
            if hDC and is_job_active:
                try: hDC.AbortDoc()
                except: pass
            self._finish_ui(False, output_folder, f"Lỗi hệ thống in: {e}")
        
        finally:
            self.font_cache.clear() # Xóa cache font
            if hDC:
                try: hDC.DeleteDC()
                except: pass

    def _draw_data_scaled(self, img, idx, scale):
        draw = ImageDraw.Draw(img)
        row = self.model.df.iloc[idx]
        config = self.model.get_effective_config(idx)
        
        for col, cfg in config.items():
            if not cfg.get("enable", False): continue
            
            x = int(cfg["x"] * scale)
            y = int(cfg["y"] * scale)
            
            if col == "signature_img":
                sig = self.model.get_signature_image(idx)
                if sig:
                    w = int(cfg.get("w", 150) * scale)
                    h = int(cfg.get("h", 80) * scale)
                    # [TỐI ƯU] Resize chữ ký cũng tốn CPU, nhưng khó cache vì chữ ký mỗi người khác nhau
                    sig = sig.resize((w, h), Image.Resampling.LANCZOS)
                    img.paste(sig, (x - w//2, y - h//2), sig)
            else:
                raw_val = row.get(col, "")
                
                col_idx = -1
                if self.model.df is not None:
                    try: col_idx = self.model.df.columns.get_loc(col)
                    except: pass
                
                val = ""
                # Ưu tiên index cứng như bạn yêu cầu
                if col_idx == 2: val = format_date_text_vn(raw_val) 
                elif col_idx == 4: val = format_cccd(raw_val)         
                else:
                    if str(raw_val).lower() == "nan": val = ""
                    else: val = str(raw_val)
                
                if not val: continue
                if cfg.get("upper", False): val = val.upper()
                
                # --- [TỐI ƯU CỰC MẠNH]: Caching Font ---
                font_key = (cfg.get("font", "Times New Roman"), cfg.get("bold", True), int(cfg.get("size", 21) * scale))
                
                if font_key in self.font_cache:
                    font = self.font_cache[font_key]
                else:
                    # Chỉ load từ ổ cứng nếu chưa có trong cache
                    font_size = font_key[2]
                    font_path = FontManager.get_path(font_key[0], font_key[1])
                    try: 
                        font = ImageFont.truetype(font_path, font_size)
                    except: 
                        font = ImageFont.load_default()
                    self.font_cache[font_key] = font
                # ----------------------------------------
                
                draw.text((x, y), val, font=font, fill=cfg.get("color", "black"), anchor="mm")
                
    def _direct_print_to_dc(self, hDC, pil_image):
        hDC.StartPage()
        printer_w = hDC.GetDeviceCaps(win32con.HORZRES)
        printer_h = hDC.GetDeviceCaps(win32con.VERTRES)
        
        dib = ImageWin.Dib(pil_image)
        dib.draw(hDC.GetHandleOutput(), (0, 0, printer_w, printer_h))
        hDC.EndPage()

    def show_progress_window(self, total):
        parent = self._get_parent_window()
        self.prog_win = Toplevel(parent)
        apply_window_icon(self.prog_win)
        self.prog_win.title("Đang in ấn...")
        self.prog_win.geometry("350x150")
        
        try:
            x = parent.winfo_rootx() + 50
            y = parent.winfo_rooty() + 50
            self.prog_win.geometry(f"+{x}+{y}")
        except: pass

        fr = ttk.Frame(self.prog_win, padding=15)
        fr.pack(fill="both", expand=True)
        
        self.lbl_status = ttk.Label(fr, text="Đang khởi tạo máy in...", font=("Segoe UI", 10))
        self.lbl_status.pack(pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(fr, length=300, mode="determinate", maximum=total)
        self.progress_bar.pack(pady=5, fill="x")
        
        ttk.Button(fr, text="HỦY IN", command=self.stop_event.set).pack(pady=10)
        
        self.prog_win.transient(parent)
        self.prog_win.grab_set()

    # --- [HÀM MỚI]: Cập nhật UI an toàn từ Thread ---
    def _safe_update_ui(self, text, val):
        if hasattr(self, 'prog_win') and self.prog_win and self.prog_win.winfo_exists():
            # Dùng after để đẩy lệnh cập nhật về luồng chính (Main Thread)
            self.prog_win.after(0, lambda: self._update_ui_label_impl(text, val))

    def _update_ui_label_impl(self, text, val):
        # Hàm này chạy ở Main Thread nên an toàn
        try:
            if self.lbl_status.winfo_exists():
                self.lbl_status.config(text=text)
                self.progress_bar["value"] = val
        except: pass

    def _finish_ui(self, s, f, m):
        if self.router.view:
            self.router.view.after(0, lambda: self._finish_process_ui_thread(s, f, m))

    def _finish_process_ui_thread(self, s, f, m):
        try:
            if self.prog_win:
                self.prog_win.grab_release()
                self.prog_win.destroy()
                self.prog_win = None
        except: pass
        
        if s: MsgHelper.show_info(m)
        else: MsgHelper.show_error(m)