import time
# pyrefly: ignore [missing-import]
from PyQt6.QtCore import QObject, pyqtSignal
import keyboard
import pynput

from core.clipboard_manager import ClipboardManager

class SystemListener(QObject):
    """
    Lớp lắng nghe sự kiện Hệ thống (Bàn phím và Chuột).
    Kế thừa từ QObject để sử dụng hệ thống Signal (Tín hiệu) của PyQt6,
    giúp truyền sự kiện từ luồng chạy ngầm sang giao diện chính (UI Thread) một cách an toàn.
    """
    # Định nghĩa các tín hiệu để giao diện chính (main.py) kết nối và xử lý:
    # 1. Phát ra văn bản cần dịch trực tiếp khi ấn phím tắt Alt+D
    trigger_translation = pyqtSignal(str)
    # 2. Phát ra sự kiện yêu cầu mở vùng chụp màn hình để dịch OCR khi ấn Alt+Q
    trigger_ocr = pyqtSignal()
    # 3. Phát ra khi người dùng vừa bôi đen xong văn bản bằng chuột: (văn bản bôi đen, tọa độ x, tọa độ y)
    text_selected = pyqtSignal(str, int, int)

    def __init__(self):
        super().__init__()
        # Trạng thái theo dõi chuột
        self.is_left_pressed = False      # Lưu trạng thái chuột trái có đang đè xuống không
        self.drag_start_pos = None        # Tọa độ (x, y) lúc bắt đầu nhấn chuột trái
        self.mouse_listener = None        # Bộ lắng nghe sự kiện chuột
        
        # Ngưỡng khoảng cách tối thiểu (pixel) để coi là một hành động kéo bôi đen
        # Nhấp chuột thông thường (click) thường dịch chuyển từ 0-5px. 
        # Chúng ta đặt 12px để chắc chắn người dùng đang kéo bôi đen chữ.
        self.drag_threshold = 12 

    def start(self, hotkey: str = "alt+z", ocr_hotkey: str = "alt+q"):
        """Khởi chạy bộ lắng nghe phím tắt và chuột."""
        try:
            # 1. Đăng ký phím tắt hệ thống bằng thư viện `keyboard`
            # Lệnh này sẽ chạy ngầm để bắt phím kể cả khi app đang ẩn
            keyboard.add_hotkey(hotkey, self._on_translate_hotkey)
            keyboard.add_hotkey(ocr_hotkey, self._on_ocr_hotkey)
            
            # 2. Đăng ký lắng nghe chuột bằng `pynput.mouse`
            # Khởi chạy một luồng daemon chạy ngầm để lắng nghe
            self.mouse_listener = pynput.mouse.Listener(on_click=self._on_click)
            self.mouse_listener.start()
            
            print(f"[Listener] Đang lắng nghe phím tắt ({hotkey}, {ocr_hotkey}) và sự kiện chuột...")
        except Exception as e:
            print(f"[Listener] Lỗi khởi động bộ lắng nghe: {e}")

    def stop(self):
        """Dừng tất cả bộ lắng nghe và giải phóng tài nguyên."""
        try:
            # Hủy đăng ký tất cả phím tắt
            keyboard.unhook_all()
            
            # Dừng lắng nghe chuột
            if self.mouse_listener:
                self.mouse_listener.stop()
                
            print("[Listener] Đã dừng bộ lắng nghe hệ thống.")
        except Exception as e:
            print(f"[Listener] Lỗi khi dừng bộ lắng nghe: {e}")

    def _on_translate_hotkey(self):
        """Hàm callback được gọi khi phím tắt Alt+Z được nhấn."""
        print("\n[DEBUG] Bộ lắng nghe đã bắt được phím tắt Alt+Z!")
        text = ClipboardManager.get_selected_text()
        print(f"[DEBUG] Văn bản bôi đen lấy được từ clipboard: '{text}'")
        if text:
            # Nếu có chữ, phát tín hiệu yêu cầu dịch thẳng
            self.trigger_translation.emit(text)
        else:
            print("[DEBUG] Không lấy được văn bản bôi đen nào (hoặc chuỗi rỗng).")

    def _on_ocr_hotkey(self):
        """Hàm callback được gọi khi phím tắt Alt+Q được nhấn."""
        # Phát tín hiệu yêu cầu mở màn hình chụp ảnh OCR
        self.trigger_ocr.emit()

    def _on_click(self, x, y, button, pressed):
        """
        Hàm callback xử lý sự kiện click chuột.
        Được gọi mỗi khi người dùng click chuột xuống hoặc nhả chuột ra.
        """
        # Chúng ta chỉ quan tâm tới chuột trái (chuột dùng để bôi đen chữ)
        if button == pynput.mouse.Button.left:
            if pressed:
                # Chuột trái được nhấn xuống: Ghi lại trạng thái và tọa độ bắt đầu
                self.is_left_pressed = True
                self.drag_start_pos = (x, y)
            else:
                # Chuột trái được nhả ra: Tính toán khoảng cách kéo
                self.is_left_pressed = False
                if self.drag_start_pos:
                    start_x, start_y = self.drag_start_pos
                    # Công thức tính khoảng cách dịch chuyển (d = sqrt(dx^2 + dy^2))
                    distance = ((x - start_x) ** 2 + (y - start_y) ** 2) ** 0.5
                    
                    # Nếu khoảng cách kéo lớn hơn ngưỡng quy định (người dùng vừa bôi đen xong)
                    if distance > self.drag_threshold:
                        # Chờ khoảng 80ms để hệ thống hoàn tất việc cập nhật vùng chọn bôi đen trên màn hình
                        time.sleep(0.08)
                        
                        # Gọi ClipboardManager lấy chữ bôi đen
                        text = ClipboardManager.get_selected_text()
                        if text:
                            # Phát tín hiệu bôi đen kèm theo tọa độ nhả chuột (x, y) 
                            # Tọa độ này sẽ dùng để hiển thị nút dịch nhanh ngay dưới con trỏ chuột
                            self.text_selected.emit(text, x, y)
                            
                # Reset vị trí bắt đầu kéo về None để chuẩn bị cho lượt kéo sau
                self.drag_start_pos = None
