# controllers/router.py
import os
from models.data_model import VoterModel
from controllers.data_controller import DataController
from controllers.canvas_controller import CanvasController
from controllers.print_controller import PrintController
from ttkbootstrap.dialogs import Messagebox
from helpers.msg_helper import MsgHelper

class AppRouter:
    def __init__(self):
        # 1. Khởi tạo Model và các Controllers con
        self.model = VoterModel()
        self.view = None
        
        self.ctrl_data = DataController(self)
        self.ctrl_canvas = CanvasController(self)
        self.ctrl_print = PrintController(self)
        
        # 2. Các biến trạng thái hệ thống
        self.current_idx = 0
        self.selected_field = None
        self.edit_mode = None 
        self.search_timer = None
        self.sort_state = {"col": None, "reverse": False}
        self.is_bulk_updating = False 
        self.is_loading_ui = False
        
        # --- CẤU HÌNH XOAY VÀ GIẤY ---
        self.template_rotation = 0       
        self.is_paper_landscape = False  

    def set_view(self, view):
        self.view = view
        if hasattr(view.p_left, 'var_edit_mode'):
            self.edit_mode = view.p_left.var_edit_mode

    # =======================================================
    #              NHÓM CHỨC NĂNG HỆ THỐNG
    # =======================================================
    def exit_app(self):
        if MsgHelper.ask_yes_no("Bạn muốn thoát chương trình?", title="Xác nhận thoát", parent=self.view):
            self.view.master.destroy()

    def select_template(self): self.ctrl_data.select_template()
    def select_excel(self): self.ctrl_data.select_excel()
    def select_signature_folder(self): self.ctrl_data.select_signature_folder()

    # =======================================================
    #              NHÓM CHỨC NĂNG IN ẤN
    # =======================================================
    def start_print(self):
        if self.model.df is None or self.model.df.empty:
            return MsgHelper.show_warning("Chưa có dữ liệu để in!")

        try:
            val_from = self.view.p_right.var_print_from.get()
            val_to = self.view.p_right.var_print_to.get()
        except:
            val_from, val_to = "1", ""

        custom_indices = None
        if val_to.strip() != "":
            try:
                start_row = int(val_from)
                end_row = int(val_to)
                max_row = len(self.model.df)
                
                if start_row < 1: start_row = 1
                if end_row > max_row: end_row = max_row
                
                if start_row > end_row:
                     return MsgHelper.show_error(f"Hàng bắt đầu ({start_row}) không được lớn hơn hàng kết thúc ({end_row})!")

                custom_indices = list(range(start_row - 1, end_row))
                self.deselect_all()
                
            except ValueError:
                return MsgHelper.show_error("Vui lòng nhập số hàng hợp lệ!")

        self.ctrl_print.print_batch(custom_indices)

    # =======================================================
    #              NHÓM CHỨC NĂNG CANVAS & VIEW
    # =======================================================
    def toggle_paper_orientation(self):
        self.is_paper_landscape = not self.is_paper_landscape
        
        if self.is_paper_landscape:
            self.template_rotation = 90
        else:
            self.template_rotation = 0

        try:
            if self.view and hasattr(self.view, 'p_right'):
                btn = self.view.p_right.btn_rotate_paper 
                icon = "▬" if self.is_paper_landscape else "▮"
                btn.configure(text=icon)
        except Exception as e:
            print(f"Lỗi cập nhật nút giấy: {e}")

        self.ctrl_canvas.render()

    def rotate_template_right(self):
        self.template_rotation = (self.template_rotation + 90) % 360
        self.ctrl_canvas.render()

    def on_paper_config_change(self, event=None):
        self.ctrl_canvas.render()

    def on_shift_zoom(self, event): self.ctrl_canvas.handle_zoom(event)
    def on_drag_start(self, event): self.ctrl_canvas.drag_start(event)
    def on_drag_motion(self, event): self.ctrl_canvas.drag_motion(event)
    def on_drag_end(self, event): self.ctrl_canvas.drag_end(event)
    def on_canvas_resize(self, event): self.ctrl_canvas.on_resize(event)

    # =======================================================
    #              NHÓM CHỨC NĂNG DỮ LIỆU (TABLE)
    # =======================================================
    def refresh_mid_table(self):
        if self.model.df is None: return
        self.is_bulk_updating = True 

        df_page = self.model.get_current_page_data()
        self.view.p_mid.update_data(df_page, self.model.custom_configs)
        self.view.p_mid.update_pagination_label(self.model.current_page, self.model.total_pages)
        
        if list(self.view.p_mid.cbb_filter['values']) != self.model.unique_areas:
             self.view.p_mid.cbb_filter['values'] = self.model.unique_areas

        defaults = ["Tất cả", "Chưa chọn khu vực", "Lọc theo khu vực", ""]
        if self.model.current_area_filter in defaults:
            self.view.p_mid.cbb_filter.set("Lọc theo khu vực")
        else:
            self.view.p_mid.cbb_filter.set(self.model.current_area_filter)
            
        self.is_bulk_updating = False

    def next_page(self):
        if self.model.set_page(self.model.current_page + 1):
            self.refresh_mid_table()

    def prev_page(self):
        if self.model.set_page(self.model.current_page - 1):
            self.refresh_mid_table()

    def on_header_click(self, col):
        if self.sort_state["col"] == col:
            self.sort_state["reverse"] = not self.sort_state["reverse"]
        else:
            self.sort_state["col"] = col
            self.sort_state["reverse"] = False
            
        self.model.sort_data(col, self.sort_state["reverse"])
        if self.view:
            self.view.p_mid.update_header_arrow(col, self.sort_state["reverse"])
        self.refresh_mid_table()

    # =======================================================
    #              NHÓM CHỨC NĂNG FILTER / SEARCH
    # =======================================================
    def on_filter_change(self, event):
        selected_area = self.view.p_mid.cbb_filter.get()
        self.model.filter_data(selected_area)
        self.deselect_all() 
        self.refresh_mid_table()
        # [QUAN TRỌNG] Không làm gì với lbl_total_val ở đây cả.
        
    def on_search_typing(self, event):
        if self.search_timer:
            try: self.view.after_cancel(self.search_timer)
            except: pass
        current_text = self.view.p_mid.search_view.get_keyword()
        if not current_text:
            self.on_search_action()
            return
        self.search_timer = self.view.after(500, self.on_search_action)

    def on_search_action(self, event=None):
        if self.search_timer:
            self.search_timer = None
        
        if self.view: self.view.master.config(cursor="watch")
        
        try:
            keyword = self.view.p_mid.search_view.get_keyword()
            self.model.search_data(keyword)
            self.deselect_all()
            self.refresh_mid_table()
            # [QUAN TRỌNG] Không làm gì với lbl_total_val ở đây cả.
        finally:
            if self.view: self.view.master.config(cursor="")

    # =======================================================
    #              NHÓM CHỨC NĂNG SELECTION (CHỌN)
    # =======================================================
    def on_tree_left_click(self, event):
        if not self.view: return
        tree = self.view.p_mid.tree
        item_id = tree.identify_row(event.y)
        if not item_id: return 

        tree.selection_set(item_id)
        tree.focus(item_id)

        try:
            new_idx = int(item_id)
            self.current_idx = new_idx
            self.ctrl_canvas.render()
            if self.selected_field: 
                self.load_field_props_to_ui()
        except ValueError: pass
        
        return "break"

    def on_user_select_change(self, event):
        if self.model.df is None or self.is_bulk_updating: return

        visible_ids = self.view.p_mid.tree.get_children()
        visible_ints = {int(x) for x in visible_ids}
        selected_ids = self.view.p_mid.tree.selection()
        selected_ints = {int(x) for x in selected_ids}
        
        self.model.selected_indices -= visible_ints
        self.model.selected_indices.update(selected_ints)
        self.update_count_label()

        if len(selected_ids) == 1:
            try:
                self.current_idx = int(selected_ids[0])
                self.ctrl_canvas.render()
                if self.selected_field: self.load_field_props_to_ui()
            except: pass

    def select_all(self):
        if self.model.df_filtered is None or self.model.df_filtered.empty: return
        self.is_bulk_updating = True 
        all_ids = set(self.model.df_filtered.index)
        self.model.selected_indices.update(all_ids)
        
        current_page_items = self.view.p_mid.tree.get_children()
        self.view.p_mid.tree.selection_set(current_page_items)
        
        self.update_count_label()
        self.is_bulk_updating = False

    def deselect_all(self):
        self.is_bulk_updating = True
        self.view.p_mid.tree.selection_set([])
        self.model.selected_indices.clear()
        self.update_count_label()
        self.is_bulk_updating = False

    def update_count_label(self):
        pass # Không làm gì cả để tránh chạm vào text tổng

    # =======================================================
    #              NHÓM CHỨC NĂNG EDIT CONFIG (STYLE)
    # =======================================================
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
        finally:
            self.is_loading_ui = False

    def on_style_change(self):
        self.ctrl_canvas.render()
        if self.selected_field: self.load_field_props_to_ui()

    def on_prop_change(self, event=None):
        if not self.selected_field or self.is_loading_ui: return
        
        view_l = self.view.p_left
        try:
            mode = self.edit_mode.get() 
        except: mode = "global"
        
        col = self.selected_field
        
        try:
            if col == "signature_img":
                try: w = int(view_l.spin_img_w.get())
                except: w = 150
                try: h = int(view_l.spin_img_h.get())
                except: h = 80
                self.model.update_config_value(self.current_idx, mode, col, "w", w)
                self.model.update_config_value(self.current_idx, mode, col, "h", h)
            else:
                if hasattr(view_l, 'combo_font'):
                    self.model.update_config_value(self.current_idx, mode, col, "font", view_l.combo_font.get())
                if hasattr(view_l, 'combo_color'):
                    self.model.update_config_value(self.current_idx, mode, col, "color", view_l.combo_color.get())
                
                try: size_val = int(view_l.spin_size.get())
                except: size_val = 14
                self.model.update_config_value(self.current_idx, mode, col, "size", size_val)
                
                if hasattr(view_l, 'chk_bold_var'):
                    self.model.update_config_value(self.current_idx, mode, col, "bold", view_l.chk_bold_var.get())
                if hasattr(view_l, 'chk_upper_var'):
                    self.model.update_config_value(self.current_idx, mode, col, "upper", view_l.chk_upper_var.get())
        
        except Exception as e: 
            print(f"Lỗi on_prop_change: {e}")

        self.ctrl_canvas.render()
        
        if mode == "individual":
            self.view.p_mid.tree.item(str(self.current_idx), tags=('custom',))

    def update_field_config(self, key, value):
        if self.selected_field:
            mode = self.edit_mode.get()
            self.model.update_config_value(self.current_idx, mode, self.selected_field, key, value)
            if mode == "individual":
                self.view.p_mid.tree.item(str(self.current_idx), tags=('custom',))

    def reset_current_custom(self):
        if self.model.df is None or self.model.df.empty: return
        if self.model.reset_custom_config(self.current_idx):
            self.view.p_mid.tree.item(str(self.current_idx), tags=())
            self.ctrl_canvas.render()
            if self.selected_field: self.load_field_props_to_ui()
            Messagebox.show_info("Đã xóa cấu hình riêng của người này.", "Reset")

    def pick_manual_signature(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("Image", "*.png;*.jpg;*.jpeg")])
        if path:
            mode = self.edit_mode.get()
            self.model.update_config_value(self.current_idx, mode, "signature_img", "path", path)
            self.model.update_config_value(self.current_idx, mode, "signature_img", "enable", True)
            
            if mode == "individual":
                self.view.p_mid.tree.item(str(self.current_idx), tags=('custom',))
            
            self.ctrl_canvas.render()