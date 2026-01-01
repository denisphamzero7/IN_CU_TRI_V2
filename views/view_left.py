# views/view_left.py
import tkinter as tk
from tkinter import ttk
from helpers.ui_helpers import RoundedButton
from config.settings import COLORS

class LeftPanelView:
    def __init__(self, parent, router):
        self.router = router
        self.field_vars = {}
        self.field_labels = {}
        
        # --- 1. Nút chức năng ---
        lbl_input = tk.Label(parent, text="1. DỮ LIỆU ĐẦU VÀO", font=("Segoe UI", 12, "bold"), bg=COLORS["light"])
        lbl_input.pack(anchor="w", pady=(0, 5))
        
        btn_frame = tk.Frame(parent, bg=COLORS["light"])
        btn_frame.pack(fill="x", pady=5)
        RoundedButton(btn_frame, text="📂 Chọn Ảnh Phôi", command=router.select_template, bg=COLORS["primary"]).pack(fill="x", pady=2)
        RoundedButton(btn_frame, text="📊 Chọn File Excel", command=router.select_excel, bg=COLORS["success"]).pack(fill="x", pady=2)
        RoundedButton(btn_frame, text="📂 Folder Chữ Ký", command=router.select_signature_folder, bg=COLORS["purple"]).pack(fill="x", pady=2)
        
        # --- 2. Danh sách trường ---
        tk.Label(parent, text="2. CẤU HÌNH TRƯỜNG", font=("Segoe UI", 12, "bold"), bg=COLORS["light"]).pack(anchor="w", pady=(20, 5))
        
        list_container = tk.Frame(parent, bg="white", bd=1, relief="solid")
        list_container.pack(fill="both", expand=True, pady=5)
        
        self.canvas_list = tk.Canvas(list_container, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.canvas_list.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas_list, bg="white")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas_list.configure(scrollregion=self.canvas_list.bbox("all")))
        
        self.canvas_list.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas_list.configure(yscrollcommand=scrollbar.set)
        
        self.canvas_list.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        scrollbar.pack(side="right", fill="y")
        
        # --- 3. Style Controls ---
        self._setup_style_controls(parent)
        
        # Nút Thoát
        RoundedButton(parent, text="❌ Thoát", command=router.exit_app, bg="#7f8c8d").pack(side="bottom", fill="x", pady=10)

    def _setup_style_controls(self, parent):
        style_frame = tk.LabelFrame(parent, text="3. TÙY CHỈNH STYLE", font=("Segoe UI", 11, "bold"), bg=COLORS["grey"], padx=5, pady=5)
        style_frame.pack(fill="x", pady=10, side="bottom")
        
        self.var_edit_mode = tk.StringVar(value="global")
        tk.Radiobutton(style_frame, text="Chỉnh cho TẤT CẢ", variable=self.var_edit_mode, value="global", bg=COLORS["grey"], command=self.router.on_style_change).pack(anchor="w")
        tk.Radiobutton(style_frame, text="Chỉnh RIÊNG người này", variable=self.var_edit_mode, value="individual", bg=COLORS["grey"], fg="red", font=("Segoe UI", 9, "bold"), command=self.router.on_style_change).pack(anchor="w")
        
        tk.Frame(style_frame, height=1, bg="white").pack(fill="x", pady=5)
        
        tk.Label(style_frame, text="Đang chọn:", bg=COLORS["grey"]).pack(anchor="w")
        self.lbl_current_field = tk.Label(style_frame, text="(Chưa chọn)", fg="blue", bg=COLORS["grey"], font=("Segoe UI", 10, "bold"))
        self.lbl_current_field.pack(anchor="w", pady=(0, 5))
        
        # -- Controls cho Text --
        self.fr_text_props = tk.Frame(style_frame, bg=COLORS["grey"])
        
        # Font & Size
        r1 = tk.Frame(self.fr_text_props, bg=COLORS["grey"])
        r1.pack(fill="x")
        self.combo_font = ttk.Combobox(r1, values=["Arial", "Times New Roman"], width=13, state="readonly")
        self.combo_font.pack(side="left")
        self.combo_font.bind("<<ComboboxSelected>>", self.router.on_prop_change)
        
        self.spin_size = tk.Spinbox(r1, from_=5, to=300, width=5, command=self.router.on_prop_change)
        self.spin_size.pack(side="left", padx=5)
        self.spin_size.bind("<Return>", self.router.on_prop_change)
        
        # Bold, Upper, Color
        r2 = tk.Frame(self.fr_text_props, bg=COLORS["grey"])
        r2.pack(fill="x", pady=5)
        self.chk_bold_var = tk.BooleanVar()
        self.chk_upper_var = tk.BooleanVar()
        tk.Checkbutton(r2, text="B", variable=self.chk_bold_var, bg=COLORS["grey"], font="Arial 9 bold", command=self.router.on_prop_change).pack(side="left")
        tk.Checkbutton(r2, text="AA", variable=self.chk_upper_var, bg=COLORS["grey"], command=self.router.on_prop_change).pack(side="left")
        
        self.combo_color = ttk.Combobox(r2, values=["Black", "Red", "Blue"], width=8, state="readonly")
        self.combo_color.pack(side="left", padx=5)
        self.combo_color.bind("<<ComboboxSelected>>", self.router.on_prop_change)
        
        self.fr_text_props.pack(fill="x")
        
        # -- Controls cho Ảnh (Chữ ký) --
        self.fr_img_props = tk.Frame(style_frame, bg=COLORS["grey"])
        self.btn_manual_sig = RoundedButton(self.fr_img_props, text="📂 File chữ ký", command=self.router.pick_manual_signature, bg=COLORS["warning"], height=25)
        self.btn_manual_sig.pack(fill="x", pady=5)
        
        r_img = tk.Frame(self.fr_img_props, bg=COLORS["grey"])
        r_img.pack(fill="x")
        tk.Label(r_img, text="Rộng:", bg=COLORS["grey"]).pack(side="left")
        self.spin_img_w = tk.Spinbox(r_img, from_=1, to=1000, width=5, command=self.router.on_prop_change)
        self.spin_img_w.pack(side="left")
        tk.Label(r_img, text="Cao:", bg=COLORS["grey"]).pack(side="left", padx=(5,0))
        self.spin_img_h = tk.Spinbox(r_img, from_=1, to=1000, width=5, command=self.router.on_prop_change)
        self.spin_img_h.pack(side="left")
        self.spin_img_w.bind("<Return>", self.router.on_prop_change)
        self.spin_img_h.bind("<Return>", self.router.on_prop_change)
        
        # Reset button
        RoundedButton(style_frame, text="↺ Reset Default", command=self.router.reset_current_custom, bg=COLORS["danger"], height=25).pack(fill="x", pady=10)

    def refresh_field_list(self, cols, global_config):
        for w in self.scrollable_frame.winfo_children(): w.destroy()
        self.field_vars = {}
        self.field_labels = {}
        
        # Luôn đảm bảo có signature_img
        display_cols = list(cols)
        if "signature_img" not in display_cols: display_cols.append("signature_img")
        
        for col in display_cols:
            row_fr = tk.Frame(self.scrollable_frame, bg="white")
            row_fr.pack(fill="x", pady=2)
            
            is_enabled = global_config.get(col, {}).get("enable", False)
            var = tk.BooleanVar(value=is_enabled)
            self.field_vars[col] = var
            
            chk = tk.Checkbutton(row_fr, variable=var, bg="white", command=lambda c=col: self.router.on_field_toggle(c))
            chk.pack(side="left")
            
            display_text = "📷 ẢNH CHỮ KÝ" if col == "signature_img" else col
            lbl = tk.Label(row_fr, text=display_text, bg="white", anchor="w", cursor="hand2", font=("Segoe UI", 10))
            lbl.pack(side="left", fill="x", expand=True)
            lbl.bind("<Button-1>", lambda e, c=col: self.router.select_field(c))
            self.field_labels[col] = lbl

    def update_prop_inputs(self, cfg, field_name):
        self.lbl_current_field.config(text=field_name)
        
        # Highlight label
        for f, lbl in self.field_labels.items():
            if f == field_name:
                lbl.config(bg="#dff9fb", fg="blue", font=("Segoe UI", 10, "bold"))
            else:
                lbl.config(bg="white", fg="black", font=("Segoe UI", 10))
        
        if field_name == "signature_img":
            self.fr_text_props.pack_forget()
            self.fr_img_props.pack(fill="x")
            
            self.spin_img_w.delete(0, tk.END)
            self.spin_img_w.insert(0, cfg.get("w", 150))
            self.spin_img_h.delete(0, tk.END)
            self.spin_img_h.insert(0, cfg.get("h", 80))
        else:
            self.fr_img_props.pack_forget()
            self.fr_text_props.pack(fill="x")
            
            self.combo_font.set(cfg.get("font", "Arial"))
            self.spin_size.delete(0, tk.END)
            self.spin_size.insert(0, cfg.get("size", 30))
            self.chk_bold_var.set(cfg.get("bold", False))
            self.chk_upper_var.set(cfg.get("upper", False))
            self.combo_color.set(cfg.get("color", "Black"))