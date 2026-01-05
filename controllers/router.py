import os
from tkinter import filedialog
from models.data_model import VoterModel
from controllers.data_controller import DataController
from controllers.canvas_controller import CanvasController
from controllers.print_controller import PrintController
from helpers.msg_helper import MsgHelper
from ttkbootstrap.dialogs import Messagebox

class AppRouter:
    def __init__(self):
        self.model = VoterModel()
        self.view = None
        self.ctrl_data = DataController(self)
        self.ctrl_canvas = CanvasController(self)
        self.ctrl_print = PrintController(self)
        
        self.current_idx = 0
        self.selected_field = None
        self.edit_mode = None 
        self.search_timer = None
        self.sort_state = {"col": None, "reverse": False}
        self.is_bulk_updating = False 
        self.is_loading_ui = False
        
        # --- Cấu hình mặc định ---
        # [SỬA TẠI ĐÂY] Mặc định là True (Ngang)
        self.is_paper_landscape = True 
        self.template_rotation = 0      

    def set_view(self, view):
        self.view = view
        if hasattr(view.p_left, 'var_edit_mode'):
            self.edit_mode = view.p_left.var_edit_mode

    # --- HÀM XỬ LÝ SẮP XẾP ---
    def on_header_click(self, col_id):
        if self.model.df is None or self.model.df.empty: return

        if self.sort_state["col"] == col_id:
            self.sort_state["reverse"] = not self.sort_state["reverse"]
        else:
            self.sort_state["col"] = col_id
            self.sort_state["reverse"] = False 

        is_ascending = not self.sort_state["reverse"]

        try:
            if col_id == "stt":
                self.model.df.sort_index(ascending=is_ascending, inplace=True)
            
            elif col_id == "name":
                target_col = None
                for c in self.model.df.columns:
                    if any(kw in c.lower() for kw in ["họ tên", "họ và tên", "name", "tên"]):
                        target_col = c
                        break
                
                if not target_col and len(self.model.df.columns) > 1:
                    target_col = self.model.df.columns[1]

                if target_col:
                    self.model.df.sort_values(
                        by=target_col, 
                        ascending=is_ascending, 
                        inplace=True,
                        key=lambda col: col.astype(str).str.lower()
                    )

            self.refresh_mid_table()
            
            if self.view:
                self.view.p_mid.update_header_arrow(col_id, self.sort_state["reverse"])
                
        except Exception as e:
            print(f"Lỗi khi sắp xếp: {e}")

    # --- Các hàm khác ---
    def on_orientation_change(self, event=None):
        val = self.view.p_right.var_orientation.get()
        if val == "Ngang": 
            self.is_paper_landscape = True 
            self.template_rotation = 0
        else:
            self.is_paper_landscape = False 
            self.template_rotation = 0
        self.ctrl_canvas.render()

    def rotate_template_right(self):
        self.template_rotation = (self.template_rotation + 90) % 360
        self.ctrl_canvas.render()

    def start_print(self):
        if self.model.df is None or self.model.df.empty:
            return MsgHelper.show_warning("Chưa có dữ liệu!")
        try:
            val_from = self.view.p_right.var_print_from.get()
            val_to = self.view.p_right.var_print_to.get()
            start_row = int(val_from)
            end_row = int(val_to) if val_to.strip() else start_row
            max_row = len(self.model.df)
            start_row = max(1, min(start_row, max_row))
            end_row = max(1, min(end_row, max_row))
            if start_row > end_row: return MsgHelper.show_error("Lỗi: Từ > Đến")
            custom_indices = list(range(start_row - 1, end_row))
            self.ctrl_print.print_batch(custom_indices)
        except ValueError:
            return MsgHelper.show_error("Số hàng không hợp lệ!")

    def pick_manual_signature(self):
        path = filedialog.askopenfilename(filetypes=[("Image", "*.png;*.jpg;*.jpeg")])
        if path:
            mode = "global"
            try: mode = self.edit_mode.get()
            except: pass
            self.model.update_config_value(self.current_idx, mode, "signature_img", "path", path)
            self.model.update_config_value(self.current_idx, mode, "signature_img", "enable", True)
            if mode == "individual": self.view.p_mid.tree.item(str(self.current_idx), tags=('custom',))
            self.ctrl_canvas.render()
    def on_style_change(self):
        self.ctrl_canvas.render()
        if self.selected_field: self.load_field_props_to_ui()
    def select_template(self): self.ctrl_data.select_template()
    def select_excel(self): self.ctrl_data.select_excel()
    def select_signature_folder(self): self.ctrl_data.select_signature_folder()
    def exit_app(self):
        if MsgHelper.ask_yes_no("Thoát?", parent=self.view): self.view.master.destroy()
    def refresh_mid_table(self):
        if self.model.df is None: return
        self.is_bulk_updating = True 
        df_page = self.model.get_current_page_data()
        self.view.p_mid.update_data(df_page, self.model.custom_configs)
        self.view.p_mid.update_pagination_label(self.model.current_page, self.model.total_pages)
        if list(self.view.p_mid.cbb_filter['values']) != self.model.unique_areas:
             self.view.p_mid.cbb_filter['values'] = self.model.unique_areas
        self.is_bulk_updating = False
    def next_page(self):
        if self.model.set_page(self.model.current_page + 1): self.refresh_mid_table()
    def prev_page(self):
        if self.model.set_page(self.model.current_page - 1): self.refresh_mid_table()
    def on_filter_change(self, event):
        self.model.filter_data(self.view.p_mid.cbb_filter.get())
        self.deselect_all()
        self.refresh_mid_table()
    def on_search_action(self, event=None):
        if self.view: self.view.master.config(cursor="watch")
        try:
            self.model.search_data(self.view.p_mid.search_view.get_keyword())
            self.deselect_all()
            self.refresh_mid_table()
        finally:
            if self.view: self.view.master.config(cursor="")
    def on_search_typing(self, event):
        if self.search_timer: self.view.after_cancel(self.search_timer)
        if not self.view.p_mid.search_view.get_keyword():
            self.on_search_action()
            return
        self.search_timer = self.view.after(500, self.on_search_action)
    def on_tree_left_click(self, event):
        item = self.view.p_mid.tree.identify_row(event.y)
        if not item: return
        self.view.p_mid.tree.selection_set(item)
        self.view.p_mid.tree.focus(item)
        try:
            self.current_idx = int(item)
            self.ctrl_canvas.render()
            if self.selected_field: self.load_field_props_to_ui()
        except: pass
        return "break"
    def on_user_select_change(self, event):
        if self.is_bulk_updating or not self.model.df: return
        sel = self.view.p_mid.tree.selection()
        if len(sel) == 1:
            self.current_idx = int(sel[0])
            self.ctrl_canvas.render()
            if self.selected_field: self.load_field_props_to_ui()
    def on_field_toggle(self, col):
        is_on = self.view.p_left.field_vars[col].get()
        self.model.update_config_value(self.current_idx, "global", col, "enable", is_on)
        self.ctrl_canvas.render()
    def select_field(self, col):
        self.selected_field = col
        self.load_field_props_to_ui()
    def load_field_props_to_ui(self):
        if not self.selected_field: return
        self.is_loading_ui = True 
        try:
            cfg = self.model.get_effective_config(self.current_idx).get(self.selected_field, {})
            self.view.p_left.update_prop_inputs(cfg, self.selected_field)
        finally: self.is_loading_ui = False
    def on_prop_change(self, event=None):
        if not self.selected_field or self.is_loading_ui: return
        view = self.view.p_left
        mode = "global"
        try: mode = self.edit_mode.get()
        except: pass
        col = self.selected_field
        try:
            if col == "signature_img":
                self.model.update_config_value(self.current_idx, mode, col, "w", int(view.spin_img_w.get() or 150))
                self.model.update_config_value(self.current_idx, mode, col, "h", int(view.spin_img_h.get() or 80))
            else:
                if hasattr(view, 'combo_font'): self.model.update_config_value(self.current_idx, mode, col, "font", view.combo_font.get())
                if hasattr(view, 'combo_color'): self.model.update_config_value(self.current_idx, mode, col, "color", view.combo_color.get())
                self.model.update_config_value(self.current_idx, mode, col, "size", int(view.spin_size.get() or 14))
                if hasattr(view, 'chk_bold_var'): self.model.update_config_value(self.current_idx, mode, col, "bold", view.chk_bold_var.get())
                if hasattr(view, 'chk_upper_var'): self.model.update_config_value(self.current_idx, mode, col, "upper", view.chk_upper_var.get())
        except: pass
        self.ctrl_canvas.render()
        if mode == "individual": self.view.p_mid.tree.item(str(self.current_idx), tags=('custom',))
    def update_field_config(self, k, v):
        if self.selected_field:
            mode = "global"
            try: mode = self.edit_mode.get()
            except: pass
            self.model.update_config_value(self.current_idx, mode, self.selected_field, k, v)
    def reset_current_custom(self):
        if self.model.reset_custom_config(self.current_idx):
            self.view.p_mid.tree.item(str(self.current_idx), tags=())
            self.ctrl_canvas.render()
            if self.selected_field: self.load_field_props_to_ui()
            Messagebox.show_info("Đã xóa cấu hình riêng.", "Reset")
    def deselect_all(self):
        self.is_bulk_updating = True
        try: self.view.p_mid.tree.selection_set([])
        except: pass
        self.model.selected_indices.clear()
        self.is_bulk_updating = False
    def select_all(self): pass 
    def on_header_click(self, col): pass 
    def on_shift_zoom(self, e): self.ctrl_canvas.handle_zoom(e)
    def on_drag_start(self, e): self.ctrl_canvas.drag_start(e)
    def on_drag_motion(self, e): self.ctrl_canvas.drag_motion(e)
    def on_drag_end(self, e): self.ctrl_canvas.drag_end(e)
    def on_canvas_resize(self, e): self.ctrl_canvas.on_resize(e)
    def on_paper_config_change(self, e=None): self.ctrl_canvas.render()