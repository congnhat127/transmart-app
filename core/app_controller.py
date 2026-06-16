import os
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QCursor

from config.settings import settings_manager
from config.history_manager import history_manager
from core.listener import SystemListener
from ui.pop_icon import PopIconWidget
from ui.pop_translation import PopTranslationWidget
from ui.settings_window import SettingsWindow
from ui.history_window import HistoryWindow
from services.ai_service import AIService
from services.tts_service import TTSService

class TranslationThread(QThread):
    """Luồng phụ để thực hiện gọi API dịch thuật AI (tránh gây đơ/block GUI chính)."""
    translation_finished = pyqtSignal(str, dict)  # Phát ra: (văn bản gốc, dict kết quả)

    def __init__(self, ai_service: AIService, text: str, source_lang: str, target_lang: str):
        super().__init__()
        self.ai_service = ai_service
        self.text = text
        self.source_lang = source_lang
        self.target_lang = target_lang

    def run(self):
        result = self.ai_service.translate(self.text, self.source_lang, self.target_lang)
        self.translation_finished.emit(self.text, result)

class TransMartApp:
    """
    Controller chính của ứng dụng TransMart theo mô hình MVC.
    Chịu trách nhiệm kết nối bộ lắng nghe sự kiện, giao diện hiển thị và các dịch vụ xử lý.
    """
    def __init__(self):
        # 1. Đọc cấu hình người dùng
        self.settings = settings_manager.load_settings()
        self.theme = self.settings.get("theme", "dark")
        self.font_size = self.settings.get("font_size", 13)

        # 2. Khởi tạo các thành phần giao diện nổi (Views)
        self.pop_icon = PopIconWidget(theme=self.theme)
        self.pop_translation = PopTranslationWidget(theme=self.theme, font_size=self.font_size)
        
        # Khởi tạo các cửa sổ quản lý chính
        self.settings_window = SettingsWindow(theme=self.theme)
        self.history_window = HistoryWindow(theme=self.theme)

        # 3. Khởi tạo các dịch vụ nghiệp vụ (Services)
        self.ai_service = AIService()
        self.tts_service = TTSService()
        self.translation_thread = None

        # 4. Khởi tạo bộ lắng nghe sự kiện hệ thống (Hooks)
        self.listener = SystemListener()

        # 5. Kết nối các tín hiệu sự kiện (Signals & Slots)
        # - Lọc sự kiện từ listener
        self.listener.text_selected.connect(self.on_text_selected)
        self.listener.trigger_translation.connect(self.on_translation_triggered)
        self.listener.trigger_ocr.connect(self.on_ocr_triggered)
        self.listener.click_detected.connect(self.on_click_detected)

        # - Nút tròn dịch nhanh click ➔ Mở bảng dịch
        self.pop_icon.text_triggered.connect(
            lambda text: self.start_translation(text, self.pop_icon.x(), self.pop_icon.y())
        )
        
        # - Bảng dịch phát âm click ➔ Gọi TTS Service
        self.pop_translation.speak_triggered.connect(self.on_speak_triggered)
        
        # - Footer buttons click ➔ Mở các cửa sổ chức năng tương ứng
        self.pop_translation.history_triggered.connect(self.on_history_triggered)
        self.pop_translation.api_triggered.connect(self.on_api_triggered)
        self.pop_translation.settings_triggered.connect(self.on_settings_triggered)

        # - Đồng bộ cấu hình khi người dùng lưu cài đặt mới
        self.settings_window.settings_saved.connect(self.on_settings_saved)

    def start(self):
        """Khởi chạy bộ lắng nghe sự kiện hệ thống ngầm."""
        hotkey = self.settings.get("hotkey", "alt+z")
        ocr_hotkey = self.settings.get("ocr_hotkey", "alt+q")
        self.listener.start(hotkey=hotkey, ocr_hotkey=ocr_hotkey)

    def stop(self):
        """Dọn dẹp tài nguyên khi thoát ứng dụng."""
        self.listener.stop()
        self.pop_icon.close()
        self.pop_translation.close()
        self.settings_window.close()
        self.history_window.close()
        if self.translation_thread and self.translation_thread.isRunning():
            self.translation_thread.terminate()
            self.translation_thread.wait()

    def on_text_selected(self, text: str, x: int, y: int):
        """Hiển thị nút tròn dịch nhanh khi bôi đen thành công."""
        self.pop_translation.hide()
        
        screen = QApplication.primaryScreen()
        dpi_scale = screen.devicePixelRatio() if screen else 1.0
            
        logical_x = int(x / dpi_scale)
        logical_y = int(y / dpi_scale)
        
        self.pop_icon.show_at(text, logical_x, logical_y)

    def on_click_detected(self, x: int, y: int):
        """Ẩn các cửa sổ nổi nếu click ra ngoài phạm vi."""
        screen = QApplication.primaryScreen()
        dpi_scale = screen.devicePixelRatio() if screen else 1.0
        logical_x = int(x / dpi_scale)
        logical_y = int(y / dpi_scale)
        
        click_point = QPoint(logical_x, logical_y)
        
        # Ẩn nút tròn nếu nhấp chuột ra ngoài
        if self.pop_icon.isVisible():
            if not self.pop_icon.geometry().contains(click_point):
                self.pop_icon.hide()
                
        # Ẩn bảng dịch nếu click ra ngoài (chỉ ẩn khi không có cửa sổ phụ nào đang hiện)
        if self.pop_translation.isVisible():
            if not self.settings_window.isVisible() and not self.history_window.isVisible():
                if not self.pop_translation.geometry().contains(click_point):
                    self.pop_translation.hide()

    def on_translation_triggered(self, text: str):
        """Dịch trực tiếp khi nhấn Alt+Z."""
        self.pop_icon.hide()
        pos = QCursor.pos()
        self.start_translation(text, pos.x(), pos.y())

    def on_ocr_triggered(self):
        """Chụp ảnh màn hình OCR (Alt+Q)."""
        print("\n[OCR] Đã nhấn Alt+Q. (Tính năng OCR sẽ được tích hợp ở nhánh ocr-capture)")

    def start_translation(self, text: str, x: int = None, y: int = None):
        """Bắt đầu tiến trình dịch thuật bất đồng bộ."""
        if not text.strip():
            return

        if x is None or y is None:
            pos = QCursor.pos()
            x, y = pos.x(), pos.y()
            
        # Lấy ngôn ngữ nguồn và đích từ cài đặt
        source_lang = self.settings.get("source_lang", "Auto")
        target_lang = self.settings.get("target_lang", "Vietnamese")
        
        # Ánh xạ tên ngôn ngữ thân thiện từ hằng số hiển thị lên UI
        from config.constants import SUPPORTED_LANGUAGES
        ui_src = SUPPORTED_LANGUAGES.get(source_lang, source_lang)
        ui_tgt = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
        
        # 1. Hiển thị trạng thái Loading tức thời để tăng trải nghiệm người dùng
        self.pop_translation.show_loading(text, x, y, source_lang=ui_src, target_lang=ui_tgt)
        
        # 2. Hủy luồng dịch cũ nếu đang chạy trước đó
        if self.translation_thread and self.translation_thread.isRunning():
            self.translation_thread.terminate()
            self.translation_thread.wait()
            
        # 3. Tạo luồng dịch mới bất đồng bộ gọi API thực tế
        self.translation_thread = TranslationThread(self.ai_service, text, source_lang, target_lang)
        self.translation_thread.translation_finished.connect(self.on_translation_finished)
        self.translation_thread.start()

    def on_translation_finished(self, text: str, result: dict):
        """Hiển thị kết quả dịch và ghi nhận vào lịch sử dịch thuật."""
        # 1. Đổ kết quả vào bảng dịch nổi
        self.pop_translation.display_result(text, result)
        
        # 2. Lưu vào lịch sử dịch (tránh lưu nếu kết quả dịch báo lỗi chưa cấu hình hoặc lỗi kết nối)
        translation = result.get("translation", "")
        explanation = result.get("explanation", "")
        detected_lang = result.get("detected_lang", "unknown")
        
        if "Chưa cấu hình" not in translation and "đã xảy ra lỗi" not in translation.lower():
            history_manager.add_record(text, translation, explanation, detected_lang)
            # Tải lại danh sách lịch sử nếu cửa sổ lịch sử đang mở để cập nhật dữ liệu mới nhất
            if self.history_window.isVisible():
                self.history_window.load_history()

    def on_speak_triggered(self, text: str, lang: str):
        """Phát âm văn bản bằng dịch vụ Edge-TTS ngầm."""
        self.tts_service.speak(text, lang)

    def on_history_triggered(self):
        """Mở cửa sổ danh sách lịch sử dịch thuật."""
        self.history_window.theme = self.theme
        self.history_window._apply_style()
        self.history_window.load_history()
        self.history_window.show()
        self.history_window.raise_()
        self.history_window.activateWindow()

    def on_api_triggered(self):
        """Mở thẳng tab cấu hình API Key."""
        self.settings_window.theme = self.theme
        self.settings_window._apply_style()
        self.settings_window.load_values()
        self.settings_window.tabs.setCurrentIndex(1)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def on_settings_triggered(self):
        """Mở tab cấu hình cài đặt chung."""
        self.settings_window.theme = self.theme
        self.settings_window._apply_style()
        self.settings_window.load_values()
        self.settings_window.tabs.setCurrentIndex(0)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def on_settings_saved(self):
        """Đồng bộ hóa lại cấu hình ứng dụng sau khi lưu thành công từ Settings Window."""
        self.settings = settings_manager.load_settings()
        self.theme = self.settings.get("theme", "dark")
        self.font_size = self.settings.get("font_size", 13)
        
        # Cập nhật lại giao diện các cửa sổ nổi theo cấu hình mới
        self.pop_icon.update_theme(self.theme)
        self.pop_translation.update_theme(self.theme, self.font_size)
        
        # Khởi động lại Listener nếu người dùng đổi phím tắt hệ thống
        hotkey = self.settings.get("hotkey", "alt+z")
        ocr_hotkey = self.settings.get("ocr_hotkey", "alt+q")
        self.listener.stop()
        self.listener.start(hotkey=hotkey, ocr_hotkey=ocr_hotkey)
