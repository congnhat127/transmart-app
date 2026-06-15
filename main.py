import sys
import os
import signal
import time
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QCursor

# Thêm đường dẫn thư mục gốc vào python path để tránh lỗi import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings_manager
from core.listener import SystemListener
from ui.pop_icon import PopIconWidget
from ui.pop_translation import PopTranslationWidget
from ui.settings_window import SettingsWindow
from ui.history_window import HistoryWindow

class TransMartApp:
    """
    Controller chính của ứng dụng TransMart.
    Chịu trách nhiệm kết nối bộ lắng nghe phím/chuột ngầm với giao diện nổi (Floating UI).
    """
    def __init__(self):
        # 1. Đọc file cấu hình cài đặt của người dùng
        self.settings = settings_manager.load_settings()
        self.theme = self.settings.get("theme", "dark")
        self.font_size = self.settings.get("font_size", 13)

        # 2. Khởi tạo các thành phần giao diện nổi (Floating Widgets)
        self.pop_icon = PopIconWidget(theme=self.theme)
        self.pop_translation = PopTranslationWidget(theme=self.theme, font_size=self.font_size)
        
        # Khởi tạo các cửa sổ quản lý chính (chỉ hiển thị khi người dùng yêu cầu)
        self.settings_window = SettingsWindow(theme=self.theme)
        self.history_window = HistoryWindow(theme=self.theme)

        # 3. Khởi tạo bộ lắng nghe sự kiện hệ thống (Hooks)
        self.listener = SystemListener()

        # 4. Kết nối các tín hiệu sự kiện (Signals) tới các hàm xử lý tương ứng (Slots)
        # - Khi kéo chuột bôi đen xong ➔ Hiển thị nút dịch nhanh
        self.listener.text_selected.connect(self.on_text_selected)
        # - Khi bấm phím tắt Alt+Z ➔ Kích hoạt dịch trực tiếp không qua nút tròn
        self.listener.trigger_translation.connect(self.on_translation_triggered)
        # - Khi bấm phím tắt Alt+Q ➔ Kích hoạt màn hình chụp OCR
        self.listener.trigger_ocr.connect(self.on_ocr_triggered)
        # - Khi có cú click chuột thường ➔ Kiểm tra ẩn các widget nổi
        self.listener.click_detected.connect(self.on_click_detected)

        # - Khi click vào nút tròn dịch nhanh ➔ Mở bảng dịch tại đúng vị trí nút tròn đó
        self.pop_icon.text_triggered.connect(lambda text: self.start_translation(text, self.pop_icon.x(), self.pop_icon.y()))
        
        # - Khi click nút phát âm trong bảng dịch ➔ Gửi yêu cầu phát âm
        self.pop_translation.speak_triggered.connect(self.on_speak_triggered)
        
        # - Khi click các nút phụ (Lịch sử, API, Cài đặt) ➔ Chạy xử lý tương ứng
        self.pop_translation.history_triggered.connect(self.on_history_triggered)
        self.pop_translation.api_triggered.connect(self.on_api_triggered)
        self.pop_translation.settings_triggered.connect(self.on_settings_triggered)

    def start(self):
        """Khởi chạy bộ lắng nghe sự kiện ngầm."""
        hotkey = self.settings.get("hotkey", "alt+z")
        ocr_hotkey = self.settings.get("ocr_hotkey", "alt+q")
        self.listener.start(hotkey=hotkey, ocr_hotkey=ocr_hotkey)

    def stop(self):
        """Dọn dẹp và đóng toàn bộ tài nguyên."""
        self.listener.stop()
        self.pop_icon.close()
        self.pop_translation.close()

    def on_text_selected(self, text: str, x: int, y: int):
        """Xử lý khi bôi đen chữ bằng chuột thành công."""
        # Ẩn bảng dịch cũ đi (nếu đang mở)
        self.pop_translation.hide()
        
        # Chuyển đổi tọa độ vật lý (từ pynput) sang tọa độ logic (cho PyQt6) bằng Device Pixel Ratio
        screen = QApplication.primaryScreen()
        if screen:
            dpi_scale = screen.devicePixelRatio()
        else:
            dpi_scale = 1.0
            
        logical_x = int(x / dpi_scale)
        logical_y = int(y / dpi_scale)
        
        # Hiển thị nút tròn dịch nhanh ngay tại góc dưới bên phải vùng chọn
        self.pop_icon.show_at(text, logical_x, logical_y)

    def on_click_detected(self, x: int, y: int):
        """Xử lý khi phát hiện cú click chuột thường (để ẩn các popup nếu nhấp ra ngoài)."""
        screen = QApplication.primaryScreen()
        dpi_scale = screen.devicePixelRatio() if screen else 1.0
        logical_x = int(x / dpi_scale)
        logical_y = int(y / dpi_scale)
        
        from PyQt6.QtCore import QPoint
        click_point = QPoint(logical_x, logical_y)
        
        # 1. Ẩn nút tròn nếu click ra ngoài phạm vi nút tròn
        if self.pop_icon.isVisible():
            if not self.pop_icon.geometry().contains(click_point):
                self.pop_icon.hide()
                
        # 2. Ẩn bảng dịch nếu click ra ngoài phạm vi bảng dịch
        if self.pop_translation.isVisible():
            # Chỉ ẩn bảng dịch khi người dùng KHÔNG đang làm việc với các cửa sổ chức năng khác (Lịch sử, Cài đặt)
            if not self.settings_window.isVisible() and not self.history_window.isVisible():
                if not self.pop_translation.geometry().contains(click_point):
                    self.pop_translation.hide()

    def on_translation_triggered(self, text: str):
        """Xử lý khi phím tắt Alt+Z được nhấn."""
        # Ẩn nút tròn đi nếu đang hiện
        self.pop_icon.hide()
        # Lấy tọa độ chuột hiện tại để hiển thị bảng dịch
        pos = QCursor.pos()
        self.start_translation(text, pos.x(), pos.y())

    def on_ocr_triggered(self):
        """Xử lý khi phím tắt Alt+Q được nhấn."""
        print("\n[OCR] Đã nhấn Alt+Q. (Tính năng chụp ảnh màn hình và OCR sẽ được làm ở nhánh ocr-capture)")

    def start_translation(self, text: str, x: int = None, y: int = None):
        """Bắt đầu tiến trình dịch thuật."""
        # Nếu chưa có tọa độ (ví dụ click từ nút icon), lấy tọa độ chuột hiện tại
        if x is None or y is None:
            pos = QCursor.pos()
            x, y = pos.x(), pos.y()
            
        # 1. Hiển thị bảng dịch nổi ở trạng thái 'Loading...' ngay lập tức (Tối ưu hóa UX)
        self.pop_translation.show_loading(text, x, y, source_lang="Tự động", target_lang="Tiếng Việt")
        
        # 2. Giả lập độ trễ dịch AI 800ms để kiểm tra giao diện (Loading Spinner)
        # Ở các nhánh sau, chúng ta sẽ gọi API Gemini/OpenAI trong QThread ở đây.
        QTimer.singleShot(800, lambda: self.finish_mock_translation(text))

    def finish_mock_translation(self, text: str):
        """Đổ kết quả dịch giả lập vào giao diện sau khi dịch xong."""
        mock_result = {
            "translation": f"[DỊCH MOCK] Kết quả dịch của cụm: '{text}'",
            "explanation": "Đây là văn bản giải thích ngữ nghĩa giả lập từ AI.\nChức năng dịch thật kết nối API của Gemini và OpenAI sẽ được triển khai ở nhánh tiếp theo (feature/ai-tts-services).",
            "detected_lang": "en"
        }
        self.pop_translation.display_result(text, mock_result)

    def on_speak_triggered(self, text: str, lang: str):
        """Xử lý yêu cầu phát âm văn bản bằng Edge TTS."""
        print(f"\n[TTS] Yêu cầu đọc văn bản: '{text}' (Mã ngôn ngữ: {lang})")
        print("-> Tính năng phát âm Edge-TTS sẽ được tích hợp ở nhánh tiếp theo (feature/ai-tts-services)")

    def on_history_triggered(self):
        """Xử lý sự kiện mở Lịch sử dịch."""
        self.history_window.theme = self.theme
        self.history_window._apply_style()
        self.history_window.load_history()
        self.history_window.show()
        self.history_window.raise_()
        self.history_window.activateWindow()

    def on_api_triggered(self):
        """Xử lý sự kiện cấu hình API Key."""
        self.settings_window.theme = self.theme
        self.settings_window._apply_style()
        self.settings_window.load_values()
        self.settings_window.tabs.setCurrentIndex(1)  # Chuyển thẳng sang Tab Cấu hình API
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def on_settings_triggered(self):
        """Xử lý sự kiện mở Cài đặt hệ thống."""
        self.settings_window.theme = self.theme
        self.settings_window._apply_style()
        self.settings_window.load_values()
        self.settings_window.tabs.setCurrentIndex(0)  # Chuyển thẳng sang Tab Cài đặt chung
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

def sigint_handler(app_instance):
    """Hàm xử lý bắt phím tắt Ctrl+C để thoát ứng dụng."""
    def handler(*args):
        print("\n[Hệ thống] Nhận lệnh dừng (Ctrl+C). Đang dọn dẹp và thoát...")
        app_instance.stop()
        QApplication.quit()
    return handler

def main():
    # Ẩn các cảnh báo hệ thống font DirectWrite không cần thiết của Qt trên Windows
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false"
    
    # Khởi tạo ứng dụng PyQt6
    app = QApplication(sys.argv)
    
    # Đảm bảo ứng dụng chạy ngầm không tự động thoát khi ẩn các cửa sổ nổi
    app.setQuitOnLastWindowClosed(False)
    
    # Khởi tạo App Controller điều phối chung
    app_controller = TransMartApp()
    app_controller.start()

    # Thiết lập hệ thống bắt tín hiệu Ctrl+C từ terminal
    signal.signal(signal.SIGINT, sigint_handler(app_controller))
    
    # QTimer chạy tuần hoàn giúp Python thông dịch nhận tín hiệu Ctrl+C
    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    print("=== TransMart Floating UI Test ===")
    print("Ứng dụng đang chạy ẩn...")
    print("Vui lòng thử thực hiện:")
    print("1. Kéo chuột bôi đen chữ bất kỳ ở Chrome/Word ➔ Hiện nút tròn 🌐 ➔ Click để xem kết quả dịch nổi.")
    print("2. Bôi đen chữ bất kỳ rồi nhấn Alt + Z ➔ Bảng dịch nổi lên trực tiếp tại chuột.")
    print("3. Bấm thử nút 'Sao chép' hoặc 'Phát âm' trên bảng dịch nổi để kiểm tra.")
    print("Nhấn Ctrl + C tại Terminal này để dừng chương trình.")
    print("==================================")

    # Chạy vòng lặp sự kiện giao diện
    exit_code = app.exec()
    app_controller.stop()
    os._exit(exit_code)

if __name__ == "__main__":
    main()
