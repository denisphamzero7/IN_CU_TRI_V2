import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class SearchView(ttk.Frame):
    def __init__(self, parent, router, width=15):
        super().__init__(parent)
        self.router = router
        self.placeholder_text = "Tìm Tên, Cccd"
        self.is_placeholder_active = True 
        
        # --- UI SETUP ---
        self._setup_ui(width)
        
        # --- LOGIC PLACEHOLDER BAN ĐẦU ---
        self._set_placeholder()

    def _setup_ui(self, width):
        # 1. Ô nhập liệu
        self.ent_search = ttk.Entry(self, width=width, bootstyle="info", font=("Segoe UI", 7))
        self.ent_search.pack(side=LEFT, padx=(0, 5))

        # 2. Binding Sự kiện
        self.ent_search.bind("<FocusIn>", self._on_focus_in)
        self.ent_search.bind("<FocusOut>", self._on_focus_out)
        self.ent_search.bind("<KeyRelease>", self._on_key_release)
        self.ent_search.bind("<Return>", self.router.on_search_action)

    def _set_placeholder(self):
        """Hiển thị text gợi ý màu xám"""
        self.ent_search.delete(0, "end")
        self.ent_search.insert(0, self.placeholder_text)
        self.ent_search.config(foreground="grey")
        self.is_placeholder_active = True

    def _on_focus_in(self, event):
        """Khi click vào: Xóa placeholder"""
        if self.is_placeholder_active:
            self.ent_search.delete(0, "end")
            self.ent_search.config(foreground="") # Reset màu chữ theme
            self.is_placeholder_active = False

    def _on_focus_out(self, event):
        """Khi click ra ngoài: Nếu rỗng thì hiện lại placeholder"""
        content = self.ent_search.get().strip()
        if not content:
            self._set_placeholder()

    def _on_key_release(self, event):
        if self.is_placeholder_active: return
        self.router.on_search_typing(event)

    def get_keyword(self):
        if self.is_placeholder_active:
            return ""
        return self.ent_search.get().strip()

    # --- [HÀM QUAN TRỌNG] ĐỂ ROUTER GỌI ---
    def clear_input(self):
        """Reset ô tìm kiếm về trạng thái Placeholder"""
        self.ent_search.delete(0, "end")
        self._set_placeholder()
        # Dùng master thay vì parent để tránh lỗi
        try: self.master.focus() 
        except: pass