import os
from tkinter import filedialog
from models.data_model import VoterModel
from controllers.data_controller import DataController
from controllers.canvas_controller import CanvasController
from controllers.print_controller import PrintController
from helpers.msg_helper import MsgHelper
from ttkbootstrap.dialogs import Messagebox
from controllers.license_controller import LicenseController

class AppRouter:
    def __init__(self):
        self.model = VoterModel()
        self.view = None
        self.sort_reverse = False 
        self.last_sort_col = None 
        self.ctrl_data = DataController(self)
        self.ctrl_canvas = CanvasController(self)
        self.ctrl_print = PrintController(self)
        self.ctrl_license = LicenseController(self)

        self.current_idx = 0
        self.selected_field = None
        self.edit_mode = None 
        self.search_timer = None
        self.sort_state = {"col": None, "reverse": False}
        self.is_bulk_updating = False 
        self.is_loading_ui = False
        
        self.is_paper_landscape = True 
        self.template_rotation = 0   
        self.pressed_keys = set()
        self.move_loop_id = None 
        # --- MAP ĐỂ TRA CỨU KEY LỌC ĐỘNG ---
        self.map_date = {}
        self.map_cccd = {}

    def set_view(self, view):
        self.view = view
        if hasattr(view.p_left, 'var_edit_mode'):
            self.edit_mode = view.p_left.var_edit_mode
        self.ctrl_license.set_view(view)
        self.ctrl_license.check_at_startup()
        self.view.after(100, lambda: self.ctrl_canvas.fit_to_window())

    # --- HÀM KIỂM TRA BẢN QUYỀN (DÙNG CHUNG) ---
    def check_license(self):
        """Trả về True nếu đã Active, False nếu chưa (và hiện thông báo)"""
        if self.ctrl_license.is_licensed:
            return True
        else:
            MsgHelper.show_warning("Vui lòng kích hoạt bản quyền để sử dụng tính năng này!")
            return False

    # --- HÀM VẼ CANVAS AN TOÀN ---
    def render_canvas_safe(self):
        if not self.has_template():
            if hasattr(self.ctrl_canvas, 'canvas'):
                self.ctrl_canvas.canvas.delete("all")
                w = self.ctrl_canvas.canvas.winfo_width()
                h = self.ctrl_canvas.canvas.winfo_height()
                self.ctrl_canvas.canvas.create_text(w/2, h/2, text="Chưa chọn ảnh phôi", font=("Arial", 16), fill="gray")
            return
        self.ctrl_canvas.render()

    def has_template(self):
        if hasattr(self.model, 'template_path') and self.model.template_path:
            return True
        return False

    # -------------------------------------------------------------
    # CÁC HÀM ACTION
    # -------------------------------------------------------------

    def start_print(self):
        if not self.check_license(): return 

        if not self.has_template(): return MsgHelper.show_warning("Vui lòng chọn phôi trước!") 
        if self.model.df is None or self.model.df.empty: return MsgHelper.show_warning("Chưa có dữ liệu!")

        try:
            val_from = self.view.p_right.var_print_from.get().strip()
            val_to = self.view.p_right.var_print_to.get().strip()

            if val_from == "Từ": val_from = ""
            if val_to == "Đến": val_to = ""

            if not val_from or not val_to: 
                return MsgHelper.show_warning("Vui lòng nhập số thứ tự Từ - Đến!")
            
            start_row = int(val_from)
            end_row = int(val_to)
            
            max_row = len(self.model.df)
            start_row = max(1, min(start_row, max_row))
            end_row = max(1, min(end_row, max_row))

            if start_row > end_row: return MsgHelper.show_error("Số 'Từ' không được lớn hơn 'Đến'!")
            
            try:
                printer_name = self.view.p_right.cbb_printer.get()
                invalid_names = ["", "Chọn máy in...", "Không có máy in"]
                if not printer_name or printer_name in invalid_names:
                    return MsgHelper.show_warning("Vui lòng chọn máy in trước khi in!", title="Chưa chọn máy in")
            except:
                return MsgHelper.show_warning("Không tìm thấy danh sách máy in!")
            
            custom_indices = list(range(start_row - 1, end_row))
            self.ctrl_print.print_batch(custom_indices)
            
        except ValueError:
            return MsgHelper.show_error("Vui lòng nhập đúng định dạng số!")

    def rotate_template_right(self):
        self.template_rotation = (self.template_rotation + 90) % 360
        self.render_canvas_safe()

    def on_paper_config_change(self, event=None):
        self.render_canvas_safe()

    def on_orientation_change(self, event=None):
        val = self.view.p_right.var_orientation.get()
        if val == "Ngang": 
            self.is_paper_landscape = True 
            self.template_rotation = 0
        else:
            self.is_paper_landscape = False 
            self.template_rotation = 0
        self.render_canvas_safe()

    def on_prop_change(self, event=None):
        if not self.selected_field or self.is_loading_ui: return
        if not self.has_template(): return 
        
        view = self.view.p_right 
        mode = "global"
        if hasattr(self.view.p_left, 'var_edit_mode'):
             try: mode = self.view.p_left.var_edit_mode.get()
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
        
        self.render_canvas_safe()
        if mode == "individual": self.view.p_mid.tree.item(str(self.current_idx), tags=('custom',))

    def pick_manual_signature(self):
        if not self.has_template(): return MsgHelper.show_warning("Vui lòng chọn phôi trước!") 
        path = filedialog.askopenfilename(filetypes=[("Image", "*.png;*.jpg;*.jpeg")])
        if path:
            mode = "global"
            try: mode = self.edit_mode.get()
            except: pass
            self.model.update_config_value(self.current_idx, mode, "signature_img", "path", path)
            self.model.update_config_value(self.current_idx, mode, "signature_img", "enable", True)
            if mode == "individual": self.view.p_mid.tree.item(str(self.current_idx), tags=('custom',))
            self.render_canvas_safe()

    def reset_current_custom(self):
        if not self.has_template(): return MsgHelper.show_warning("Chưa có phôi!")
        
        mode = "global"
        try: mode = self.edit_mode.get()
        except: pass

        # TRƯỜNG HỢP 1: Reset cấu hình riêng (Individual)
        if mode == "individual":
            if self.model.reset_custom_config(self.current_idx):
                self.view.p_mid.tree.item(str(self.current_idx), tags=())
                self.render_canvas_safe()
                if self.selected_field: self.load_field_props_to_ui()
                MsgHelper.show_info("Đã xóa cấu hình riêng.", "Thành công")
            else:
                MsgHelper.show_info("Đang dùng cấu hình chung.", "Thông báo")

        # TRƯỜNG HỢP 2: Reset cấu hình chung (Global) - [ĐÃ TỐI ƯU]
        else:
            if not self.selected_field: return MsgHelper.show_warning("Chọn một trường để reset!")
            
            if MsgHelper.ask_yes_no(f"Reset '{self.selected_field}' về mặc định?", "Xác nhận"):
                
                # B1: Gom nhóm thông số mặc định vào Dictionary cho gọn
                defaults = {}
                
                if self.selected_field == "signature_img":
                    # Mặc định cho Ảnh
                    defaults = {
                        "w": 150,
                        "h": 80
                    }
                else:
                    # Mặc định cho Text
                    defaults = {
                        "font": "Times New Roman",
                        "size": 21,
                        "bold": True,
                        "color": "Black",
                        "upper": False
                    }

                # B2: Dùng vòng lặp để update (Code sạch hơn, dễ mở rộng sau này)
                for key, val in defaults.items():
                    self.model.update_config_value(0, "global", self.selected_field, key, val)

                # B3: Cập nhật lại giao diện
                self.render_canvas_safe()
                self.load_field_props_to_ui() # Load lại số liệu lên Spinbox/Combobox ngay lập tức
                MsgHelper.show_info("Đã khôi phục mặc định.", "Thành công")
    def select_template(self): 
        if not self.check_license(): return 
        self.ctrl_data.select_template()

    def select_excel(self): 
        if not self.check_license(): return 
        self.ctrl_data.select_excel()

    def select_signature_folder(self): 
        if not self.check_license(): return 
        self.ctrl_data.select_signature_folder()
    
    def exit_app(self):
        if MsgHelper.ask_yes_no("Thoát?", parent=self.view): self.view.master.destroy()

    # --- REFRESH TABLE ---
    def refresh_mid_table(self):
        if self.model.df is None: return
        self.is_bulk_updating = True 
        try:
            # 1. Update Options cho Combobox (lọc động)
            self.update_filter_options_ui()

            # 2. Update Table
            df_page = self.model.get_current_page_data()
            self.view.p_mid.update_data(df_page, self.model.custom_configs)
            
            # Cập nhật số trang
            self.view.p_mid.update_pagination_label(self.model.current_page, self.model.total_pages)
            
            # Lấy tổng số dòng của file Excel gốc
            full_count = len(self.model.df) 
            self.view.p_mid.set_total_count(full_count)
            
            # Cập nhật danh sách cột lọc (nếu cần)
            if list(self.view.p_mid.cbb_filter['values']) != self.model.searchable_columns:
                 self.view.p_mid.cbb_filter['values'] = self.model.searchable_columns
                 self.view.p_mid.cbb_filter.set("Tất cả")
            
        except Exception as e: print(f"Lỗi refresh table: {e}")
        finally: self.is_bulk_updating = False
    
    def update_filter_options_ui(self):
        """Hàm helper để cập nhật Map động và Text cho Combobox Filter"""
        if self.model.df is None or self.model.df.empty: return

        # 1. Date Options
        date_opts = self.model.get_date_options()
        self.view.p_mid.cbb_date['values'] = [x[0] for x in date_opts]
        # Tạo Map: "Text hiển thị" -> "Key logic"
        self.map_date = {x[0]: x[1] for x in date_opts}
        
        if self.view.p_mid.cbb_date.current() == -1 and date_opts:
             self.view.p_mid.cbb_date.current(0)

        # 2. CCCD Options
        cccd_opts = self.model.get_cccd_options()
        self.view.p_mid.cbb_cccd['values'] = [x[0] for x in cccd_opts]
        self.map_cccd = {x[0]: x[1] for x in cccd_opts}
        
        if self.view.p_mid.cbb_cccd.current() == -1 and cccd_opts:
             self.view.p_mid.cbb_cccd.current(0)

    def next_page(self):
        if self.model.set_page(self.model.current_page + 1): self.refresh_mid_table()

    def prev_page(self):
        if self.model.set_page(self.model.current_page - 1): self.refresh_mid_table()

    def on_filter_change(self, event):
        if not self.has_template(): return 
        selected_column = self.view.p_mid.cbb_filter.get()
        self.model.set_search_column(selected_column)
        self.deselect_all()
        self.refresh_mid_table()

    def on_search_action(self, event=None):
        if not self.has_template(): return
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
            self.render_canvas_safe()
            if self.selected_field: self.load_field_props_to_ui()
        except: pass
        return "break"

    def on_user_select_change(self, event):
        if self.is_bulk_updating or self.model.df is None: return 
        sel = self.view.p_mid.tree.selection()
        if len(sel) == 1:
            self.current_idx = int(sel[0])
            self.render_canvas_safe()
            if self.selected_field: self.load_field_props_to_ui()

    def on_field_toggle(self, col):
        if not self.has_template(): return 
        is_on = self.view.p_left.field_vars[col].get()
        self.model.update_config_value(self.current_idx, "global", col, "enable", is_on)
        self.render_canvas_safe()

    def select_field(self, col):
        self.selected_field = col
        self.load_field_props_to_ui()

    def load_field_props_to_ui(self):
        if not self.selected_field: return
        self.is_loading_ui = True 
        try:
            cfg = self.model.get_effective_config(self.current_idx).get(self.selected_field, {})
            if hasattr(self.view.p_left, 'highlight_selected_field'):
                self.view.p_left.highlight_selected_field(self.selected_field)
            self.view.p_right.update_prop_inputs(cfg, self.selected_field)
        finally: self.is_loading_ui = False 

    def update_field_config(self, k, v):
        if not self.has_template(): return
        if self.selected_field:
            mode = "global"
            try: mode = self.edit_mode.get()
            except: pass
            self.model.update_config_value(self.current_idx, mode, self.selected_field, k, v)

    def deselect_all(self):
        self.is_bulk_updating = True
        try: self.view.p_mid.tree.selection_set([])
        except: pass
        self.model.selected_indices.clear()
        self.is_bulk_updating = False

    def on_header_click(self, col_id):
        if self.model.df is None or self.model.df.empty: return 
        if self.last_sort_col == col_id:
            self.sort_reverse = not self.sort_reverse 
        else:
            self.sort_reverse = False 
            self.last_sort_col = col_id

        self.model.sort_data(col_id, self.sort_reverse) 
        if hasattr(self.view, 'p_mid'):
            df_page = self.model.get_current_page_data()
            self.view.p_mid.update_data(df_page, self.model.custom_configs)
            self.view.p_mid.update_header_arrow(col_id, self.sort_reverse)

    # --- CANVAS & KEYBOARD ---
    def on_shift_zoom(self, e): 
        if self.has_template(): self.ctrl_canvas.handle_zoom(e)
    def on_drag_start(self, e): 
        if self.has_template(): self.ctrl_canvas.drag_start(e)
    def on_drag_motion(self, e): 
        if self.has_template(): self.ctrl_canvas.drag_motion(e)
    def on_drag_end(self, e): 
        if self.has_template(): self.ctrl_canvas.drag_end(e)
    def on_canvas_resize(self, e): 
        self.ctrl_canvas.on_resize(e)
    
    def on_key_press(self, event):
        key = event.keysym
        valid_keys = ('Up', 'Down', 'Left', 'Right', 'Shift_L', 'Shift_R')
        if key not in valid_keys: return
        if key in self.pressed_keys: return
        
        first_press = (len(self.pressed_keys) == 0)
        self.pressed_keys.add(key)
        if first_press:
            self.perform_move_step()
            self.is_holding = False
            self.move_loop_id = self.view.after(400, self.start_smooth_move)
                
    def on_key_release(self, event):
        key = event.keysym
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)
        arrows = {'Up', 'Down', 'Left', 'Right'}
        if not (self.pressed_keys & arrows):
            if self.move_loop_id:
                self.view.after_cancel(self.move_loop_id)
                self.move_loop_id = None
            self.is_holding = False
            self.ctrl_canvas.commit_selection_position()

    def start_smooth_move(self):
        self.is_holding = True
        self.move_loop()

    def move_loop(self):
        if not self.pressed_keys or not self.selected_field:
            self.move_loop_id = None
            return
        self.perform_move_step()
        self.move_loop_id = self.view.after(15, self.move_loop)

    def perform_move_step(self):
        is_fast = ('Shift_L' in self.pressed_keys) or ('Shift_R' in self.pressed_keys)
        speed = 10 if is_fast else 1 
        dx, dy = 0, 0
        if 'Up' in self.pressed_keys:    dy -= speed
        if 'Down' in self.pressed_keys:  dy += speed
        if 'Left' in self.pressed_keys:  dx -= speed
        if 'Right' in self.pressed_keys: dx += speed
        if dx != 0 or dy != 0:
            self.ctrl_canvas.visual_move_selection(dx, dy)
    
    def on_canvas_right_click(self, event):
        if self.has_template():
            self.ctrl_canvas.handle_right_click(event)

    def disable_field(self, field_name):
        if self.model.delete_field_permanently(field_name):
            if hasattr(self.view, 'p_left'):
                if field_name in self.view.p_left.field_vars:
                    del self.view.p_left.field_vars[field_name]
                try:
                    if hasattr(self.view.p_left, 'field_widgets') and field_name in self.view.p_left.field_widgets:
                        widget = self.view.p_left.field_widgets[field_name]
                        widget.destroy() 
                        del self.view.p_left.field_widgets[field_name]
                except Exception as e: print(f"Lỗi xóa UI: {e}")

            if self.selected_field == field_name:
                self.selected_field = None
                if hasattr(self.view.p_left, 'highlight_selected_field'):
                    self.view.p_left.highlight_selected_field(None)

            self.render_canvas_safe()
            MsgHelper.show_info(f"Đã xóa vĩnh viễn trường '{field_name}'", "Thành công")

    # --- SỰ KIỆN LỌC (DÙNG MAP DYNAMIC) ---
    def on_date_filter_change(self, event):
        if not self.has_template(): return
        
        text = self.view.p_mid.cbb_date.get()
        key = self.map_date.get(text, "all")
        
        self.model.set_date_filter(key)
        self.deselect_all()
        self.refresh_mid_table()

    def on_cccd_filter_change(self, event):
        if not self.has_template(): return
        
        text = self.view.p_mid.cbb_cccd.get()
        key = self.map_cccd.get(text, "all")
        
        self.model.set_cccd_filter(key)
        self.deselect_all()
        self.refresh_mid_table()

    # --- [ĐÃ SỬA] XÓA LỌC & XÓA TEXT TÌM KIẾM ---
    def clear_filters(self):
        if self.model.df is None or self.model.df.empty: return
        
        self.model.filter_state["date"] = "all"
        self.model.filter_state["cccd"] = "all"
        self.model.current_search_keyword = ""       
        self.model.current_search_column = "Tất cả"  
        
        try:
            if len(self.view.p_mid.cbb_date['values']) > 0:
                self.view.p_mid.cbb_date.current(0)
            if len(self.view.p_mid.cbb_cccd['values']) > 0:
                self.view.p_mid.cbb_cccd.current(0)
            
            self.view.p_mid.cbb_filter.set("Tất cả")

            # --- [ĐOẠN QUAN TRỌNG] Gọi hàm clear của SearchView ---
            if hasattr(self.view.p_mid.search_view, 'clear_input'):
                self.view.p_mid.search_view.clear_input()
                
        except Exception: pass

        self.model.apply_filters()
        self.deselect_all()
        self.refresh_mid_table()