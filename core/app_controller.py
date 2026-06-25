import os
import sys
import time
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, QPoint, Qt
from PyQt6.QtGui import QCursor, QAction

from config.settings import settings_manager
from config.history_manager import history_manager
from core.listener import SystemListener
from ui.pop_icon import PopIconWidget
from ui.pop_translation import PopTranslationWidget
from ui.settings_window import SettingsWindow
from ui.history_window import HistoryWindow
from ui.styles import create_tray_icon
from services.ai_service import AIService
from services.tts_service import TTSService
from core.ocr_engine import ScreenCaptureWidget, qpixmap_to_pil

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

class OcrTranslationThread(QThread):
    """Luồng phụ để thực hiện nhận dạng và dịch ảnh (OCR) bất đồng bộ."""
    translation_finished = pyqtSignal(str, dict)  # Phát ra: (văn bản gốc OCR, dict kết quả)

    def __init__(self, ai_service: AIService, image, target_lang: str):
        super().__init__()
        self.ai_service = ai_service
        self.image = image
        self.target_lang = target_lang

    def run(self):
        result = self.ai_service.translate_image(self.image, self.target_lang)
        source_text = result.get("source_text", "Không nhận dạng được văn bản")
        self.translation_finished.emit(source_text, result)

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
        
        # - Bảng dịch thay đổi nội dung gốc ➔ Dịch lại bất đồng bộ
        self.pop_translation.translation_requested.connect(self.on_translation_requested)
        
        # - Footer buttons click ➔ Mở các cửa sổ chức năng tương ứng
        self.pop_translation.history_triggered.connect(self.on_history_triggered)
        self.pop_translation.api_triggered.connect(self.on_api_triggered)
        self.pop_translation.settings_triggered.connect(self.on_settings_triggered)

        # - Đồng bộ cấu hình khi người dùng lưu cài đặt mới
        self.settings_window.settings_saved.connect(self.on_settings_saved)

        # - Theo dõi trạng thái hoạt động của toàn bộ ứng dụng (lấy/mất focus khỏi hệ thống)
        self.last_active_window = None
        self.capture_widget = None
        QApplication.instance().focusChanged.connect(self.on_focus_changed)
        QApplication.instance().applicationStateChanged.connect(self.on_application_state_changed)

        # 6. Khởi tạo System Tray Icon (Biểu tượng khay hệ thống)
        self._init_tray_icon()

    def start(self):
        """Khởi chạy bộ lắng nghe sự kiện hệ thống ngầm."""
        hotkey = self.settings.get("hotkey", "alt+z")
        ocr_hotkey = self.settings.get("ocr_hotkey", "alt+q")
        self.listener.start(hotkey=hotkey, ocr_hotkey=ocr_hotkey)
        
        # Hiển thị bảng dịch trống ngay khi khởi động ứng dụng
        self.pop_translation.show_blank()

    def stop(self):
        """Dọn dẹp tài nguyên khi thoát ứng dụng."""
        self.listener.stop()
        self.pop_icon.close()
        self.pop_translation.close()
        self.settings_window.close()
        self.history_window.close()
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()
        if self.translation_thread and self.translation_thread.isRunning():
            self.translation_thread.terminate()
            self.translation_thread.wait()
        if hasattr(self, "tts_service") and self.tts_service:
            self.tts_service.stop()

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
        # Ẩn nút tròn nếu nhấp chuột ra ngoài
        if self.pop_icon.isVisible():
            click_point = QCursor.pos()
            if not self.pop_icon.frameGeometry().contains(click_point):
                self.pop_icon.hide()

    def on_translation_triggered(self, text: str):
        """Dịch trực tiếp khi nhấn Alt+Z."""
        self.pop_icon.hide()
        pos = QCursor.pos()
        self.start_translation(text, pos.x(), pos.y())

    def on_ocr_triggered(self):
        """Chụp ảnh màn hình OCR (Alt+Q)."""
        print("\n[OCR] Bắt đầu quét vùng màn hình để dịch...")
        # Ẩn các cửa sổ hiện tại của ứng dụng để tránh chụp đè lên hình chụp màn hình
        self.pop_icon.hide()
        self.pop_translation.hide()
        
        # Khởi tạo widget chụp màn hình nếu chưa có
        if not self.capture_widget:
            self.capture_widget = ScreenCaptureWidget()
            self.capture_widget.capture_finished.connect(self.on_ocr_capture_finished)
            
        self.capture_widget.start_capture()

    def on_ocr_capture_finished(self, pixmap, rect):
        """Xử lý sau khi người dùng quét xong vùng chọn trên màn hình."""
        # 1. Định vị vị trí hiển thị cho popup dịch
        # Hiển thị ở chính giữa bên dưới vùng quét
        x = rect.x() + (rect.width() - self.pop_translation.width()) // 2
        y = rect.y() + rect.height()
        
        # Đảm bảo tọa độ x và y nằm trong phạm vi màn hình khả dụng
        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.availableGeometry()
            # Tránh tràn lề trái/phải
            x = max(screen_geom.left() + 10, min(x, screen_geom.right() - self.pop_translation.width() - 10))
            # Tránh tràn lề dưới (nếu không đủ không gian phía dưới thì hiển thị ở phía trên vùng quét)
            if y + self.pop_translation.height() > screen_geom.bottom() - 10:
                y = max(screen_geom.top() + 10, rect.y() - self.pop_translation.height() - 10)
        
        # 2. Hiển thị popup dịch ở trạng thái Loading
        self.pop_translation.show_loading("Đang quét ảnh OCR...", x, y)
        self.last_active_window = self.pop_translation
        
        # 3. Chuyển QPixmap sang Pillow Image
        try:
            pil_img = qpixmap_to_pil(pixmap)
        except Exception as e:
            print(f"[OCR] Lỗi chuyển đổi ảnh: {e}")
            self.pop_translation.display_result(
                "Lỗi quét ảnh OCR",
                {
                    "translation": "Không thể xử lý định dạng ảnh chụp màn hình.",
                    "explanation": str(e),
                    "detected_lang": "unknown"
                },
                self.settings.get("target_lang", "Vietnamese")
            )
            return
            
        # 4. Hủy luồng dịch cũ nếu có
        if self.translation_thread and self.translation_thread.isRunning():
            self.translation_thread.terminate()
            self.translation_thread.wait()
            
        # 5. Khởi chạy luồng dịch OCR bất đồng bộ
        target_lang = self.settings.get("target_lang", "Vietnamese")
        self.translation_thread = OcrTranslationThread(self.ai_service, pil_img, target_lang)
        self.translation_thread.translation_finished.connect(self.on_translation_finished)
        self.translation_thread.start()

    def start_translation(self, text: str, x: int = None, y: int = None):
        """Bắt đầu tiến trình dịch thuật bất đồng bộ."""
        if not text.strip():
            return

        if x is None or y is None:
            pos = QCursor.pos()
            x, y = pos.x(), pos.y()
            
        # Lấy ngôn ngữ nguồn và đích từ cài đặt
        from config.settings import settings_manager
        self.settings = settings_manager.load_settings()
        source_lang = self.settings.get("source_lang", "Auto")
        target_lang = self.settings.get("target_lang", "Vietnamese")
        
        # 1. Hiển thị trạng thái Loading tức thời để tăng trải nghiệm người dùng (truyền key trực tiếp)
        self.pop_translation.show_loading(text, x, y, source_lang=source_lang, target_lang=target_lang)
        self.last_active_window = self.pop_translation
        
        # 1.5. Kiểm tra Cache cục bộ trước khi gọi AI để đạt tốc độ tức thời (0ms)
        provider = self.settings.get("provider", "gemini")
        cached_record = history_manager.find_cached_record(text, target_lang, provider)
        if cached_record:
            print(f"[DEBUG] Tìm thấy bản dịch trùng khớp trong Cache (0ms) cho: '{text[:20]}...'")
            self.display_translation_result(text, cached_record, save_to_history=False)
            return

        # 2. Hủy luồng dịch cũ nếu đang chạy trước đó
        if self.translation_thread and self.translation_thread.isRunning():
            self.translation_thread.terminate()
            self.translation_thread.wait()
            
        # 3. Tạo luồng dịch mới bất đồng bộ gọi API thực tế
        self.translation_thread = TranslationThread(self.ai_service, text, source_lang, target_lang)
        self.translation_thread.translation_finished.connect(self.on_translation_finished)
        self.translation_thread.start()

    def on_translation_finished(self, text: str, result: dict):
        """Callback khi luồng dịch thuật AI hoàn thành."""
        self.display_translation_result(text, result, save_to_history=True)

    def on_translation_requested(self, text: str):
        """Dịch lại khi người dùng sửa nội dung văn bản gốc trực tiếp trên popup."""
        if not text.strip():
            return
            
        from config.settings import settings_manager
        self.settings = settings_manager.load_settings()
        source_lang = self.settings.get("source_lang", "Auto")
        target_lang = self.settings.get("target_lang", "Vietnamese")
        
        # Chỉ hiển thị trạng thái loading cho ô dịch, không thay đổi ô nhập gốc
        self.pop_translation.show_translation_loading()
        
        # Kiểm tra Cache cục bộ
        provider = self.settings.get("provider", "gemini")
        cached_record = history_manager.find_cached_record(text, target_lang, provider)
        if cached_record:
            print(f"[DEBUG] Tìm thấy bản dịch trùng khớp trong Cache (0ms) cho văn bản sửa: '{text[:20]}...'")
            self.display_translation_result(text, cached_record, save_to_history=False)
            return
            
        # Hủy luồng dịch cũ nếu có
        if self.translation_thread and self.translation_thread.isRunning():
            self.translation_thread.terminate()
            self.translation_thread.wait()
            
        # Tạo luồng dịch mới
        self.translation_thread = TranslationThread(self.ai_service, text, source_lang, target_lang)
        self.translation_thread.translation_finished.connect(self.on_translation_finished)
        self.translation_thread.start()

    def display_translation_result(self, text: str, result: dict, save_to_history: bool = True):
        """Hiển thị kết quả dịch lên popup và ghi vào lịch sử nếu cần."""
        # 1. Đổ kết quả vào bảng dịch nổi
        from config.settings import settings_manager
        self.settings = settings_manager.load_settings()
        target_lang = self.settings.get("target_lang", "Vietnamese")
        self.pop_translation.display_result(text, result, target_lang)
        
        if not save_to_history:
            return
            
        # 2. Lưu vào lịch sử dịch (tránh lưu nếu kết quả dịch báo lỗi chưa cấu hình hoặc lỗi kết nối)
        translation = result.get("translation", "")
        explanation = result.get("explanation", "")
        summary = result.get("summary", "")
        detected_lang = result.get("detected_lang", "unknown")
        target_lang = self.settings.get("target_lang", "Vietnamese")
        
        if "Chưa cấu hình" not in translation and "đã xảy ra lỗi" not in translation.lower():
            provider = self.settings.get("provider", "gemini")
            history_manager.add_record(text, translation, explanation, detected_lang, target_lang, summary, provider)
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
        self.history_window.last_shown_time = time.time()
        self.last_active_window = self.history_window
        if self.history_window.isMinimized():
            self.history_window.showNormal()
        else:
            self.history_window.show()
        self.history_window.raise_()
        self.history_window.activateWindow()

    def on_api_triggered(self):
        """Mở thẳng tab cấu hình API Key."""
        self.settings_window.theme = self.theme
        self.settings_window._apply_style()
        self.settings_window.load_values()
        self.settings_window.tabs.setCurrentIndex(1)
        self.settings_window.last_shown_time = time.time()
        self.last_active_window = self.settings_window
        if self.settings_window.isMinimized():
            self.settings_window.showNormal()
        else:
            self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def on_settings_triggered(self):
        """Mở tab cấu hình cài đặt chung."""
        self.settings_window.theme = self.theme
        self.settings_window._apply_style()
        self.settings_window.load_values()
        self.settings_window.tabs.setCurrentIndex(0)
        self.settings_window.last_shown_time = time.time()
        self.last_active_window = self.settings_window
        if self.settings_window.isMinimized():
            self.settings_window.showNormal()
        else:
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

    def _init_tray_icon(self):
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(create_tray_icon())
        self.tray_icon.setToolTip("TransMart - Dịch thuật thông minh")
        
        # Tạo menu chuột phải cho khay hệ thống
        tray_menu = QMenu()
        
        action_settings = QAction("⚙️ Cài đặt", self.settings_window)
        action_settings.triggered.connect(self.on_settings_triggered)
        tray_menu.addAction(action_settings)
        
        action_history = QAction("📋 Lịch sử dịch", self.history_window)
        action_history.triggered.connect(self.on_history_triggered)
        tray_menu.addAction(action_history)
        
        tray_menu.addSeparator()
        
        action_exit = QAction("❌ Thoát ứng dụng", self.settings_window)
        action_exit.triggered.connect(self.exit_app)
        tray_menu.addAction(action_exit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Click hoặc Double click vào tray icon ➔ Mở cài đặt
        self.tray_icon.activated.connect(self.on_tray_activated)

    def on_tray_activated(self, reason):
        if reason in (QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick):
            self.on_settings_triggered()

    def exit_app(self):
        print("\n[Hệ thống] Thoát ứng dụng từ Khay hệ thống...")
        self.stop()
        QApplication.quit()
        sys.exit(0)

    def on_focus_changed(self, old, now):
        """Theo dõi cửa sổ hoạt động cuối cùng của ứng dụng."""
        active = QApplication.activeWindow()
        if active in (self.pop_translation, self.settings_window, self.history_window):
            self.last_active_window = active

    def on_application_state_changed(self, state):
        """Xử lý sự kiện khi toàn bộ ứng dụng mất focus (người dùng click ra ứng dụng khác hoặc Desktop)."""
        print(f"[DEBUG] on_application_state_changed: state={state}")
        if state == Qt.ApplicationState.ApplicationInactive:
            # Bỏ qua nếu người dùng đang nhấn giữ chuột (ví dụ: đang kéo cửa sổ hoặc click tương tác)
            if QApplication.mouseButtons() & Qt.MouseButton.LeftButton:
                print("[DEBUG] Ignore because Left Mouse Button is pressed")
                return

            import time
            now = time.time()
            cursor_pos = QCursor.pos()
            
            # Kiểm tra xem con trỏ chuột có đang nằm trên bất kỳ cửa sổ nào của ứng dụng hay không
            # (bao gồm cả pop_icon vừa ẩn cách đây dưới 1.5 giây)
            pop_icon_hidden_diff = now - getattr(self.pop_icon, "last_hidden_time", 0.0)
            
            is_inside = False
            # 1. Kiểm tra pop_icon
            if (self.pop_icon.isVisible() or pop_icon_hidden_diff < 1.5) and self.pop_icon.frameGeometry().contains(cursor_pos):
                is_inside = True
            # 2. Kiểm tra pop_translation
            elif self.pop_translation.isVisible() and self.pop_translation.frameGeometry().contains(cursor_pos):
                is_inside = True
            # 3. Kiểm tra settings_window
            elif self.settings_window.isVisible() and self.settings_window.frameGeometry().contains(cursor_pos):
                is_inside = True
            # 4. Kiểm tra history_window
            elif self.history_window.isVisible() and self.history_window.frameGeometry().contains(cursor_pos):
                is_inside = True

            if is_inside:
                print("[DEBUG] Ignore focus loss because cursor is over one of the application windows")
                return

            # Nếu nút tròn dịch nhanh vừa ẩn trong vòng 1.5 giây, bỏ qua sự kiện mất focus này
            # (vì đây là tiến trình chuyển tiếp tự nhiên từ nút tròn sang bảng dịch)
            if pop_icon_hidden_diff < 1.5:
                print(f"[DEBUG] Ignore focus loss because pop_icon was hidden recently ({pop_icon_hidden_diff:.3f}s)")
                return

            # Nếu có bất kỳ cửa sổ nào vừa mới được mở/khôi phục trong vòng 1.5 giây, bỏ qua
            pop_shown_diff = now - getattr(self.pop_translation, "last_shown_time", 0.0)
            settings_shown_diff = now - getattr(self.settings_window, "last_shown_time", 0.0)
            history_shown_diff = now - getattr(self.history_window, "last_shown_time", 0.0)
            if pop_shown_diff < 1.5 or settings_shown_diff < 1.5 or history_shown_diff < 1.5:
                print(f"[DEBUG] Ignore focus loss because a window was shown recently (pop: {pop_shown_diff:.3f}s, settings: {settings_shown_diff:.3f}s, history: {history_shown_diff:.3f}s)")
                return

            # Thu nhỏ tất cả các cửa sổ đang hiển thị xuống thanh Taskbar (do nhấp ra ngoài ứng dụng hoặc Alt+Tab)
            if self.pop_translation.isVisible() and not self.pop_translation.isMinimized():
                is_playing = False
                if hasattr(self, "tts_service") and self.tts_service:
                    try:
                        if self.tts_service.player.playbackState().name == "PlayingState":
                            is_playing = True
                    except Exception:
                        pass
                
                if is_playing:
                    print("[DEBUG] Skip minimizing pop_translation because TTS is playing")
                else:
                    print("[DEBUG] Minimizing pop_translation")
                    self.pop_translation.showMinimized()
            if self.settings_window.isVisible() and not self.settings_window.isMinimized():
                print("[DEBUG] Minimizing settings_window")
                self.settings_window.save_values(close_window=False)
                self.settings_window.showMinimized()
            if self.history_window.isVisible() and not self.history_window.isMinimized():
                print("[DEBUG] Minimizing history_window")
                self.history_window.showMinimized()
