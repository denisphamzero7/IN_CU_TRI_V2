import win32print

class PrinterHelper:
    @staticmethod
    def get_all_printers():
        """Lấy danh sách tất cả máy in đang kết nối"""
        try:
            flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            # EnumPrinters trả về list các tuple, phần tử thứ 2 (index 2) là tên máy in
            printers = [p[2] for p in win32print.EnumPrinters(flags)]
            return sorted(printers)
        except Exception as e:
            print(f"Lỗi lấy danh sách máy in: {e}")
            return []

    @staticmethod
    def get_default_printer():
        """Lấy tên máy in mặc định của hệ thống"""
        try:
            return win32print.GetDefaultPrinter()
        except:
            return ""