import sys
import os
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QColor, QPainter

# Thêm đường dẫn thư mục gốc vào python path để tránh lỗi import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings_manager
from core.listener import SystemListener
from core.clipboard_manager import ClipboardManager
from core.ocr_engine import ScreenCaptureWidget
from ui.pop_icon import PopIconWidget
from ui.pop_translation import PopTranslationWidget
from ui.settings_window import SettingsWindow
class TranslationWorker(QThread):
    # Trả về kết quả dịch: (văn bản gốc, kết quả JSON)
    finished = pyqtSignal(str, dict)
    
    def __init__(self, text, source_lang, target_lang):
        super().__init__()
        self.text = text
        self.source_lang = source_lang
        self.target_lang = target_lang
        
    def run(self):
        from services.ai_service import ai_service
        result = ai_service.translate(self.text, self.source_lang, self.target_lang)
        self.finished.emit(self.text, result)


class OcrWorker(QThread):
    # Trả về kết quả dịch sau OCR: (văn bản nhận dạng, kết quả JSON)
    finished = pyqtSignal(str, dict)
    
    def __init__(self, pil_image, target_lang):
        super().__init__()
        self.pil_image = pil_image
        self.target_lang = target_lang
        
    def run(self):
        from core.ocr_engine import OcrEngine
        from services.ai_service import ai_service
        
        # 1. Thử nhận diện chữ cục bộ qua Windows OCR
        text = OcrEngine.extract_text(self.pil_image)
        if text and len(text.strip()) > 0:
            result = ai_service.translate(text, "Auto", self.target_lang)
            self.finished.emit(text, result)
        else:
            # 2. Dự phòng: Gửi ảnh cho Gemini Multimodal tự nhận dạng và dịch
            result = ai_service.translate_image(self.pil_image, self.target_lang)
            self.finished.emit("Hình ảnh đã chụp", result)


class TransMartApp:
    def __init__(self):
        # Khởi tạo các Widgets giao diện
        self.pop_icon = PopIconWidget()
        self.pop_translation = PopTranslationWidget()
        self.settings_window = SettingsWindow()
        self.capture_widget = None
        
        # Workers chạy ngầm
        self.trans_worker = None
        self.ocr_worker = None
        
        # Đăng ký listener hệ thống
        hotkey = settings_manager.get("hotkey", "alt+d")
        ocr_hotkey = settings_manager.get("ocr_hotkey", "alt+q")
        show_pop_icon = settings_manager.get("show_pop_icon", True)
        
        self.listener = SystemListener(hotkey, ocr_hotkey, show_pop_icon)
        self.listener.hotkey_triggered.connect(self._on_hotkey_triggered)
        self.listener.ocr_hotkey_triggered.connect(self._on_ocr_hotkey_triggered)
        self.listener.text_selected.connect(self._on_text_selected_by_mouse)
        
        # Kết nối tín hiệu của Pop Icon
        self.pop_icon.clicked_trigger.connect(self.start_translation)
        
        # Kết nối sự kiện lưu cấu hình từ Dashboard cài đặt
        self.settings_window.settings_saved.connect(self._on_settings_saved)
        
        # Tạo System Tray Icon
        self.setup_tray_icon()
        
        # Bắt đầu lắng nghe sự kiện hệ thống
        self.listener.start()

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon()
        
        # Vẽ một icon động hình vuông màu xanh dương có chữ 'T' màu trắng ở giữa làm logo
        pixmap = QPixmap(24, 24)
        pixmap.fill(QColor(Qt.GlobalColor.transparent))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Vẽ vòng tròn nền xanh dương
        painter.setBrush(QColor(0, 120, 212))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 24, 24)
        
        # Vẽ chữ 'T' màu trắng ở tâm
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPixelSize(14)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "T")
        painter.end()
        
        self.tray_icon.setIcon(QIcon(pixmap))
        self.tray_icon.setToolTip("TransMart - Dịch thuật thông minh")
        
        # Menu của System Tray
        tray_menu = QMenu()
        
        action_settings = tray_menu.addAction("Dashboard Cài đặt")
        action_settings.triggered.connect(self.show_settings)
        
        action_ocr = tray_menu.addAction("Chụp vùng màn hình dịch OCR")
        action_ocr.triggered.connect(self._on_ocr_hotkey_triggered)
        
        tray_menu.addSeparator()
        
        action_quit = tray_menu.addAction("Thoát ứng dụng")
        action_quit.triggered.connect(self.quit_app)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def show_settings(self):
        self.settings_window.load_values()
        self.settings_window.show()
        self.settings_window.activateWindow()

    def _on_settings_saved(self):
        """Cập nhật các listener và áp dụng giao diện mới ngay lập tức."""
        hotkey = settings_manager.get("hotkey", "alt+d")
        ocr_hotkey = settings_manager.get("ocr_hotkey", "alt+q")
        show_pop_icon = settings_manager.get("show_pop_icon", True)
        
        self.listener.update_settings(hotkey, ocr_hotkey, show_pop_icon)
        
        # Đóng popup cũ nếu đang mở để thay đổi theme đồng bộ
        self.pop_translation.close()

    def _on_hotkey_triggered(self):
        """Kích hoạt dịch nhanh bằng phím tắt."""
        text = ClipboardManager.get_selected_text()
        if text:
            self.start_translation(text)

    def _on_ocr_hotkey_triggered(self):
        """Kích hoạt giao diện chụp vùng màn hình để dịch OCR."""
        # Đóng các cửa sổ popup đang mở để tránh bị chụp đè vào ảnh nền
        self.pop_translation.close()
        self.pop_icon.hide()
        
        # Khởi tạo widget chụp màn hình mới
        self.capture_widget = ScreenCaptureWidget()
        self.capture_widget.screenshot_captured.connect(self.start_ocr_translation)
        self.capture_widget.show()

    def _on_text_selected_by_mouse(self, text, x, y):
        """Sự kiện khi bôi đen bằng chuột thành công."""
        self.pop_icon.show_at(text, x, y)

    def start_translation(self, text):
        """Gửi văn bản dịch qua AI chạy trên Thread phụ."""
        # Hiển thị popup dịch ở trạng thái Loading để phản hồi người dùng ngay lập tức
        self.pop_translation.lang_label.setText("Đang kết nối AI...")
        self.pop_translation.translation_browser.setHtml(f"<h3 style='color:#0078D4;'>Đang xử lý bản dịch...</h3><p style='color:gray;'>Gốc: {text}</p>")
        self.pop_translation.explanation_browser.setText("Đang phân tích...")
        self.pop_translation.examples_browser.setText("Đang tải ví dụ...")
        self.pop_translation.show()
        self.pop_translation.fade_in()
        
        src_lang = settings_manager.get("source_lang", "Auto")
        tgt_lang = settings_manager.get("target_lang", "Vietnamese")
        
        # Hủy worker cũ nếu đang chạy
        if self.trans_worker and self.trans_worker.isRunning():
            self.trans_worker.terminate()
            
        self.trans_worker = TranslationWorker(text, src_lang, tgt_lang)
        self.trans_worker.finished.connect(self._on_translation_finished)
        self.trans_worker.start()

    def _on_translation_finished(self, raw_text, result_dict):
        """Hiển thị kết quả dịch khi AI phản hồi."""
        self.pop_translation.display_result(raw_text, result_dict)

    def start_ocr_translation(self, pil_image):
        """Chạy OCR nhận diện và dịch hình ảnh trên thread phụ."""
        self.pop_translation.lang_label.setText("Đang quét ảnh...")
        self.pop_translation.translation_browser.setHtml("<h3 style='color:#0078D4;'>Đang xử lý hình ảnh chụp...</h3>")
        self.pop_translation.show()
        self.pop_translation.fade_in()
        
        tgt_lang = settings_manager.get("target_lang", "Vietnamese")
        
        if self.ocr_worker and self.ocr_worker.isRunning():
            self.ocr_worker.terminate()
            
        self.ocr_worker = OcrWorker(pil_image, tgt_lang)
        self.ocr_worker.finished.connect(self._on_translation_finished)
        self.ocr_worker.start()

    def quit_app(self):
        self.listener.stop()
        self.tray_icon.hide()
        QApplication.quit()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Không thoát ứng dụng khi tất cả các cửa sổ (như Settings) đóng lại
    # Để ứng dụng tiếp tục chạy ngầm trong System Tray
    app.setQuitOnLastWindowClosed(False)
    
    # Khởi tạo controller chính
    mart_app = TransMartApp()
    
    sys.exit(app.exec())
