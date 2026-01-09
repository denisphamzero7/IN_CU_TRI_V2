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
        self.ctrl_data = DataController(self)
        self.ctrl_canvas = CanvasController(self)
        self.ctrl_print = PrintController(self)
        # [MỚI] Khởi tạo quản lý bản quyền
       # [MỚI] Khởi tạo License Controller
        self.ctrl_license = LicenseController(self)

        self.current_idx = 0
        self.selected_field = None
        self.edit_mode = None 
        self.search_timer = None
        self.sort_state = {"col": None, "reverse": False}
        self.is_bulk_updating = False 
        self.is_loading_ui = False
        
        # --- Cấu hình mặc định ---
        self.is_paper_landscape = True 
        self.template_rotation = 0   

        # --- [THÊM] Biến quản lý trạng thái phím ---
        self.pressed_keys = set()  # Lưu các phím đang được giữ
        self.move_loop_id = None   # ID của vòng lặp after     

    def set_view(self, view):
        self.view = view
        if hasattr(view.p_left, 'var_edit_mode'):
            self.edit_mode = view.p_left.var_edit_mode
        # [MỚI] Kiểm tra bản quyền ngay khi view đã load xong
        self.ctrl_license.set_view(view)
        # Check bản quyền ngay khi view load xong
        self.ctrl_license.check_at_startup()

    # --- HÀM KIỂM TRA PHÔI ---
    def has_template(self):
        """Kiểm tra xem Model đã có đường dẫn ảnh phôi chưa."""
        if hasattr(self.model, 'template_path') and self.model.template_path:
            return True
        return False

    # --- HÀM VẼ CANVAS AN TOÀN ---
    def render_canvas_safe(self):
        # Nếu chưa có phôi -> Không cho hiển thị dữ liệu lên canvas.
        if not self.has_template():
            if hasattr(self.ctrl_canvas, 'canvas'):
                self.ctrl_canvas.canvas.delete("all")
                w = self.ctrl_canvas.canvas.winfo_width()
                h = self.ctrl_canvas.canvas.winfo_height()
                self.ctrl_canvas.canvas.create_text(w/2, h/2, text="Chưa chọn ảnh phôi", font=("Arial", 16), fill="gray")
            return
            
        self.ctrl_canvas.render()

    # --- CÁC HÀM XỬ LÝ KHÁC ---
    def on_orientation_change(self, event=None):
        val = self.view.p_right.var_orientation.get()
        if val == "Ngang": 
            self.is_paper_landscape = True 
            self.template_rotation = 0
        else:
            self.is_paper_landscape = False 
            self.template_rotation = 0
        self.render_canvas_safe()

    def rotate_template_right(self):
        self.template_rotation = (self.template_rotation + 90) % 360
        self.render_canvas_safe()

    def start_print(self):
        if not self.ctrl_license.is_licensed:
            MsgHelper.show_warning("Tính năng IN chỉ dành cho bản Pro!")
            return
        # 1. Kiểm tra điều kiện tiên quyết
        if not self.has_template(): 
            return MsgHelper.show_warning("Vui lòng chọn phôi trước!") 
        
        if self.model.df is None or self.model.df.empty:
            return MsgHelper.show_warning("Chưa có dữ liệu!")

        try:
            val_from = self.view.p_right.var_print_from.get().strip()
            val_to = self.view.p_right.var_print_to.get().strip()

            if not val_from:
                if hasattr(self.view.p_right, 'entry_from'):
                    self.view.p_right.entry_from.focus()
                return MsgHelper.show_warning("Vui lòng nhập số thứ tự bắt đầu (Từ)!")
            
            if not val_to:
                if hasattr(self.view.p_right, 'entry_to'):
                    self.view.p_right.entry_to.focus()
                return MsgHelper.show_warning("Vui lòng nhập số thứ tự kết thúc (Đến)!")

            start_row = int(val_from)
            end_row = int(val_to)
            
            max_row = len(self.model.df)
            start_row = max(1, min(start_row, max_row))
            end_row = max(1, min(end_row, max_row))

            if start_row > end_row: 
                return MsgHelper.show_error(f"Lỗi: Số 'Từ' ({start_row}) không được lớn hơn số 'Đến' ({end_row})!")

            custom_indices = list(range(start_row - 1, end_row))
            self.ctrl_print.print_batch(custom_indices)

        except ValueError:
            return MsgHelper.show_error("Lỗi: Vui lòng chỉ nhập số nguyên vào ô khoảng in!")

    def pick_manual_signature(self):
        if not self.ctrl_license.is_licensed:
            MsgHelper.show_warning("Vui lòng đăng kí bẳn quyền!")
            return
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

    def on_style_change(self):
        self.render_canvas_safe()
        if self.selected_field: self.load_field_props_to_ui()

    def select_template(self): self.ctrl_data.select_template()
    def select_excel(self): self.ctrl_data.select_excel()
    def select_signature_folder(self): self.ctrl_data.select_signature_folder()
    
    def exit_app(self):
        if MsgHelper.ask_yes_no("Thoát?", parent=self.view): self.view.master.destroy()

    def refresh_mid_table(self):
        if self.model.df is None: return

        self.is_bulk_updating = True 
        try:
            df_page = self.model.get_current_page_data()
            self.view.p_mid.update_data(df_page, self.model.custom_configs)
            self.view.p_mid.update_pagination_label(self.model.current_page, self.model.total_pages)
            
            if list(self.view.p_mid.cbb_filter['values']) != self.model.unique_areas:
                 self.view.p_mid.cbb_filter['values'] = self.model.unique_areas
        except Exception as e:
            print(f"Lỗi refresh table: {e}")
        finally:
            self.is_bulk_updating = False

    def next_page(self):
        if self.model.set_page(self.model.current_page + 1): self.refresh_mid_table()

    def prev_page(self):
        if self.model.set_page(self.model.current_page - 1): self.refresh_mid_table()

    def on_filter_change(self, event):
        if not self.has_template(): return 
        self.model.filter_data(self.view.p_mid.cbb_filter.get())
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
            
            # 1. Gọi Left Panel để tô màu dòng chọn
            if hasattr(self.view.p_left, 'highlight_selected_field'):
                self.view.p_left.highlight_selected_field(self.selected_field)
            
            # 2. Gọi Right Panel để điền thông số vào Toolbar [MỚI]
            self.view.p_right.update_prop_inputs(cfg, self.selected_field)
            
        finally: self.is_loading_ui = False 
    def on_prop_change(self, event=None):
        if not self.selected_field or self.is_loading_ui: return
        if not self.has_template(): return 
        
        # [QUAN TRỌNG] Lấy dữ liệu từ VIEW.P_RIGHT (Bên phải)
        view = self.view.p_right 
        
        mode = "global"
        if hasattr(self.view.p_left, 'var_edit_mode'): # Edit mode vẫn nằm bên trái (nếu bạn chưa chuyển)
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

    def update_field_config(self, k, v):
        if not self.has_template(): return
        if self.selected_field:
            mode = "global"
            try: mode = self.edit_mode.get()
            except: pass
            self.model.update_config_value(self.current_idx, mode, self.selected_field, k, v)

    def reset_current_custom(self):
        if not self.has_template(): 
            return MsgHelper.show_warning("Vui lòng chọn ảnh phôi trước khi thực hiện!")
        
        mode = "global"
        try: mode = self.edit_mode.get()
        except: pass

        if mode == "individual":
            if self.model.reset_custom_config(self.current_idx):
                self.view.p_mid.tree.item(str(self.current_idx), tags=())
                self.render_canvas_safe()
                if self.selected_field: self.load_field_props_to_ui()
                MsgHelper.show_info("Đã xóa cấu hình riêng.", "Thành công")
            else:
                MsgHelper.show_info("Người này đang sử dụng cấu hình chung.", "Thông báo")
        else:
            if not self.selected_field:
                return MsgHelper.show_warning("Vui lòng chọn một trường để reset!")

            if MsgHelper.ask_yes_no(f"Bạn có chắc muốn đưa cấu hình chung của '{self.selected_field}' về mặc định gốc?", "Xác nhận"):
                self.model.update_config_value(0, "global", self.selected_field, "font", "Arial")
                self.model.update_config_value(0, "global", self.selected_field, "size", 14)
                self.model.update_config_value(0, "global", self.selected_field, "bold", False)
                self.model.update_config_value(0, "global", self.selected_field, "color", "Black")
                
                self.render_canvas_safe()
                self.load_field_props_to_ui()
                MsgHelper.show_info("Đã khôi phục mặc định cho trường này.", "Thành công")

    def deselect_all(self):
        self.is_bulk_updating = True
        try: self.view.p_mid.tree.selection_set([])
        except: pass
        self.model.selected_indices.clear()
        self.is_bulk_updating = False

    def select_all(self): pass 

    def on_header_click(self, col):
        if not self.has_template(): return
        if self.sort_state["col"] == col:
            self.sort_state["reverse"] = not self.sort_state["reverse"]
        else:
            self.sort_state["col"] = col
            self.sort_state["reverse"] = False
            
        self.model.sort_data(col, self.sort_state["reverse"])
        if self.view and hasattr(self.view, 'p_mid'):
            self.view.p_mid.update_header_arrow(col, self.sort_state["reverse"])
        self.refresh_mid_table()

    # --- CANVAS HANDLERS ---
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
    def on_paper_config_change(self, e=None): self.render_canvas_safe()

   # --- [CHỈNH SỬA LẠI ĐOẠN NÀY] KEYBOARD HANDLER CHUẨN OS ---
    def on_key_press(self, event):
        """Khi nhấn phím"""
        key = event.keysym
        valid_keys = ('Up', 'Down', 'Left', 'Right', 'Shift_L', 'Shift_R')
        
        if key not in valid_keys: return
        
        # Nếu phím này đã được ghi nhận là đang nhấn rồi thì bỏ qua (chặn auto-repeat của OS)
        if key in self.pressed_keys: return
        
        # Nếu đây là phím đầu tiên được nhấn (bắt đầu chuỗi hành động)
        first_press = (len(self.pressed_keys) == 0)
        
        self.pressed_keys.add(key)
        
        if first_press:
            # 1. DI CHUYỂN NGAY LẬP TỨC 1 LẦN (Cho cú nhấp)
            self.perform_move_step()
            
            # 2. Thiết lập Delay (Khựng lại 400ms) trước khi bắt đầu chạy mượt
            # Nếu nhả tay trước 400ms -> move_loop không bao giờ chạy -> Không bị trượt
            self.is_holding = False
            self.move_loop_id = self.view.after(400, self.start_smooth_move)
                
    def on_key_release(self, event):
        """Khi thả phím"""
        key = event.keysym
        if key in self.pressed_keys:
            self.pressed_keys.remove(key)

        # Kiểm tra xem còn phím mũi tên nào không
        arrows = {'Up', 'Down', 'Left', 'Right'}
        if not (self.pressed_keys & arrows):
            # Nếu không còn phím điều hướng -> Hủy mọi vòng lặp
            if self.move_loop_id:
                self.view.after_cancel(self.move_loop_id)
                self.move_loop_id = None
            
            self.is_holding = False
            # Lưu vị trí cuối cùng vào Model
            self.ctrl_canvas.commit_selection_position()

    def start_smooth_move(self):
        """Bắt đầu vào chế độ di chuyển mượt sau khi đã delay"""
        self.is_holding = True
        self.move_loop()

    def move_loop(self):
        """Vòng lặp di chuyển liên tục"""
        if not self.pressed_keys or not self.selected_field:
            self.move_loop_id = None
            return

        self.perform_move_step()

        # Tốc độ lặp lại: 15ms (Khoảng 60 FPS) -> Đủ mượt mà không quá nhanh
        self.move_loop_id = self.view.after(15, self.move_loop)

    def perform_move_step(self):
        """Hàm thực hiện 1 bước di chuyển"""
        # Kiểm tra Shift để tăng tốc
        is_fast = ('Shift_L' in self.pressed_keys) or ('Shift_R' in self.pressed_keys)
        
        # TỐC ĐỘ:
        # - Bình thường: 1px (Chính xác tuyệt đối)
        # - Giữ Shift: 10px (Di chuyển nhanh)
        speed = 10 if is_fast else 1 
        
        dx, dy = 0, 0
        if 'Up' in self.pressed_keys:    dy -= speed
        if 'Down' in self.pressed_keys:  dy += speed
        if 'Left' in self.pressed_keys:  dx -= speed
        if 'Right' in self.pressed_keys: dx += speed

        if dx != 0 or dy != 0:
            self.ctrl_canvas.visual_move_selection(dx, dy)