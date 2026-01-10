import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from helpers.license_manager import LicenseManager
from helpers.msg_helper import MsgHelper
import os

class LicenseController:
    def __init__(self, router):
        self.router = router
        self.view = None
        self.manager = LicenseManager()
        self.is_licensed = False 

    def set_view(self, view):
        self.view = view

    def check_at_startup(self):
        """Kiểm tra bản quyền khi khởi động"""
        is_valid, hwid = self.manager.validate()
        
        # 1. Hiển thị HWID
        if self.view and hasattr(self.view, 'p_left') and hasattr(self.view.p_left, 'ent_hwid'):
            ent = self.view.p_left.ent_hwid
            ent.config(state="normal")
            ent.delete(0, tk.END)
            ent.insert(0, hwid)
            ent.config(state="readonly")
            
        # 2. [MỚI] Nếu đã kích hoạt, nạp lại Key cũ vào ô nhập để hiển thị
        if is_valid:
            try:
                # Đọc key từ file (giả sử file lưu key tên là license.key nằm cùng thư mục)
                if os.path.exists(self.manager.LICENSE_FILE):
                    with open(self.manager.LICENSE_FILE, "r") as f:
                        saved_key = f.read().strip()
                        # Điền key vào ô input
                        self.view.p_left.ent_key.delete(0, tk.END)
                        self.view.p_left.ent_key.insert(0, saved_key)
            except Exception:
                pass

        self.update_ui_state(is_valid)

    def on_activate(self):
        """Xử lý nút Kích hoạt"""
        key_input = self.view.p_left.ent_key.get().strip()
        if not key_input:
            MsgHelper.show_warning("Vui lòng nhập Key!")
            return

        self.manager.save_license(key_input)
        is_valid, hwid = self.manager.validate()
        
        if is_valid:
            self.update_ui_state(True)
            MsgHelper.show_info("Kích hoạt thành công!\nCác tính năng đã được mở khóa.", "Thành công")
        else:
            self.update_ui_state(False)
            MsgHelper.show_error("Key không hợp lệ hoặc không khớp mã máy!", "Thất bại")

    def on_copy_hwid(self):
        """Copy mã máy"""
        hwid = self.view.p_left.ent_hwid.get()
        self.view.master.clipboard_clear()
        self.view.master.clipboard_append(hwid)
        self.view.master.update()
        MsgHelper.show_info("Đã copy Mã máy!", "Thông báo")

    # --- CÁC HÀM HỖ TRỢ KHÓA GIAO DIỆN ---
    def _change_state_recursive(self, widget, state):
        try:
            if isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Button, ttk.Checkbutton, ttk.Radiobutton, ttk.Spinbox)):
                if isinstance(widget, ttk.Combobox):
                    widget.configure(state="readonly" if state == "normal" else "disabled")
                else:
                    widget.configure(state=state)
        except: pass
        for child in widget.winfo_children():
            self._change_state_recursive(child, state)

    def _show_locked_msg(self, event):
        if not self.is_licensed:
            MsgHelper.show_warning("Vui lòng kích hoạt bản quyền!")
            return "break"

    def _lock_area(self, container):
        self._change_state_recursive(container, "disabled")
        container.unbind("<Button-1>")
        container.bind("<Button-1>", self._show_locked_msg, add="+")

    def _unlock_area(self, container):
        self._change_state_recursive(container, "normal")
        container.unbind("<Button-1>")

    def update_ui_state(self, is_valid):
        """Khóa hoặc Mở khóa giao diện"""
        self.is_licensed = is_valid
        if not self.view: return

        p_left = self.view.p_left

        if is_valid:
            # --- TRƯỜNG HỢP: ĐÃ KÍCH HOẠT ---
            p_left.fr_license.configure(text="Cập nhật mã sử dụng", bootstyle="success")
            
            # [SỬA] Nút Active: Dùng style="Small.success.TButton" (Xóa bootstyle cũ đi)
            p_left.btn_activate.configure(
                text="✔", 
                style="Small.success.TButton", # <--- QUAN TRỌNG: Style nhỏ màu xanh
                state="normal", 
                command=lambda: None
            )

            # Ô Key: Xanh, Chỉ đọc
            p_left.ent_key.configure(
                bootstyle="success", 
                state="readonly", 
                show="" 
            )
            
            if hasattr(p_left, 'fr_buttons'): self._unlock_area(p_left.fr_buttons)

        else:
            # --- TRƯỜNG HỢP: CHƯA KÍCH HOẠT ---
            p_left.fr_license.configure(text="Cập nhật mã sử dụng", bootstyle="danger")
            
            # [SỬA] Nút Active: Dùng style="Small.danger.TButton"
            p_left.btn_activate.configure(
                text="⚠", 
                style="Small.danger.TButton", # <--- QUAN TRỌNG: Style nhỏ màu đỏ
                state="normal",
                command=self.on_activate
            )

            # Ô Key: Bình thường
            p_left.ent_key.configure(
                bootstyle="default", 
                state="normal", 
                show="" 
            )
            
            if hasattr(p_left, 'fr_buttons'): self._lock_area(p_left.fr_buttons)