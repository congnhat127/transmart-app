import time
from PyQt6.QtCore import QObject, pyqtSignal
from pynput import mouse
import keyboard

class SystemListener(QObject):
    # Tín hiệu khi bấm phím tắt dịch nhanh (Alt+D)
    hotkey_triggered = pyqtSignal()
    
    # Tín hiệu khi bấm phím tắt chụp ảnh màn hình dịch OCR (Alt+Q)
    ocr_hotkey_triggered = pyqtSignal()
    
    # Tín hiệu khi người dùng bôi đen văn bản bằng chuột: truyền vào (văn bản bôi đen, x, y)
    text_selected = pyqtSignal(str, int, int)

    def __init__(self, hotkey="alt+d", ocr_hotkey="alt+q", show_pop_icon=True):
        super().__init__()
        self.hotkey = hotkey
        self.ocr_hotkey = ocr_hotkey
        self.show_pop_icon = show_pop_icon
        
        self.keyboard_active = False
        self.mouse_listener = None
        
        # Lưu tọa độ khi bắt đầu nhấn chuột trái
        self.drag_start_pos = None
        self.is_dragging = False

    def start(self):
        """Khởi chạy các hook bàn phím và chuột toàn hệ thống."""
        self.start_keyboard_listening()
        if self.show_pop_icon:
            self.start_mouse_listening()

    def stop(self):
        """Gỡ cài đặt các hook toàn hệ thống."""
        self.stop_keyboard_listening()
        self.stop_mouse_listening()

    def start_keyboard_listening(self):
        if not self.keyboard_active:
            try:
                keyboard.add_hotkey(self.hotkey, self._on_hotkey)
                keyboard.add_hotkey(self.ocr_hotkey, self._on_ocr_hotkey)
                self.keyboard_active = True
            except Exception as e:
                print(f"[Listener] Không thể cài đặt phím tắt toàn cục: {e}")

    def stop_keyboard_listening(self):
        if self.keyboard_active:
            try:
                keyboard.unhook_all_hotkeys()
            except:
                pass
            self.keyboard_active = False

    def start_mouse_listening(self):
        if self.mouse_listener is None:
            self.mouse_listener = mouse.Listener(on_click=self._on_click)
            self.mouse_listener.start()

    def stop_mouse_listening(self):
        if self.mouse_listener is not None:
            self.mouse_listener.stop()
            self.mouse_listener = None

    def update_settings(self, hotkey: str, ocr_hotkey: str, show_pop_icon: bool):
        """Cập nhật nóng phím tắt và lắng nghe chuột."""
        self.stop()
        self.hotkey = hotkey
        self.ocr_hotkey = ocr_hotkey
        self.show_pop_icon = show_pop_icon
        self.start()

    def _on_hotkey(self):
        self.hotkey_triggered.emit()

    def _on_ocr_hotkey(self):
        self.ocr_hotkey_triggered.emit()

    def _on_click(self, x, y, button, pressed):
        """
        Lắng nghe nhấn chuột trái để nhận diện hành động kéo thả bôi đen văn bản.
        """
        if button == mouse.Button.left:
            if pressed:
                self.drag_start_pos = (x, y)
                self.is_dragging = False
            else:
                if self.drag_start_pos:
                    dx = abs(x - self.drag_start_pos[0])
                    dy = abs(y - self.drag_start_pos[1])
                    # Nếu kéo chuột quá 12 pixel, xem như người dùng bôi đen văn bản
                    if dx > 12 or dy > 12:
                        self.is_dragging = True
                    
                    if self.is_dragging:
                        # Tạo độ trễ nhỏ để tránh xung đột thao tác nhả chuột
                        time.sleep(0.08)
                        from core.clipboard_manager import ClipboardManager
                        text = ClipboardManager.get_selected_text()
                        if text and len(text.strip()) > 0:
                            # Phát tín hiệu mang theo text bôi đen và tọa độ chuột hiện tại
                            self.text_selected.emit(text, x, y)
                
                # Reset trạng thái
                self.drag_start_pos = None
                self.is_dragging = False
