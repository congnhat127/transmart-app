import time
import pyperclip
import keyboard

class ClipboardManager:
    @staticmethod
    def get_selected_text(timeout: float = 0.25) -> str:
        """
        Giả lập tổ hợp phím Ctrl+C để lấy văn bản đang bôi đen trên bất kỳ ứng dụng nào.
        """
        # Lưu trữ nội dung clipboard hiện tại để khôi phục sau đó
        old_clipboard = pyperclip.paste()
        
        # Xóa clipboard tạm thời để theo dõi sự thay đổi
        pyperclip.copy("")
        
        # Mô phỏng nhấn Ctrl+C
        keyboard.send("ctrl+c")
        
        # Đợi văn bản được đưa vào clipboard
        start_time = time.time()
        selected_text = ""
        while time.time() - start_time < timeout:
            selected_text = pyperclip.paste().strip()
            if selected_text:
                break
            time.sleep(0.03)
        
        # Khôi phục lại dữ liệu clipboard ban đầu của người dùng để tránh ảnh hưởng trải nghiệm
        if not selected_text:
            pyperclip.copy(old_clipboard)
            return ""
        
        # Có thể khôi phục clipboard cũ sau một khoảng thời gian ngắn nếu muốn giữ clipboard sạch
        # Ở đây ta khôi phục lại clipboard cũ ngay lập tức sau khi đã lấy được text
        pyperclip.copy(old_clipboard)
        
        return selected_text
