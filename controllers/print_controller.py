import os
import threading
import time
import gc
import tkinter as tk
from tkinter import Toplevel, Label, ttk
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont, ImageWin

# Import Win32 cho in ấn
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

    def print_batch(self):
        parent_ui = self._get_parent_window()

        # 1. Validate dữ liệu
        if not self.model.selected_indices:
            return MsgHelper.show_warning("Chưa chọn người để in!", parent=parent_ui)
        
        if not self.model.template_path or not os.path.exists(self.model.template_path):
            return MsgHelper.show_error("File ảnh phôi chưa được chọn!", parent=parent_ui)

        selection = sorted(list(self.model.selected_indices))
        count = len(selection)

        # 2. Hiển thị Dialog chọn phương thức in
        self.show_print_options_dialog(selection, count)

    def show_print_options_dialog(self, selection, count):
        """Hiện popup để user chọn Xuất PDF hay In trực tiếp"""
        parent = self._get_parent_window()
        dialog = Toplevel(parent)
        dialog.title("Cấu hình in ấn")
        dialog.geometry("400x300")
        apply_window_icon(dialog)
        dialog.transient(parent)
        dialog.grab_set()
        
        # Center dialog
        try:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 150
            dialog.geometry(f"+{x}+{y}")
        except: pass

        # -- UI Components --
        lbl = Label(dialog, text=f"Đã chọn {count} bản ghi.", font=("Segoe UI", 12, "bold"))
        lbl.pack(pady=15)

        # Combo chọn máy in
        lbl_printer = Label(dialog, text="Chọn máy in (nếu in trực tiếp):")
        lbl_printer.pack(pady=(5, 0))
        
        # Lấy danh sách máy in từ Windows
        printers = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        default_printer = win32print.GetDefaultPrinter()
        
        cbo_printers = ttk.Combobox(dialog, values=printers, state="readonly", width=40)
        cbo_printers.pack(pady=5)
        if default_printer in printers:
            cbo_printers.set(default_printer)
        elif printers:
            cbo_printers.current(0)

        # Biến lưu khổ giấy
        try:
            paper_size = self.router.view.p_mid.var_paper_size.get()
        except:
            paper_size = "A4"

        # Hàm xử lý start
        def start_process(mode):
            printer_name = cbo_printers.get() if mode == "DIRECT" else None
            dialog.destroy()
            self._start_thread(selection, paper_size, mode, printer_name)

        # Buttons
        f_btns = tk.Frame(dialog, pady=20)
        f_btns.pack(fill="x")

        create_button(f_btns, "Xuất ra PDF", lambda: start_process("PDF"), style="info", width=15).pack(side="left", padx=20)
        create_button(f_btns, "In Ngay", lambda: start_process("DIRECT"), style="success", width=15).pack(side="right", padx=20)

    def _start_thread(self, selection, paper_size, mode, printer_name=None):
        # 3. Chuẩn bị thư mục output (chỉ dùng nếu xuất PDF hoặc lưu log)
        timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%Mm%Ss")
        session_folder = os.path.join(os.path.abspath("KetQuaIn"), f"Lan_In_{timestamp}")
        if not os.path.exists(session_folder):
            os.makedirs(session_folder)

        # 4. Kích thước logic (Template thiết kế ở 300 DPI)
        SIZE_MAP = {
             "A4": (2480, 3508),
            "A5": (1748, 2480), "A6": (1240, 1748)
        }
        target_w, target_h = SIZE_MAP.get(paper_size, (2480, 3508))

        # 5. Khởi chạy tiến trình
        self.stop_event.clear()
        self.errors_log = []
        self.show_progress_window(len(selection), mode)

        thread = threading.Thread(
            target=self._run_print_process,
            args=(selection, target_w, target_h, session_folder, mode, printer_name)
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
        
        # Căn giữa popup
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
    def _run_print_process(self, selection, target_w, target_h, output_folder, mode, printer_name):
        BATCH_SIZE = 50 
        pages_buffer = []
        count = len(selection)
        start_time = time.time()
        chunk_index = 1
        
        # Setup Printer Context
        hDC = None
        if mode == "DIRECT":
            try:
                hDC = win32ui.CreateDC()
                hDC.CreatePrinterDC(printer_name)
                hDC.StartDoc(f"Batch Print {datetime.now().strftime('%H:%M')}")
            except Exception as e:
                self._finish_ui(False, output_folder, f"Không thể kết nối máy in: {e}")
                return

        try:
            base_template = Image.open(self.model.template_path).convert("RGB")
            user_angle = self.router.template_rotation

            for i, idx in enumerate(selection):
                if self.stop_event.is_set(): break

                try:
                    # 1. Vẽ dữ liệu
                    img_draw = base_template.copy()
                    self._draw_data_on_original(img_draw, int(idx))
                    
                    # 2. Xoay theo người dùng chỉnh (nếu có)
                    if user_angle == 90: img_final = img_draw.transpose(Image.ROTATE_270)
                    elif user_angle == 180: img_final = img_draw.transpose(Image.ROTATE_180)
                    elif user_angle == 270: img_final = img_draw.transpose(Image.ROTATE_90)
                    else: img_final = img_draw

                    # 3. [TỐI ƯU A4/A5/A6] Tự động xoay khổ giấy theo ảnh
                    # target_w, target_h là kích thước gốc (ví dụ A5 dọc: 1748x2480) được truyền vào từ bên ngoài
                    
                    final_w, final_h = target_w, target_h
                    
                    # Kiểm tra: Nếu ảnh đang là NGANG (Rộng > Cao)
                    if img_final.width > img_final.height:
                        # Nhưng khổ giấy đang là DỌC (Rộng < Cao) -> Cần Đảo chiều khổ giấy
                        if final_w < final_h:
                            final_w, final_h = target_h, target_w # Swap thành Ngang
                    else:
                        # Ảnh DỌC, nhưng khổ giấy đang NGANG -> Đảo chiều khổ giấy về Dọc
                        if final_w > final_h:
                            final_w, final_h = target_h, target_w # Swap về Dọc

                    # 4. Smart Resize vào khổ giấy chuẩn (A4/A5/A6)
                    # Lúc này final_w, final_h đã đúng là A4/A5/A6 Ngang hoặc Dọc
                    img_ready = self._smart_resize(img_final, final_w, final_h)
                    
                    if mode == "PDF":
                        pages_buffer.append(img_ready)
                    else:
                        # In trực tiếp
                        self._print_image_to_dc(hDC, img_ready)

                except Exception as e:
                    self.errors_log.append(f"Dòng {idx+1}: {str(e)}")
                    print(f"Lỗi: {e}")

                # ... (Phần Update UI và Save PDF giữ nguyên không đổi) ...
                if i % 2 == 0 or i == count - 1:
                    elapsed = time.time() - start_time
                    avg = elapsed / (i + 1)
                    rem_sec = int((count - i) * avg)
                    eta_str = str(timedelta(seconds=rem_sec))
                    self.prog_win.after(0, lambda c=i+1, t=eta_str: self._update_ui(c, count, t))

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
                msg = "Hoàn thành! Đã gửi lệnh in xuống máy." if mode == "DIRECT" else "Đã xuất xong file PDF!"
                self._finish_ui(True, output_folder, msg)

        except Exception as e:
            if hDC: 
                try: hDC.EndDoc()
                except: pass
            self._finish_ui(False, output_folder, f"Lỗi hệ thống: {e}")

    def _print_image_to_dc(self, hDC, pil_image):
        """
        Hàm core để gửi ảnh PIL xuống Printer Driver.
        Tự động scale ảnh vừa khít trang in vật lý.
        """
        try:
            hDC.StartPage()

            # 1. Lấy thông số vật lý của máy in (Pixel thực tế)
            # HORZRES / VERTRES: Chiều rộng/cao tính bằng pixel của trang in
            printer_w = hDC.GetDeviceCaps(win32con.HORZRES)
            printer_h = hDC.GetDeviceCaps(win32con.VERTRES)

            # 2. Tính toán tỷ lệ scale (Fit to Page)
            # Ảnh gốc (VD: A4 300dpi = 2480x3508)
            img_w, img_h = pil_image.size
            
            ratio_w = printer_w / img_w
            ratio_h = printer_h / img_h
            scale = min(ratio_w, ratio_h) # Chọn tỷ lệ nhỏ hơn để ảnh nằm trọn trong trang

            new_w = int(img_w * scale)
            new_h = int(img_h * scale)

            # Căn giữa trang
            x_offset = (printer_w - new_w) // 2
            y_offset = (printer_h - new_h) // 2
            
            # Tọa độ vẽ: (Left, Top, Right, Bottom)
            dib_dst = (x_offset, y_offset, x_offset + new_w, y_offset + new_h)

            # 3. Vẽ
            # Sử dụng ImageWin để convert PIL Image sang định dạng DIB mà Windows hiểu
            dib = ImageWin.Dib(pil_image)
            dib.draw(hDC.GetHandleOutput(), dib_dst)

            hDC.EndPage()
        except Exception as e:
            raise e

    def _draw_data_on_original(self, img, idx):
        # ... (Giữ nguyên code cũ của bạn đoạn này) ...
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
            # Nếu in PDF thì hỏi mở folder, nếu in trực tiếp thì chỉ báo xong
            if "PDF" in message: 
                if MsgHelper.ask_yes_no(f"{message}\nMở thư mục kết quả?", title="Thành công"):
                    os.startfile(output_folder)
            else:
                MsgHelper.show_info(message, title="Thành công")
        else:
            MsgHelper.show_error(message)
    def _smart_resize(self, img, target_w, target_h):
        """
        Hàm resize ảnh giữ nguyên tỷ lệ (Aspect Ratio) để không bị méo.
        - Tự động tính toán tỷ lệ co giãn.
        - Tạo nền trắng chuẩn khổ giấy (A4/A5/A6).
        - Dán ảnh thẻ cử tri vào chính giữa.
        """
        # 1. Tạo tờ giấy trắng tinh đúng kích thước target (A4/A5/A6)
        bg = Image.new('RGB', (target_w, target_h), (255, 255, 255))
        
        # 2. Tính toán tỷ lệ resize (Fit to Page)
        img_w, img_h = img.size
        # Chọn tỷ lệ nhỏ hơn giữa chiều rộng và chiều cao để ảnh nằm trọn trong trang
        ratio = min(target_w / img_w, target_h / img_h)
        
        # 3. Kích thước mới của ảnh sau khi co lại
        new_w = int(img_w * ratio)
        new_h = int(img_h * ratio)
        
        # 4. Thực hiện resize chất lượng cao (LANCZOS)
        img_resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        
        # 5. Tính tọa độ để dán vào chính giữa tờ giấy trắng
        offset_x = (target_w - new_w) // 2
        offset_y = (target_h - new_h) // 2
        
        # 6. Dán ảnh lên nền trắng
        bg.paste(img_resized, (offset_x, offset_y))
        
        return bg