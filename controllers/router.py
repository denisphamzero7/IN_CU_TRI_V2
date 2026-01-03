# controllers/router.py
from models.data_model import VoterModel
from controllers.data_controller import DataController
from controllers.canvas_controller import CanvasController
from controllers.print_controller import PrintController
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
        
        self.sort_state = {"col": None, "reverse": False}
        self.is_bulk_updating = False 
        self.is_loading_ui = False

        # --- [QUAN TRỌNG] Biến lưu góc xoay ảnh phôi (0, 90, 180, 270) ---
        self.template_rotation = 0 
        # ---------------------------------------------

    def set_view(self, view):
        self.view = view
        self.edit_mode = view.p_left.var_edit_mode

    # --- Actions ---
    def select_template(self): self.ctrl_data.select_template()
    def select_excel(self): self.ctrl_data.select_excel()
    def select_signature_folder(self): self.ctrl_data.select_signature_folder()
    def start_print(self): self.ctrl_print.print_batch()
    
    def exit_app(self):
        if Messagebox.show_question("Bạn muốn thoát chương trình?", "Thoát", buttons=['No:secondary', 'Yes:primary']) == 'Yes':
            self.view.master.destroy()

    # --- Pagination Actions ---
    def next_page(self):
        if self.model.set_page(self.model.current_page + 1):
            self.refresh_mid_table()

    def prev_page(self):
        if self.model.set_page(self.model.current_page - 1):
            self.refresh_mid_table()

    def refresh_mid_table(self):
        """Load dữ liệu và khôi phục trạng thái chọn"""
        if self.model.df is None: return
        self.is_bulk_updating = True 

        # 1. Update Data
        df_page = self.model.get_current_page_data()
        self.view.p_mid.update_data(df_page, self.model.custom_configs)
        self.view.p_mid.update_pagination_label(self.model.current_page, self.model.total_pages)
        
        # Cập nhật list Combobox lọc
        current_values = self.view.p_mid.cbb_filter['values']
        if not current_values or (len(current_values) == 0 and len(self.model.unique_areas) > 0):
            self.view.p_mid.cbb_filter['values'] = self.model.unique_areas
            if self.model.unique_areas:
                self.view.p_mid.cbb_filter.current(0) 
        
        # 2. Khôi phục chọn (Selection)
        items_to_select = []
        for item_id in self.view.p_mid.tree.get_children():
            if int(item_id) in self.model.selected_indices:
                items_to_select.append(item_id)
        if items_to_select:
            self.view.p_mid.tree.selection_set(items_to_select)
        
        # 3. Update Label
        self.update_count_label()
        self.is_bulk_updating = False

    # --- Filter & Sort ---
    def on_filter_change(self, event):
        selected_area = self.view.p_mid.cbb_filter.get()
        self.model.filter_data(selected_area)
        self.deselect_all()
        self.refresh_mid_table()
        self.select_all() # Tự động chọn hết sau khi lọc

        count = len(self.model.selected_indices)
        if selected_area and selected_area not in ["Tất cả", "All", ""]:
            self.view.p_mid.lbl_count.config(text=f"Đã tự động chọn {count} người thuộc Khu vực {selected_area}")
        else:
            self.update_count_label()

    def on_header_click(self, col_id):
        new_reverse = False
        if self.sort_state["col"] == col_id:
            new_reverse = not self.sort_state["reverse"]
        self.sort_state = {"col": col_id, "reverse": new_reverse}
        self.model.sort_data(col_id, new_reverse)
        self.view.p_mid.update_header_arrow(col_id, new_reverse)
        self.deselect_all() 
        self.refresh_mid_table()

    # --- Selection Events ---
    def on_user_select_change(self, event):
        if self.model.df is None: return
        if self.is_bulk_updating: return

        visible_ids = self.view.p_mid.tree.get_children()
        visible_ints = {int(x) for x in visible_ids}
        selected_ids = self.view.p_mid.tree.selection()
        selected_ints = {int(x) for x in selected_ids}
        
        self.model.selected_indices -= visible_ints
        self.model.selected_indices.update(selected_ints)
        self.update_count_label()

        # Render Canvas khi focus thay đổi
        focus_item = self.view.p_mid.tree.focus()
        target_id = focus_item if focus_item else (selected_ids[0] if selected_ids else None)

        if target_id:
            try:
                new_idx = int(target_id)
                if new_idx != self.current_idx:
                    self.current_idx = new_idx
                    self.ctrl_canvas.render()
                    if self.selected_field:
                        self.load_field_props_to_ui()
            except ValueError: pass

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
        count = len(self.model.selected_indices)
        self.view.p_mid.lbl_count.config(text=f"Đã chọn: {count} người")

    # --- Style & Config Events ---
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
        mode = self.edit_mode.get()
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
                self.model.update_config_value(self.current_idx, mode, col, "font", view_l.combo_font.get())
                self.model.update_config_value(self.current_idx, mode, col, "color", view_l.combo_color.get())
                try: size_val = int(view_l.spin_size.get())
                except: size_val = 14
                self.model.update_config_value(self.current_idx, mode, col, "size", size_val)
                self.model.update_config_value(self.current_idx, mode, col, "bold", view_l.chk_bold_var.get())
                self.model.update_config_value(self.current_idx, mode, col, "upper", view_l.chk_upper_var.get())
        except Exception as e: print(f"Lỗi style: {e}")

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
        path = filedialog.askopenfilename(filetypes=[("Image", "*.png;*.jpg")])
        if path:
            self.edit_mode.set("individual")
            self.model.update_config_value(self.current_idx, "individual", "signature_img", "path", path)
            self.model.update_config_value(self.current_idx, "individual", "signature_img", "enable", True)
            self.view.p_mid.tree.item(str(self.current_idx), tags=('custom',))
            self.ctrl_canvas.render()

    # --- Canvas Actions ---
    def on_shift_zoom(self, event): self.ctrl_canvas.handle_zoom(event)
    def on_drag_start(self, event): self.ctrl_canvas.drag_start(event)
    def on_drag_motion(self, event): self.ctrl_canvas.drag_motion(event)
    def on_drag_end(self, event): self.ctrl_canvas.drag_end(event)
    def on_canvas_resize(self, event): self.ctrl_canvas.on_resize(event)
    def on_paper_config_change(self, event=None):
        """Xử lý khi thay đổi khổ giấy"""
        # In ra để debug (tùy chọn)
        # print("Đã đổi khổ giấy!") 
        self.ctrl_canvas.render()


    def rotate_template_right(self):
        """Xoay ảnh phôi 90 độ (CW) -> Vẽ lại Canvas"""
        self.template_rotation = (self.template_rotation + 90) % 360
        self.ctrl_canvas.render()