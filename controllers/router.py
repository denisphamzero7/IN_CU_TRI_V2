# controllers/router.py
from models.data_model import VoterModel
from controllers.data_controller import DataController
from controllers.canvas_controller import CanvasController
from controllers.print_controller import PrintController
from tkinter import messagebox

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

        # --- [MỚI] Biến lưu trạng thái sắp xếp ---
        # reverse = False (Tăng dần), True (Giảm dần)
        self.sort_state = {"col": None, "reverse": False}
        
        # --- [OPTIMIZATION] Cờ chặn sự kiện ---
        # Khi biến này là True, sự kiện click chuột sẽ bị bỏ qua
        self.is_bulk_updating = False 

       # --- [THÊM MỚI] Cờ chặn cập nhật Style khi đang load UI ---
        self.is_loading_ui = False
    def set_view(self, view):
        self.view = view
        self.edit_mode = view.p_left.var_edit_mode

    # --- Actions ---
    def select_template(self): self.ctrl_data.select_template()
    def select_excel(self): self.ctrl_data.select_excel()
    def select_signature_folder(self): self.ctrl_data.select_signature_folder()
    def start_print(self): self.ctrl_print.print_batch()
    def exit_app(self):
        if messagebox.askyesno("Thoát", "Bạn muốn thoát chương trình?"):
            self.view.master.destroy()

    # --- Pagination Actions ---
    def next_page(self):
        if self.model.set_page(self.model.current_page + 1):
            self.refresh_mid_table()

    def prev_page(self):
        if self.model.set_page(self.model.current_page - 1):
            self.refresh_mid_table()

    def refresh_mid_table(self):
        """Load dữ liệu và khôi phục trạng thái chọn (Đã tối ưu)"""
        if self.model.df is None: return

        # Bật cờ update để chặn sự kiện select nổ ra lung tung khi đang vẽ bảng
        self.is_bulk_updating = True 

        # 1. Update Data
        df_page = self.model.get_current_page_data()
        self.view.p_mid.update_data(df_page, self.model.custom_configs)
        self.view.p_mid.update_pagination_label(self.model.current_page, self.model.total_pages)
        # --- [MỚI] Cập nhật danh sách cho Combobox (nếu chưa có) ---
        # Logic: Chỉ nạp 1 lần khi load file excel xong hoặc khi list trống
        current_values = self.view.p_mid.cbb_filter['values']
        # Nếu combobox chưa có dữ liệu hoặc khác dữ liệu model thì cập nhật
        if not current_values or (len(current_values) == 0 and len(self.model.unique_areas) > 0):
            self.view.p_mid.cbb_filter['values'] = self.model.unique_areas
            if self.model.unique_areas:
                self.view.p_mid.cbb_filter.current(0) # Mặc định chọn "Tất cả"
        # -----------------------------------------------------------
        
        # 2. Khôi phục chọn (Selection)
        # gom các ID cần chọn lại vào 1 list rồi select 1 lần sẽ nhanh hơn loop
        items_to_select = []
        for item_id in self.view.p_mid.tree.get_children():
            if int(item_id) in self.model.selected_indices:
                items_to_select.append(item_id)
        
        if items_to_select:
            self.view.p_mid.tree.selection_set(items_to_select)
        
        # 3. Update Label
        self.update_count_label()
        
        # Tắt cờ update
        self.is_bulk_updating = False
    # --- [MỚI] Sự kiện xử lý bộ lọc ---
    def on_filter_change(self, event):
        """Khi người dùng chọn khu vực khác"""
        selected_area = self.view.p_mid.cbb_filter.get()
        
        # 1. Gọi Model lọc dữ liệu
        self.model.filter_data(selected_area)
        
        # 2. Xóa lựa chọn cũ (để tránh in nhầm người không còn hiển thị)
        self.deselect_all()

        # 3. Refresh lại bảng (Tự động về trang 1 của danh sách mới)
        self.refresh_mid_table()

    # --- UI Events (Đã tối ưu) ---
    def on_user_select_change(self, event):
        """
        Sự kiện này chỉ chạy khi NGƯỜI DÙNG click chuột.
        Nếu code tự chạy (select_all), ta sẽ chặn lại nhờ biến is_bulk_updating
        """
        if self.model.df is None: return
        
        # [QUAN TRỌNG] Nếu đang update hàng loạt bằng code thì thoát ngay, không tính toán gì cả
        if self.is_bulk_updating: return

        # 1. Đồng bộ Model
        visible_ids = self.view.p_mid.tree.get_children()
        visible_ints = {int(x) for x in visible_ids}
        
        selected_ids = self.view.p_mid.tree.selection()
        selected_ints = {int(x) for x in selected_ids}
        
        self.model.selected_indices -= visible_ints
        self.model.selected_indices.update(selected_ints)
        
        self.update_count_label()

        # 2. Render Canvas (Chỉ render nếu người dùng focus vào 1 người cụ thể)
        # Fix lag: Không render nếu chỉ đang kéo chọn nhiều người
        focus_item = self.view.p_mid.tree.focus()
        target_id = focus_item if focus_item else (selected_ids[0] if selected_ids else None)

        if target_id:
            try:
                new_idx = int(target_id)
                # Chỉ render lại nếu người được chọn KHÁC người hiện tại
                if new_idx != self.current_idx:
                    self.current_idx = new_idx
                    self.ctrl_canvas.render()
                    if self.selected_field:
                        self.load_field_props_to_ui()
            except ValueError: pass

    def select_all(self):
        """Chọn tất cả (Tối ưu: Không kích hoạt sự kiện select change)"""
        self.is_bulk_updating = True # <-- Bật cờ chặn sự kiện
        
        children = self.view.p_mid.tree.get_children()
        self.view.p_mid.tree.selection_set(children)
        
        ids = {int(x) for x in children}
        self.model.selected_indices.update(ids)
        
        self.update_count_label()
        self.is_bulk_updating = False # <-- Tắt cờ

    def deselect_all(self):
        """Bỏ chọn tất cả (Tối ưu)"""
        self.is_bulk_updating = True
        
        children = self.view.p_mid.tree.get_children()
        self.view.p_mid.tree.selection_set([])
        
        ids = {int(x) for x in children}
        self.model.selected_indices -= ids
        
        self.update_count_label()
        self.is_bulk_updating = False

    def update_count_label(self):
        count = len(self.model.selected_indices)
        self.view.p_mid.lbl_count.config(text=f"Đã chọn: {count} người")

    # ... (Các hàm còn lại giữ nguyên: select_field, on_prop_change, v.v.)
    def on_field_toggle(self, col):
        is_on = self.view.p_left.field_vars[col].get()
        self.model.update_config_value(self.current_idx, "global", col, "enable", is_on)
        self.ctrl_canvas.render()

    def select_field(self, col):
        self.selected_field = col
        self.load_field_props_to_ui()

    def load_field_props_to_ui(self):
        """Đổ dữ liệu từ Config vào các ô nhập liệu (View)"""
        if not self.selected_field: return
        
        # --- BẮT ĐẦU KHÓA: Chặn sự kiện on_prop_change ---
        self.is_loading_ui = True 
        
        try:
            cfg = self.model.get_effective_config(self.current_idx).get(self.selected_field, {})
            # Gọi hàm update UI của View
            self.view.p_left.update_prop_inputs(cfg, self.selected_field)
        finally:
            # --- MỞ KHÓA: Cho phép cập nhật trở lại ---
            self.is_loading_ui = False

    def on_style_change(self):
        self.ctrl_canvas.render()
        if self.selected_field:
            self.load_field_props_to_ui()

    def on_prop_change(self, event=None):
        """Hàm xử lý khi người dùng thay đổi Style"""
        # 1. Kiểm tra cơ bản
        if not self.selected_field: return
        
        # 2. [FIX BUG] Nếu đang trong quá trình load UI (đổ dữ liệu vào ô), 
        # thì KHÔNG được lưu ngược lại Model.
        if self.is_loading_ui: return

        view_l = self.view.p_left
        mode = self.edit_mode.get()
        col = self.selected_field
        
        try:
            if col == "signature_img":
                # Xử lý riêng cho Ảnh chữ ký (Width/Height)
                # Dùng try/except nhỏ để nếu nhập sai thì lấy giá trị mặc định, không làm crash app
                try: w = int(view_l.spin_img_w.get())
                except ValueError: w = 150 # Giá trị mặc định
                
                try: h = int(view_l.spin_img_h.get())
                except ValueError: h = 80 # Giá trị mặc định

                self.model.update_config_value(self.current_idx, mode, col, "w", w)
                self.model.update_config_value(self.current_idx, mode, col, "h", h)
            else:
                # Xử lý cho Text (Họ tên, ngày sinh...)
                
                # 1. Font & Color (String nên ít lỗi)
                self.model.update_config_value(self.current_idx, mode, col, "font", view_l.combo_font.get())
                self.model.update_config_value(self.current_idx, mode, col, "color", view_l.combo_color.get())
                
                # 2. Size (Dễ lỗi nhất -> Cần bắt lỗi riêng)
                try:
                    size_val = int(view_l.spin_size.get())
                except ValueError:
                    size_val = 14 # Mặc định nếu ô trống
                self.model.update_config_value(self.current_idx, mode, col, "size", size_val)
                
                # 3. Bold & Upper (Boolean)
                self.model.update_config_value(self.current_idx, mode, col, "bold", view_l.chk_bold_var.get())
                self.model.update_config_value(self.current_idx, mode, col, "upper", view_l.chk_upper_var.get())

        except Exception as e:
            print(f"Lỗi Update Style: {e}") # In lỗi ra Console để dễ debug thay vì im lặng

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
        # --- [THÊM ĐOẠN NÀY] Kiểm tra xem có dữ liệu chưa ---
        if self.model.df is None or self.model.df.empty:
            messagebox.showwarning("Chú ý", "Chưa có dữ liệu để Reset!")
            return
        # ----------------------------------------------------
        if self.model.reset_custom_config(self.current_idx):
            self.view.p_mid.tree.item(str(self.current_idx), tags=())
            self.ctrl_canvas.render()
            if self.selected_field: self.load_field_props_to_ui()
            messagebox.showinfo("Reset", "Đã xóa cấu hình riêng của người này.")

    def pick_manual_signature(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("Image", "*.png;*.jpg")])
        if path:
            self.edit_mode.set("individual")
            self.model.update_config_value(self.current_idx, "individual", "signature_img", "path", path)
            self.model.update_config_value(self.current_idx, "individual", "signature_img", "enable", True)
            self.view.p_mid.tree.item(str(self.current_idx), tags=('custom',))
            self.ctrl_canvas.render()

    def on_shift_zoom(self, event): self.ctrl_canvas.handle_zoom(event)
    def on_drag_start(self, event): self.ctrl_canvas.drag_start(event)
    def on_drag_motion(self, event): self.ctrl_canvas.drag_motion(event)
    def on_drag_end(self, event): self.ctrl_canvas.drag_end(event)
    def on_canvas_resize(self, event): self.ctrl_canvas.on_resize(event)
    def on_header_click(self, col_id):
        """Xử lý khi bấm vào tiêu đề cột"""
        
        # 1. Tính toán hướng sắp xếp (Toggle)
        new_reverse = False
        if self.sort_state["col"] == col_id:
            # Nếu bấm lại cột cũ -> Đảo ngược thứ tự
            new_reverse = not self.sort_state["reverse"]
        
        # Lưu trạng thái mới
        self.sort_state = {"col": col_id, "reverse": new_reverse}
        
        # 2. Gọi Model xử lý dữ liệu
        self.model.sort_data(col_id, new_reverse)
        
        # 3. Cập nhật giao diện (Mũi tên trên Header)
        self.view.p_mid.update_header_arrow(col_id, new_reverse)
        
        # 4. Vẽ lại bảng dữ liệu
        # Lưu ý: Reset select để tránh lỗi highlight sai dòng sau khi đảo thứ tự
        self.deselect_all() 
        self.refresh_mid_table()
