def format_cccd(value):
    """
    Chuẩn hóa số CCCD/CMND:
    - Tự động thêm số 0 ở đầu nếu bị mất do Excel đọc nhầm thành số.
    """
    if value is None: return ""
    
    # 1. Chuyển về chuỗi và xóa khoảng trắng/đuôi .0
    val_str = str(value).strip()
    if val_str.endswith(".0"):
        val_str = val_str[:-2]
        
    if val_str.lower() == "nan" or val_str == "":
        return ""

    # Nếu chuỗi không phải số thì trả về nguyên gốc
    if not val_str.isdigit():
        return val_str

    length = len(val_str)

    # 2. Logic "Sửa lỗi thông minh" CẬP NHẬT:
    
    # TRƯỜNG HỢP CCCD GẮN CHIP (12 SỐ):
    # Nếu độ dài là 10 hoặc 11 (tức là bị mất 1 hoặc 2 số 0 đầu) -> Thêm đủ 0 thành 12
    if 10 <= length <= 11:
        return val_str.zfill(12) 
    
    # TRƯỜNG HỢP CMND CŨ (9 SỐ):
    # Nếu chỉ có 8 số -> Thêm 0 vào đầu
    if length == 8:
        return "0" + val_str

    return val_str