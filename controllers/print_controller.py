import os
import threading
import time
import win32print
import win32ui
import win32con
import win32gui
from datetime import datetime, timedelta
from PIL import Image, ImageWin, ImageDraw, ImageFont
from helpers.msg_helper import MsgHelper
from helpers.ui_helpers import apply_window_icon
from helpers.font_manager import FontManager
import tkinter as tk
from tkinter import Toplevel, ttk

class PrintController:
    # Mã giấy chuẩn Windows: 9=A4, 11=A5, 70=A6. 
    # Nếu máy in dùng khổ Custom, nó có thể không khớp mã này, nhưng A4/A5 là chuẩn.
    PAPER_IDS = {"A4": 9, "A5": 11, "A6": 70}

    def __init__(self, router):
        self.router = router
        self.model = router.model
        self.stop_event = threading.Event()
        self.errors_log = [] 
        self.prog_win = None

    def _get_parent_window(self):
        try: return self.router.view.winfo_toplevel()
        except: return self.router.view.master

    def print_batch(self, custom_indices=None):
        parent_ui = self._get_parent_window()
        if not custom_indices: 
            return MsgHelper.show_warning("Chưa chọn hàng!", parent=parent_ui)
        
        try:
            # Lấy thông tin từ UI
            printer = self.router.view.p_right.cbb_printer.get()
            size = self.router.view.p_right.var_paper_size.get() # A4, A5...
            mode = self.router.view.p_right.cbb_print_mode.get() # Chế độ in (Dữ liệu/Cả khung)
            
            # Lấy thông tin hướng giấy từ biến router (đã bind với UI radio button)
            # True = Landscape (Ngang), False = Portrait (Dọc)
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
        self.show_progress_window(len(selection))

        thread = threading.Thread(
            target=self._run_print_process,
            args=(selection, session_folder, is_landscape, printer_name, paper_size, print_mode)
        )
        thread.daemon = True
        thread.start()

    def _get_devmode(self, printer_name, paper_size, is_landscape):
        """
        Cấu hình Driver máy in (Khổ giấy, Hướng giấy)
        """
        try:
            hPrinter = win32print.OpenPrinter(printer_name)
            try:
                p_info = win32print.GetPrinter(hPrinter, 2)
                devmode = p_info["pDevMode"]
            finally:
                win32print.ClosePrinter(hPrinter)
            
            # 1. Cấu hình khổ giấy
            if paper_size in self.PAPER_IDS:
                devmode.PaperSize = self.PAPER_IDS[paper_size]
            
            # 2. Cấu hình hướng giấy (1=Portrait, 2=Landscape)
            devmode.Orientation = 2 if is_landscape else 1
            
            # Báo cho Windows biết mình đã thay đổi field nào
            devmode.Fields |= (win32con.DM_PAPERSIZE | win32con.DM_ORIENTATION)
            return devmode
        except Exception as e:
            print(f"Lỗi Get DevMode: {e}")
            return None

    def _run_print_process(self, selection, output_folder, is_landscape, printer_name, paper_size, print_mode):
        hDC = None
        try:
            # 1. Khởi tạo DC (Device Context) cho máy in
            devmode = self._get_devmode(printer_name, paper_size, is_landscape)
            
            if devmode:
                hdc_handle = win32gui.CreateDC("WINSPOOL", printer_name, devmode)
                hDC = win32ui.CreateDCFromHandle(hdc_handle)
            else:
                # Fallback nếu không chỉnh được setting
                hDC = win32ui.CreateDC()
                hDC.CreatePrinterDC(printer_name)

            hDC.StartDoc("Voter Cards Batch")

            # 2. Chuẩn bị ảnh gốc (Template)
            real_template = Image.open(self.model.template_path).convert("RGB")
            
            # Nếu chỉ in dữ liệu nền trắng
            if "Chỉ dữ liệu" in print_mode:
                base_img_source = Image.new("RGB", real_template.size, (255, 255, 255))
            else:
                base_img_source = real_template

            total = len(selection)
            start_time = time.time()
            
            # Lấy góc xoay thủ công (nếu người dùng chỉnh trên UI preview)
            manual_rotation = getattr(self.router, 'template_rotation', 0)

            for i, idx in enumerate(selection):
                if self.stop_event.is_set(): break
                try:
                    # A. Vẽ dữ liệu lên ảnh (trên bộ nhớ)
                    # Lưu ý: Luôn vẽ trên bản copy để không hỏng template gốc
                    img_draw = base_img_source.copy()
                    self._draw_data_on_original(img_draw, int(idx))
                    
                    # B. Xử lý Xoay ảnh (Image Rotation)
                    # Logic: Nếu máy in thiết lập NGANG (Landscape), nhưng ảnh đang DỌC,
                    # ta cần xoay ảnh 90 độ để nó nằm ngang khớp với giấy.
                    
                    img_final = img_draw
                    
                    # Xoay theo thiết lập thủ công trước
                    if manual_rotation == 90: img_final = img_final.transpose(Image.ROTATE_270)
                    elif manual_rotation == 180: img_final = img_final.transpose(Image.ROTATE_180)
                    elif manual_rotation == 270: img_final = img_final.transpose(Image.ROTATE_90)

                    # Xoay tự động theo khổ giấy:
                    # Nếu giấy in là Landscape (Ngang) thì ảnh cuối cùng cũng phải nằm Ngang
                    if is_landscape:
                        # Nếu ảnh đang đứng (Cao > Rộng) thì xoay cho nằm xuống
                        if img_final.height > img_final.width:
                             img_final = img_final.transpose(Image.ROTATE_90)
                    else:
                        # Nếu giấy in là Portrait (Dọc)
                        # Nếu ảnh đang nằm ngang (Rộng > Cao) thì xoay cho đứng lên
                        if img_final.width > img_final.height:
                             img_final = img_final.transpose(Image.ROTATE_90)

                    # C. Đẩy xuống Driver máy in
                    self._direct_print_to_dc(hDC, img_final)

                except Exception as e:
                    print(f"Lỗi in dòng {idx}: {e}")
                    self.errors_log.append(f"Row {idx}: {e}")

                # Update Progress Bar
                elapsed = time.time() - start_time
                if i > 0:
                    avg_time = elapsed / i
                    remain_sec = int((total - i) * avg_time)
                    eta = str(timedelta(seconds=remain_sec))
                else:
                    eta = "..."
                
                self._update_ui_label(f"Đang in: {i+1}/{total} (Còn: {eta})", i+1)

            # Kết thúc lệnh in
            hDC.EndDoc()
            self._finish_ui(True, output_folder, "Đã hoàn thành quá trình in!")

        except Exception as e:
            if hDC:
                try: hDC.AbortDoc()
                except: pass
            self._finish_ui(False, output_folder, f"Lỗi hệ thống in: {e}")
        
        finally:
            if hDC:
                try: hDC.DeleteDC()
                except: pass

    def _direct_print_to_dc(self, hDC, pil_image):
        """
        Vẽ ảnh lên DC máy in.
        CHẾ ĐỘ: STRETCH TO FILL (Kéo dãn lấp đầy)
        Mục đích: Loại bỏ viền trắng do phần mềm tạo ra.
        """
        hDC.StartPage()
        
        # 1. Lấy kích thước vùng in khả dụng của máy in (Pixel)
        # Lưu ý: Đây là vùng in được bên trong lề vật lý của máy in
        printer_w = hDC.GetDeviceCaps(win32con.HORZRES)
        printer_h = hDC.GetDeviceCaps(win32con.VERTRES)
        
        # 2. BỎ QUA việc tính toán tỷ lệ (ratio).
        # Ép kích thước ảnh bằng đúng kích thước vùng in.
        # Nếu ảnh gốc và khổ giấy lệch tỷ lệ một chút, ảnh sẽ hơi bị co/dãn nhẹ,
        # nhưng bù lại sẽ lấp đầy trang giấy.
        
        x = 0
        y = 0
        new_w = printer_w
        new_h = printer_h

        # 3. Vẽ ảnh
        dib = ImageWin.Dib(pil_image)
        # Vẽ từ góc 0,0 đến kịch kim chiều rộng và chiều cao máy in cho phép
        dib.draw(hDC.GetHandleOutput(), (x, y, x + new_w, y + new_h))
        
        hDC.EndPage()

    def _draw_data_on_original(self, img, idx):
        # Hàm này giữ nguyên logic vẽ text của bạn
        draw = ImageDraw.Draw(img)
        row = self.model.df.iloc[idx]
        config = self.model.get_effective_config(idx)
        
        for col, cfg in config.items():
            if not cfg.get("enable", False): continue
            
            x, y = cfg["x"], cfg["y"]
            
            # Xử lý Chữ ký (Ảnh)
            if col == "signature_img":
                sig = self.model.get_signature_image(idx)
                if sig:
                    w, h = cfg.get("w", 150), cfg.get("h", 80)
                    sig = sig.resize((w, h), Image.Resampling.LANCZOS)
                    # Căn giữa ảnh chữ ký vào điểm x,y
                    paste_x = int(x - w/2)
                    paste_y = int(y - h/2)
                    if sig.mode == 'RGBA': 
                        img.paste(sig, (paste_x, paste_y), sig)
                    else: 
                        img.paste(sig, (paste_x, paste_y))
            
            # Xử lý Text
            else:
                val = str(row.get(col, "")).replace("nan", "")
                if not val: continue
                
                if "00:00:00" in val: val = val.split(" ")[0]
                if cfg.get("upper", False): val = val.upper()
                
                font_path = FontManager.get_path(cfg.get("font", "Arial"), cfg.get("bold", False))
                try: 
                    font = ImageFont.truetype(font_path, cfg.get("size", 30))
                except: 
                    font = ImageFont.load_default()
                
                # anchor="mm": Middle-Middle (Căn giữa tâm text vào tọa độ x,y)
                draw.text((x, y), val, font=font, fill=cfg.get("color", "black"), anchor="mm")

    def show_progress_window(self, total):
        parent = self._get_parent_window()
        self.prog_win = Toplevel(parent)
        apply_window_icon(self.prog_win)
        self.prog_win.title("Đang in ấn...")
        self.prog_win.geometry("350x150")
        
        # Căn giữa màn hình cha
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
        
        # Chặn tương tác với cửa sổ chính khi đang in
        self.prog_win.transient(parent)
        self.prog_win.grab_set()

    def _update_ui_label(self, text, val):
        if hasattr(self, 'prog_win') and self.prog_win and self.prog_win.winfo_exists():
            self.lbl_status.config(text=text)
            self.progress_bar["value"] = val

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