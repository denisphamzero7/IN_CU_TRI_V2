# layouts/main_layout.py
import tkinter as tk
from config.settings import COLORS

def create_3_columns(root):
    left = tk.Frame(root, bg=COLORS["light"], padx=15, pady=15)
    left.place(relx=0, rely=0, relwidth=0.22, relheight=1)
    
    mid = tk.Frame(root, bg="white", padx=10, pady=10, bd=1, relief="solid")
    mid.place(relx=0.22, rely=0, relwidth=0.43, relheight=1)
    
    right = tk.Frame(root, bg=COLORS["dark"])
    right.place(relx=0.65, rely=0, relwidth=0.35, relheight=1)
    return left, mid, right