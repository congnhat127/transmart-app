import time
import pyperclip
import keyboard

class ClipboardManager:
    """
    Lớp quản lý tương tác với Bộ nhớ đệm (Clipboard) hệ thống.
    Chịu trách nhiệm giả lập tổ hợp phím để copy và lấy văn bản được bôi đen.
    """
    
    @staticmethod
    def get_selected_text(timeout: float = 0.5) -> str:
        """
        Giả lập nhấn tổ hợp phím Ctrl + C để sao chép văn bản đang bôi đen và đọc nó.
        Sau khi đọc xong, khôi phục lại dữ liệu clipboard cũ của người dùng.
        
        Args:
            timeout (float): Thời gian tối đa (giây) chờ hệ điều hành nạp chữ vào clipboard.
            
        Returns:
            str: Văn bản bôi đen lấy được, hoặc chuỗi trống nếu không lấy được.
        """
        # 1. Sao lưu dữ liệu clipboard hiện có của người dùng
        # Sử dụng try-except phòng trường hợp clipboard đang bị ứng dụng khác khóa
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            old_clipboard = ""
        
        # 2. Xóa sạch clipboard tạm thời
        try:
            pyperclip.copy("")
        except Exception:
            pass
        
        # 3. Chờ và giải phóng các phím bổ trợ đang bị đè bởi người dùng (nếu có)
        # Khi nhấn Alt+Z, ngón tay người dùng vẫn đang đè vật lý lên phím Alt.
        # Chúng ta sẽ chờ tối đa 300ms cho đến khi họ nhấc ngón tay ra khỏi phím Alt/Shift/Ctrl.
        start_wait = time.time()
        while (keyboard.is_pressed("alt") or keyboard.is_pressed("ctrl") or keyboard.is_pressed("shift")) and (time.time() - start_wait < 0.3):
            time.sleep(0.01)
            
        # Giải phóng ảo thêm lần nữa cho chắc chắn
        keyboard.release("alt")
        keyboard.release("shift")
        keyboard.release("ctrl")
        time.sleep(0.05)  # Chờ 50ms để Windows đồng bộ trạng thái phím
        
        # Gửi phím ESC để tắt trạng thái Ribbon KeyTips (gợi ý phím tắt menu) của MS Word.
        # Khi nhấn tổ hợp phím chứa Alt, MS Word sẽ tự kích hoạt chế độ Menu Ribbon, 
        # chế độ này chặn các phím giả lập thông thường. Nhấn ESC sẽ đưa Word về trạng thái soạn thảo bình thường.
        keyboard.send("esc")
        time.sleep(0.05)
        
        # Mô phỏng hành động gõ phím Ctrl + C cấp hệ thống
        keyboard.send("ctrl+c")
        
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
        try:
            pyperclip.copy(old_clipboard)
        except Exception:
            pass
            
        return selected_text if selected_text else ""
