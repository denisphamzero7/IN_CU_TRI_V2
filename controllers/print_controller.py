import os
import threading
import time
import gc
import tkinter as tk
from tkinter import Toplevel, Label, ttk
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageWin
import win32gui
import win32print
import win32ui
import win32con

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

    def print_batch(self, custom_indices=None):
        parent_ui = self._get_parent_window()

        # 1. Kiểm tra danh sách in
        if custom_indices is None or len(custom_indices) == 0:
             return MsgHelper.show_warning("Vui lòng chọn hoặc nhập khoảng cần in!", parent=parent_ui)
        
        selection = sorted(list(custom_indices))
        count = len(selection)

        # 2. Lấy thông tin từ Toolbar
        try:
            printer_name = self.router.view.p_right.cbb_printer.get()
            paper_size = self.router.view.p_right.var_paper_size.get()
            
            # --- [MỚI] Lấy chế độ in (Chỉ dữ liệu / Kèm phôi) ---
            # Giá trị trả về sẽ là "Chỉ dữ liệu" hoặc "Dữ liệu + Phôi"
            print_mode = self.router.view.p_right.cbb_print_mode.get() 
            
            if not printer_name:
                return MsgHelper.show_error("Vui lòng chọn máy in!", parent=parent_ui)
        except AttributeError:
             return MsgHelper.show_error("Không tìm thấy cấu hình trên giao diện!", parent=parent_ui)

        # Validate file phôi (Vẫn cần check để lấy kích thước)
        if not self.model.template_path or not os.path.exists(self.model.template_path):
            return MsgHelper.show_error("Chưa chọn file ảnh phôi (cần file để lấy kích thước)!", parent=parent_ui)

        # 3. Xác nhận
        msg_confirm = (
            f"Xác nhận in {count} thẻ?\n\n"
            f"• Máy in: {printer_name}\n"
            f"• Chế độ: {print_mode.upper()}\n" # Hiển thị chế độ cho chắc chắn
            f"• Khổ giấy: {paper_size}\n"
            f"• Dòng: {selection[0]+1} đến {selection[-1]+1}"
        )

        if MsgHelper.ask_yes_no(msg_confirm, title="Xác nhận in", parent=parent_ui):
            # Truyền thêm print_mode vào thread
            self._start_thread(selection, paper_size, "DIRECT", printer_name, print_mode)

    def _start_thread(self, selection, paper_size, mode, printer_name=None, print_mode_option="Dữ liệu + Phôi"):
        timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
        session_folder = os.path.join(os.path.abspath("KetQuaIn"), f"Lan_In_{timestamp}")
        if not os.path.exists(session_folder):
            os.makedirs(session_folder)

        SIZE_MAP = {
             "A4": (2480, 3508),
            "A5": (1748, 2480), 
            "A6": (1240, 1748)
        }
        target_w, target_h = SIZE_MAP.get(paper_size, (2480, 3508))

        self.stop_event.clear()
        self.errors_log = []
        
        self.show_progress_window(len(selection), mode)

        thread = threading.Thread(
            target=self._run_print_process,
            args=(selection, target_w, target_h, session_folder, mode, printer_name, paper_size, print_mode_option)
        )
        thread.daemon = True
        thread.start()

    def _get_devmode(self, printer_name, paper_size, is_landscape):
        try:
            hPrinter = win32print.OpenPrinter(printer_name)
            printer_info = win32print.GetPrinter(hPrinter, 2)
            devmode = printer_info["pDevMode"]
            win32print.ClosePrinter(hPrinter)

            PAPER_CONSTANTS = { "A4": 9, "A5": 11, "A6": 70 }
            devmode.PaperSize = PAPER_CONSTANTS.get(paper_size, 9) 
            devmode.Orientation = 2 if is_landscape else 1 
            devmode.Fields |= (win32con.DM_PAPERSIZE | win32con.DM_ORIENTATION)
            return devmode
        except Exception as e:
            print(f"Lỗi Devmode: {e}")
            return None

    def _print_image_to_dc(self, hDC, pil_image):
        try:
            hDC.StartPage()
            printer_w = hDC.GetDeviceCaps(win32con.HORZRES)
            printer_h = hDC.GetDeviceCaps(win32con.VERTRES)
            img_w, img_h = pil_image.size
            
            ratio_w = printer_w / img_w
            ratio_h = printer_h / img_h
            scale = min(ratio_w, ratio_h)
            
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            
            x_offset = (printer_w - new_w) // 2
            y_offset = (printer_h - new_h) // 2
            
            dib_dst = (x_offset, y_offset, x_offset + new_w, y_offset + new_h)
            dib = ImageWin.Dib(pil_image)
            dib.draw(hDC.GetHandleOutput(), dib_dst)
            hDC.EndPage()
        except Exception as e: raise e

    def _run_print_process(self, selection, target_w, target_h, output_folder, mode, printer_name, paper_size_name, print_mode_option):
        hDC = None
        start_time = time.time()
        
        if mode == "DIRECT":
            try:
                is_landscape_default = target_w > target_h 
                devmode = self._get_devmode(printer_name, paper_size_name, is_landscape_default)
                
                if devmode:
                    hdc_handle = win32gui.CreateDC("WINSPOOL", printer_name, devmode)
                    hDC = win32ui.CreateDCFromHandle(hdc_handle)
                else:
                    hDC = win32ui.CreateDC()
                    hDC.CreatePrinterDC(printer_name)
                
                hDC.StartDoc(f"Voter Cards {datetime.now().strftime('%H:%M')}")
            except Exception as e:
                self._finish_ui(False, output_folder, f"Lỗi khởi tạo máy in: {e}")
                return

        try:
            # --- [LOGIC QUAN TRỌNG] XỬ LÝ NỀN ---
            real_template = Image.open(self.model.template_path).convert("RGB")
            
            # Nếu chọn "Chỉ dữ liệu": Tạo ảnh nền TRẮNG (White) cùng kích thước
            # Máy in sẽ hiểu màu trắng là không in gì cả -> giữ nguyên phôi giấy
            if print_mode_option == "Chỉ dữ liệu":
                base_template = Image.new("RGB", real_template.size, (255, 255, 255))
            else:
                # Nếu "Dữ liệu + Phôi": Dùng ảnh gốc
                base_template = real_template

            user_angle = getattr(self.router, 'template_rotation', 0)
            count = len(selection)

            for i, idx in enumerate(selection):
                if self.stop_event.is_set(): break
                try:
                    img_draw = base_template.copy()
                    self._draw_data_on_original(img_draw, int(idx))
                    
                    if user_angle == 90: img_final = img_draw.transpose(Image.ROTATE_270)
                    elif user_angle == 180: img_final = img_draw.transpose(Image.ROTATE_180)
                    elif user_angle == 270: img_final = img_draw.transpose(Image.ROTATE_90)
                    else: img_final = img_draw

                    final_w, final_h = target_w, target_h
                    is_img_landscape = img_final.width > img_final.height

                    if is_img_landscape:
                        if final_w < final_h: final_w, final_h = target_h, target_w
                    else:
                        if final_w > final_h: final_w, final_h = target_h, target_w

                    img_ready = self._smart_resize(img_final, final_w, final_h)
                    
                    if mode == "DIRECT":
                        self._print_image_to_dc(hDC, img_ready)

                except Exception as e:
                    self.errors_log.append(f"Dòng {idx+1}: {str(e)}")
                    print(f"Lỗi row {idx}: {e}")

                self._update_ui_progress(i + 1, count, start_time)

            if hDC:
                hDC.EndDoc()
                hDC.DeleteDC()

            if self.stop_event.is_set():
                self._finish_ui(False, output_folder, "Đã hủy in.")
            else:
                self._finish_ui(True, output_folder, "Hoàn thành lệnh in!")

        except Exception as e:
            if hDC: 
                try: hDC.EndDoc()
                except: pass
            self._finish_ui(False, output_folder, f"Lỗi hệ thống: {e}")

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
                    # Paste chữ ký (xử lý transparency nếu có)
                    if sig.mode == 'RGBA':
                        img.paste(sig, (int(x - w/2), int(y - h/2)), sig)
                    else:
                        img.paste(sig, (int(x - w/2), int(y - h/2)))
            else:
                val = str(row.get(col, "")).replace("nan", "")
                if not val: continue 
                if "00:00:00" in val: val = val.split(" ")[0]
                if cfg.get("upper", False): val = val.upper()
                
                font_path = FontManager.get_path(cfg.get("font", "Arial"), cfg.get("bold", False))
                try: font = ImageFont.truetype(font_path, cfg.get("size", 30))
                except: font = ImageFont.load_default()
                
                draw.text((x, y), val, font=font, fill=cfg.get("color", "black"), anchor="mm")

    def _smart_resize(self, img, target_w, target_h):
        bg = Image.new('RGB', (target_w, target_h), (255, 255, 255))
        img_w, img_h = img.size
        ratio = min(target_w / img_w, target_h / img_h)
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        offset_x = (target_w - new_w) // 2
        offset_y = (target_h - new_h) // 2
        bg.paste(img_resized, (offset_x, offset_y))
        return bg

    def show_progress_window(self, total, mode):
        parent = self._get_parent_window()
        self.prog_win = Toplevel(parent)
        apply_window_icon(self.prog_win)
        self.prog_win.title("Đang xử lý...")
        self.prog_win.geometry("400x180")
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 90
            self.prog_win.geometry(f"+{x}+{y}")
        except: pass

        fr = tk.Frame(self.prog_win, padx=20, pady=20)
        fr.pack(fill="both", expand=True)
        
        Label(fr, text="Đang gửi dữ liệu xuống máy in...", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        
        self.progress_bar = ttk.Progressbar(fr, length=350, mode="determinate", maximum=total)
        self.progress_bar.pack(pady=10)
        
        self.lbl_status = Label(fr, text=f"0 / {total}")
        self.lbl_status.pack()
        
        def on_cancel():
            self.stop_event.set()
            self.lbl_status.config(text="Đang dừng...")
        
        tk.Button(fr, text="Dừng lại", command=on_cancel, bg="#c0392b", fg="white").pack(pady=5)

    def _update_ui_progress(self, current, total, start_time):
        if hasattr(self, 'prog_win') and self.prog_win.winfo_exists():
            self.progress_bar["value"] = current
            elapsed = time.time() - start_time
            if current > 0:
                avg = elapsed / current
                rem = int((total - current) * avg)
                eta = str(timedelta(seconds=rem))
            else: eta = "..."
            self.lbl_status.config(text=f"Hoàn thành: {current}/{total} - Còn lại: {eta}")

    def _finish_ui(self, success, output_folder, message):
        if self.router.view:
            self.router.view.after(0, lambda: self._finish_process_ui_thread(success, output_folder, message))

    def _finish_process_ui_thread(self, success, output_folder, message):
        if hasattr(self, 'prog_win') and self.prog_win.winfo_exists():
            self.prog_win.destroy()
        
        if self.errors_log:
            with open(os.path.join(output_folder, "ERRORS.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(self.errors_log))
                
        if success:
            MsgHelper.show_info(message)
        else:
            MsgHelper.show_error(message)