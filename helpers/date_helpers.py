# helpers/date_helper.py

def format_date_text_vn(value):
    """
    Chuyển đổi ngày tháng từ YYYY-MM-DD sang chuỗi văn bản đầy đủ
    Ví dụ: 1996-04-16 -> Ngày 16 tháng 04 năm 1996
    """
    if not value:
        return ""

    str_val = str(value).strip()
    
    if " 00:00:00" in str_val:
        str_val = str_val.replace(" 00:00:00", "")
        
    if "-" in str_val:
        parts = str_val.split("-")
        if len(parts) == 3 and len(parts[0]) == 4:
            y, m, d = parts
            # Ghép thêm chữ Ngày, tháng, năm
            return f"{d}/{m}/{y}"
            
    return str_val