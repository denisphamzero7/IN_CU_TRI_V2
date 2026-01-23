def format_cccd(value):
    """
    Hiển thị CCCD: 
    - TUYỆT ĐỐI KHÔNG SỬA DỮ LIỆU.
    - 123456789012.0 -> Giữ nguyên 123456789012.0
    - Chỉ thêm số 0 vào đầu NẾU VÀ CHỈ NẾU chuỗi đó thuần túy là 11 CHỮ SỐ (không chấm, không phẩy).
    """
    if value is None: return ""
    
    # Ép về string để hiển thị
    val_str = str(value).strip()
    
    # Bỏ qua giá trị rỗng của Pandas
    if val_str.lower() in ["nan", "none", ""]: return ""
    
    # --- ĐÃ XÓA ĐOẠN CẮT DUÔI .0 ---
    # Trước đây: if val_str.endswith(".0"): val_str = val_str[:-2]
    # Bây giờ: Kệ nó.
    
    # Chỉ xử lý thêm số 0 nếu nó sạch sẽ là 11 số
    # Trường hợp "12345678901.0" (có chấm) -> isdigit() = False -> Không thêm 0 -> Trả về nguyên gốc
    if val_str.isdigit() and len(val_str) == 11:
        return "0" + val_str
        
    # Trả về nguyên bản bất kể nó là gì (số khoa học, số thập phân, text rác...)
    return val_str