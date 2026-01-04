import os
import threading
import time
import gc
import tkinter as tk
from tkinter import Toplevel, Label, ttk, messagebox
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageWin
import win32gui
import win32print
import win32ui
import win32con

from helpers.font_manager import FontManager
from helpers.msg_helper import MsgHelper
from helpers.ui_helpers import apply_window_icon, create_button

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
        """
        Hàm xử lý in:
        1. Nhận danh sách hàng từ Router (bắt buộc).
        2. Lấy máy in, khổ giấy từ Toolbar.
        3. Hỏi Yes/No.
        4. In luôn.
        """
        parent_ui = self._get_parent_window()

        # --- 1. SỬA LỖI: CHẶN IN DÒNG ĐANG CHỌN ---
        # Nếu danh sách in rỗng -> Báo lỗi. KHÔNG tự lấy dòng đang bôi đen nữa.
        if custom_indices is None or len(custom_indices) == 0:
             return MsgHelper.show_warning("Vui lòng nhập khoảng  cần in!", parent=parent_ui)
        
        selection = sorted(list(custom_indices))
        count = len(selection)

        # --- 2. LẤY THÔNG TIN TỪ TOOLBAR ---
        try:
            # Lấy tên máy in đang chọn trên thanh công cụ
            printer_name = self.router.view.p_right.cbb_printer.get()
            if not printer_name:
                return MsgHelper.show_error("Vui lòng chọn máy in trên thanh công cụ!", parent=parent_ui)
            
            # Lấy khổ giấy
            paper_size = self.router.view.p_right.var_paper_size.get()
        except AttributeError:
             return MsgHelper.show_error("Không tìm thấy cấu hình trên giao diện!", parent=parent_ui)

        # Validate file phôi
        if not self.model.template_path or not os.path.exists(self.model.template_path):
            return MsgHelper.show_error("File ảnh phôi chưa được chọn!", parent=parent_ui)

        # --- 3. HỎI XÁC NHẬN (ĐƠN GIẢN) ---
        msg_confirm = (
            f"Bạn có muốn in {count} thẻ?\n\n"
            f"• Máy in: {printer_name}\n"
            f"• Khổ giấy: {paper_size}\n"
            f"• Các hàng: {selection[0]+1} đến {selection[-1]+1}"
        )

        if MsgHelper.ask_yes_no(msg_confirm, title="Xác nhận in ngay", parent=parent_ui):
            # --- 4. IN LUÔN (BỎ QUA DIALOG CẤU HÌNH) ---
            self._start_thread(selection, paper_size, "DIRECT", printer_name)

    def _start_thread(self, selection, paper_size, mode, printer_name=None):
        timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
        session_folder = os.path.join(os.path.abspath("KetQuaIn"), f"Lan_In_{timestamp}")
        if not os.path.exists(session_folder):
            os.makedirs(session_folder)

        # Kích thước pixel cho 300 DPI (xấp xỉ)
        SIZE_MAP = {
             "A4": (2480, 3508),
            "A5": (1748, 2480), 
            "A6": (1240, 1748)
        }
        target_w, target_h = SIZE_MAP.get(paper_size, (2480, 3508))

        self.stop_event.clear()
        self.errors_log = []
        
        # Hiển thị thanh tiến trình
        self.show_progress_window(len(selection), mode)

        thread = threading.Thread(
            target=self._run_print_process,
            args=(selection, target_w, target_h, session_folder, mode, printer_name, paper_size)
        )
        thread.daemon = True
        thread.start()

    def show_progress_window(self, total, mode):
        parent = self._get_parent_window()
        self.prog_win = Toplevel(parent)
        apply_window_icon(self.prog_win)
        
        title_txt = "Đang in trực tiếp..." if mode == "DIRECT" else "Đang xuất PDF..."
        self.prog_win.title(title_txt)
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

        Label(main_fr, text=title_txt, font=("Segoe UI", 12, "bold"), fg="#2c3e50").pack(anchor="w")
        Label(main_fr, text="Vui lòng giữ kết nối máy in và không tắt app.", font=("Segoe UI", 9, "italic"), fg="#7f8c8d").pack(anchor="w", pady=(0, 10))

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

        tk.Button(main_fr, text="HỦY BỎ", command=on_cancel, bg="#c0392b", fg="white", bd=0, padx=15, pady=5, cursor="hand2").pack(pady=(15, 0), anchor="e")

    def _get_devmode(self, printer_name, paper_size, is_landscape):
        try:
            hPrinter = win32print.OpenPrinter(printer_name)
            printer_info = win32print.GetPrinter(hPrinter, 2)
            devmode = printer_info["pDevMode"]
            win32print.ClosePrinter(hPrinter)

            # Mã khổ giấy Windows API
            PAPER_CONSTANTS = { "A4": 9, "A5": 11, "A6": 70 }
            
            devmode.PaperSize = PAPER_CONSTANTS.get(paper_size, 9) 
            devmode.Orientation = 2 if is_landscape else 1 
            devmode.Fields |= (win32con.DM_PAPERSIZE | win32con.DM_ORIENTATION)
            
            return devmode
        except Exception as e:
            print(f"Lỗi cấu hình Devmode: {e}")
            return None

    def _run_print_process(self, selection, target_w, target_h, output_folder, mode, printer_name, paper_size_name):
        BATCH_SIZE = 50 
        pages_buffer = []
        count = len(selection)
        start_time = time.time()
        chunk_index = 1
        
        hDC = None
        if mode == "DIRECT":
            try:
                # Logic: Nếu ảnh template chiều ngang > dọc -> Landscape
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
            base_template = Image.open(self.model.template_path).convert("RGB")
            user_angle = self.router.template_rotation

            for i, idx in enumerate(selection):
                if self.stop_event.is_set(): break
                try:
                    img_draw = base_template.copy()
                    self._draw_data_on_original(img_draw, int(idx))
                    
                    # Xử lý xoay ảnh
                    if user_angle == 90: img_final = img_draw.transpose(Image.ROTATE_270)
                    elif user_angle == 180: img_final = img_draw.transpose(Image.ROTATE_180)
                    elif user_angle == 270: img_final = img_draw.transpose(Image.ROTATE_90)
                    else: img_final = img_draw

                    # Xử lý hướng giấy
                    final_w, final_h = target_w, target_h
                    is_img_landscape = img_final.width > img_final.height

                    if is_img_landscape:
                        if final_w < final_h: final_w, final_h = target_h, target_w
                    else:
                        if final_w > final_h: final_w, final_h = target_h, target_w

                    img_ready = self._smart_resize(img_final, final_w, final_h)
                    
                    if mode == "PDF":
                        pages_buffer.append(img_ready)
                    else:
                        self._print_image_to_dc(hDC, img_ready)

                except Exception as e:
                    self.errors_log.append(f"Dòng {idx+1}: {str(e)}")
                    print(f"Lỗi row {idx}: {e}")

                # Cập nhật tiến độ
                if i % 2 == 0 or i == count - 1:
                    elapsed = time.time() - start_time
                    avg = elapsed / (i + 1)
                    rem_sec = int((count - i) * avg)
                    eta_str = str(timedelta(seconds=rem_sec))
                    self.prog_win.after(0, lambda c=i+1, t=eta_str: self._update_ui(c, count, t))

                # Logic ghi file PDF theo Batch
                if mode == "PDF":
                    if len(pages_buffer) >= BATCH_SIZE or (i == count - 1):
                        if pages_buffer:
                            pdf_name = f"File_{chunk_index:03d}.pdf"
                            save_path = os.path.join(output_folder, pdf_name)
                            pages_buffer[0].save(save_path, "PDF", resolution=300.0, save_all=True, append_images=pages_buffer[1:])
                        pages_buffer.clear()
                        gc.collect() 
                        chunk_index += 1

            if hDC:
                hDC.EndDoc()
                hDC.DeleteDC() 

            if self.stop_event.is_set():
                self._finish_ui(False, output_folder, "Đã hủy bởi người dùng.")
            else:
                msg = "Hoàn thành lệnh in!" if mode == "DIRECT" else "Đã xuất xong PDF!"
                self._finish_ui(True, output_folder, msg)

        except Exception as e:
            if hDC: 
                try: hDC.EndDoc()
                except: pass
            self._finish_ui(False, output_folder, f"Lỗi hệ thống: {e}")

    def _print_image_to_dc(self, hDC, pil_image):
        try:
            hDC.StartPage()
            printer_w = hDC.GetDeviceCaps(win32con.HORZRES)
            printer_h = hDC.GetDeviceCaps(win32con.VERTRES)
            img_w, img_h = pil_image.size
            
            # Tính tỉ lệ scale vừa khít trang
            ratio_w = printer_w / img_w
            ratio_h = printer_h / img_h
            scale = min(ratio_w, ratio_h)
            
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            
            # Căn giữa
            x_offset = (printer_w - new_w) // 2
            y_offset = (printer_h - new_h) // 2
            
            dib_dst = (x_offset, y_offset, x_offset + new_w, y_offset + new_h)
            dib = ImageWin.Dib(pil_image)
            dib.draw(hDC.GetHandleOutput(), dib_dst)
            hDC.EndPage()
        except Exception as e: raise e

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
            if "PDF" in message: 
                if MsgHelper.ask_yes_no(f"{message}\nMở thư mục kết quả?", title="Thành công"):
                    os.startfile(output_folder)
            else:
                MsgHelper.show_info(message, title="Thành công")
        else:
            MsgHelper.show_error(message)

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