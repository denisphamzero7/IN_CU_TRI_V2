import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from helpers.license_manager import LicenseManager
from helpers.msg_helper import MsgHelper

class LicenseController:
    def __init__(self, router):
        self.router = router
        self.view = None
        self.manager = LicenseManager()
        self.is_licensed = False 

    def set_view(self, view):
        self.view = view

    def check_at_startup(self):
        """Chạy khi App vừa bật lên - Có kiểm tra an toàn"""
        is_valid, hwid = self.manager.validate()
        
        # [AN TOÀN] Kiểm tra xem view đã tạo xong ent_hwid chưa
        if self.view and hasattr(self.view, 'p_left') and hasattr(self.view.p_left, 'ent_hwid'):
            ent = self.view.p_left.ent_hwid
            ent.config(state="normal")
            ent.delete(0, tk.END)
            ent.insert(0, hwid)
            ent.config(state="readonly")
            
        self.update_ui_state(is_valid)

    def on_activate(self):
        key_input = self.view.p_left.ent_key.get().strip()
        if not key_input:
            MsgHelper.show_warning("Vui lòng nhập Key!")
            return

        self.manager.save_license(key_input)
        is_valid, hwid = self.manager.validate()
        
        if is_valid:
            self.update_ui_state(True)
            MsgHelper.show_info("Kích hoạt bản quyền thành công!\nFull tính năng đã mở.", "Thành công")
        else:
            self.update_ui_state(False)
            MsgHelper.show_error("Key sai hoặc không khớp mã máy!", "Thất bại")

    def on_copy_hwid(self):
        hwid = self.view.p_left.ent_hwid.get()
        self.view.master.clipboard_clear()
        self.view.master.clipboard_append(hwid)
        self.view.master.update()
        MsgHelper.show_info("Đã copy Mã máy!", "Thông báo")

    def _show_locked_msg(self, event):
        """Hiện thông báo khi click vào vùng bị khóa"""
        if not self.is_licensed:
            MsgHelper.show_warning("Vui lòng kích hoạt bản quyền để sử dụng tính năng này!")
            return "break"

    def _change_state_recursive(self, widget, state):
        """Chỉ đổi trạng thái visual (mờ đi), không gán sự kiện click"""
        try:
            if isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Button, ttk.Checkbutton, ttk.Radiobutton, ttk.Spinbox)):
                if isinstance(widget, ttk.Combobox):
                    widget.configure(state="readonly" if state == "normal" else "disabled")
                else:
                    widget.configure(state=state)
        except Exception: pass

        for child in widget.winfo_children():
            self._change_state_recursive(child, state)

    def _bind_lock_trigger(self, widget):
        """Gán sự kiện click báo lỗi cho Frame cha"""
        widget.unbind("<Button-1>")
        widget.bind("<Button-1>", self._show_locked_msg, add="+")

    def _lock_area(self, container):
        self._change_state_recursive(container, "disabled")
        self._bind_lock_trigger(container)

    def _unlock_area(self, container):
        self._change_state_recursive(container, "normal")
        container.unbind("<Button-1>")

    def update_ui_state(self, is_valid):
        self.is_licensed = is_valid
        if not self.view: return

        p_left = self.view.p_left
        p_right = getattr(self.view, 'p_right', None)

        # 1. License UI
        if hasattr(p_left, 'fr_license'):
            if is_valid:
                p_left.fr_license.configure(text="Thông tin bản quyền", bootstyle="success")
                p_left.lbl_license_status.config(text="✔ Đã kích hoạt (Pro)", foreground="green")
                p_left.btn_activate.configure(state="disabled", text="Đã Active")
                p_left.ent_key.delete(0, tk.END); p_left.ent_key.config(state="disabled")
            else:
                p_left.fr_license.configure(text="CHƯA KÍCH HOẠT", bootstyle="danger")
                p_left.lbl_license_status.config(text="⚠ Giới hạn tính năng - Vui lòng nhập Key", foreground="red")
                p_left.btn_activate.configure(state="normal", text="Kích hoạt")
                p_left.ent_key.config(state="normal")

        # 2. Khóa/Mở các vùng chức năng
        if hasattr(p_left, 'fr_buttons'):
            self._unlock_area(p_left.fr_buttons) if is_valid else self._lock_area(p_left.fr_buttons)

        if p_right:
            if hasattr(p_right, 'fr_print_action'):
                self._unlock_area(p_right.fr_print_action) if is_valid else self._lock_area(p_right.fr_print_action)
            if hasattr(p_right, 'fr_paper_setup'):
                self._unlock_area(p_right.fr_paper_setup) if is_valid else self._lock_area(p_right.fr_paper_setup)
            if hasattr(p_right, 'fr_style_toolbar'):
                self._unlock_area(p_right.fr_style_toolbar) if is_valid else self._lock_area(p_right.fr_style_toolbar)
                # Giữ cho label hiển thị luôn sáng
                if hasattr(p_right, 'lbl_current_field'): p_right.lbl_current_field.configure(state="normal")