import time
import ctypes
import pyperclip

def is_clipboard_image_or_file() -> bool:
    """Kiểm tra xem clipboard hiện tại có đang chứa hình ảnh hoặc file hay không (trên Windows)."""
    try:
        if ctypes.windll.user32.OpenClipboard(None):
            # Kiểm tra định dạng ảnh CF_DIB (8), CF_BITMAP (2) hoặc CF_HDROP (15 - file)
            has_data = (
                ctypes.windll.user32.IsClipboardFormatAvailable(2) or   # CF_BITMAP
                ctypes.windll.user32.IsClipboardFormatAvailable(8) or   # CF_DIB
                ctypes.windll.user32.IsClipboardFormatAvailable(15)     # CF_HDROP
            )
            ctypes.windll.user32.CloseClipboard()
            return bool(has_data)
    except Exception:
        pass
    return False

class ClipboardManager:
    """
    Lớp quản lý tương tác với Bộ nhớ đệm (Clipboard) hệ thống.
    Chịu trách nhiệm giả lập tổ hợp phím để copy và lấy văn bản được bôi đen.
    """
    
    @staticmethod
    def get_selected_text(timeout: float = 0.5, dismiss_menu: bool = False) -> str:
        """
        Giả lập nhấn tổ hợp phím Ctrl + C để sao chép văn bản đang bôi đen và đọc nó.
        Sau khi đọc xong, khôi phục lại dữ liệu clipboard cũ của người dùng.
        
        Args:
            timeout (float): Thời gian tối đa (giây) chờ hệ điều hành nạp chữ vào clipboard.
            dismiss_menu (bool): Gửi phím ESC để đóng các menu đang mở (như Ribbon KeyTips của Word khi nhấn Alt).
            
        Returns:
            str: Văn bản bôi đen lấy được, hoặc chuỗi trống nếu không lấy được.
        """
        # 1. Sao lưu dữ liệu clipboard hiện có của người dùng
        # Sử dụng try-except phòng trường hợp clipboard đang bị ứng dụng khác khóa
        has_image_or_file_initially = is_clipboard_image_or_file()
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            old_clipboard = ""
        
        # 2. Xóa sạch clipboard tạm thời nếu ban đầu không chứa ảnh/file
        # (Để tránh ảnh hưởng tới tiến trình copy văn bản thuần túy)
        if not has_image_or_file_initially:
            try:
                pyperclip.copy("")
            except Exception:
                pass
        
        # 3. Chờ và giải phóng các phím bổ trợ đang bị đè bởi người dùng (nếu có)
        # Khi nhấn Alt+Z, ngón tay người dùng vẫn đang đè vật lý lên phím Alt.
        # Chúng ta sẽ chờ tối đa 300ms cho đến khi họ nhấc ngón tay ra khỏi phím Alt/Shift/Ctrl.
        VK_SHIFT = 0x10
        VK_CONTROL = 0x11
        VK_MENU = 0x12
        VK_ESCAPE = 0x1B
        VK_C = 0x43
        KEYEVENTF_KEYUP = 0x0002

        start_wait = time.time()
        while True:
            is_pressed = (
                (ctypes.windll.user32.GetAsyncKeyState(VK_SHIFT) & 0x8000 != 0) or
                (ctypes.windll.user32.GetAsyncKeyState(VK_CONTROL) & 0x8000 != 0) or
                (ctypes.windll.user32.GetAsyncKeyState(VK_MENU) & 0x8000 != 0)
            )
            if not is_pressed or (time.time() - start_wait >= 0.3):
                break
            time.sleep(0.01)
            
        # Giải phóng ảo thêm lần nữa cho chắc chắn
        ctypes.windll.user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
        ctypes.windll.user32.keybd_event(VK_SHIFT, 0, KEYEVENTF_KEYUP, 0)
        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.05)  # Chờ 50ms để Windows đồng bộ trạng thái phím
        
        # Gửi phím ESC để tắt trạng thái Ribbon KeyTips (gợi ý phím tắt menu) của MS Word nếu được yêu cầu.
        if dismiss_menu:
            ctypes.windll.user32.keybd_event(VK_ESCAPE, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_ESCAPE, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.05)
        
        # Mô phỏng hành động gõ phím Ctrl + C cấp hệ thống
        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_C, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_C, 0, KEYEVENTF_KEYUP, 0)
        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
        
        # 4. Vòng lặp chờ dữ liệu mới được nạp vào clipboard
        # Tăng timeout lên 0.5 giây để đảm bảo MS Word có đủ thời gian ghi dữ liệu vào clipboard
        start_time = time.time()
        selected_text = ""
        while time.time() - start_time < timeout:
            try:
                selected_text = pyperclip.paste().strip()
                if selected_text:
                    break
            except Exception:
                # Nếu clipboard bị khóa tạm thời bởi ứng dụng đích (như Word),
                # bỏ qua lỗi và thử lại ở lần lặp tiếp theo
                pass
            time.sleep(0.04)
            
        # 5. Khôi phục lại dữ liệu clipboard ban đầu của người dùng
        # Chỉ khôi phục nếu hiện tại lẫn ban đầu clipboard KHÔNG chứa hình ảnh hoặc file mới được tạo (như ảnh chụp màn hình)
        if not has_image_or_file_initially and not is_clipboard_image_or_file():
            try:
                pyperclip.copy(old_clipboard)
            except Exception:
                pass
            
        return selected_text if selected_text else ""
