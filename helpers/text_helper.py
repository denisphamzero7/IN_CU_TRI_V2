def format_cccd(value):
    """
    Chuẩn hóa hiển thị CCCD/CMND theo yêu cầu:
    - 11 số -> Thêm 0 đầu -> 12 số.
    - 9, 10, 12 số -> Giữ nguyên.
    """
    if value is None: return ""
    
    val_str = str(value).strip()
    
    # Xử lý rác và lỗi scientific notation (1.23E+11)
    if val_str.lower() in ["nan", "none", ""]: return ""
    if val_str.endswith(".0"): val_str = val_str[:-2]
    if "e+" in val_str.lower():
        try: val_str = "{:.0f}".format(float(val_str))
        except: pass

    if not val_str.isdigit(): return val_str

    length = len(val_str)

    # --- LOGIC CẬP NHẬT THEO YÊU CẦU MỚI ---
    
    # 1. TRƯỜNG HỢP 11 SỐ -> Thêm số 0 vào đầu
    if length == 11:
        return "0" + val_str
        
    # 2. CÁC TRƯỜNG HỢP KHÁC (9, 10, 12...) -> GIỮ NGUYÊN
    # Không can thiệp vào 8, 9, 10 số nữa.
    
    return val_str