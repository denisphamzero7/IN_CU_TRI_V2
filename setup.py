import os
from setuptools import setup, Extension
from Cython.Build import cythonize

# ---------------------------------------------------------
# CẤU HÌNH BUILD
# ---------------------------------------------------------

# Danh sách các thư mục chứa code cần bảo vệ/tăng tốc
target_folders = [
    "controllers",
    "models",
    "views",
    "helpers",
    "layouts",
    "config" 
]

extensions = []

print("🚀 Đang quét file để mã hóa...")

for folder in target_folders:
    # 1. Kiểm tra thư mục có tồn tại không để tránh lỗi
    if not os.path.exists(folder):
        print(f"⚠️  Bỏ qua (không tìm thấy): {folder}")
        continue

    # 2. Duyệt file trong thư mục
    count = 0
    for filename in os.listdir(folder):
        # Chỉ lấy file .py, BỎ QUA __init__.py (để giữ cấu trúc package python)
        if filename.endswith(".py") and filename != "__init__.py":
            
            # Tạo đường dẫn: controllers/home_controller.py
            filepath = os.path.join(folder, filename)
            
            # Tên module: controllers.home_controller
            module_name = filepath.replace(os.path.sep, ".").replace(".py", "")
            
            extensions.append(Extension(module_name, [filepath]))
            count += 1
    
    if count > 0:
        print(f"   -> {folder}: Đã thêm {count} file.")

# ---------------------------------------------------------
# THỰC HIỆN BUILD
# ---------------------------------------------------------
if extensions:
    print(f"\n📦 Bắt đầu build tổng cộng {len(extensions)} modules...")
    
    setup(
        ext_modules=cythonize(
            extensions,
            compiler_directives={
                'language_level': "3",       # Sử dụng Python 3
                'always_allow_keywords': True # Cho phép dùng keyword linh hoạt
            },
            build_dir="build_temp" # Gom rác (file .c) vào thư mục này cho gọn
        )
    )
    print("\n✅ Build thành công! Hãy kiểm tra các file .pyd (hoặc .so).")
else:
    print("\n❌ Không tìm thấy file .py nào hợp lệ để build!")