# ui/pop_translation.py
import time
import pyperclip
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer, QEvent
from PyQt6.QtGui import QMouseEvent, QFont, QCursor

from ui.styles import get_translation_popup_style, create_tray_icon

class PopTranslationWidget(QWidget):
    """
    Hộp thoại dịch nổi Glassmorphism thông minh hiển thị kết quả dịch,
    giải thích ngữ pháp và hỗ trợ copy nhanh, phát âm (TTS).
    """
    # Tín hiệu yêu cầu phát âm văn bản: (văn bản cần đọc, mã ngôn ngữ)
    speak_triggered = pyqtSignal(str, str)
    
    # Tín hiệu mở các cửa sổ chức năng
    history_triggered = pyqtSignal()
    api_triggered = pyqtSignal()
    settings_triggered = pyqtSignal()
    
    # Tín hiệu yêu cầu dịch lại văn bản mới chỉnh sửa
    translation_requested = pyqtSignal(str)

    def __init__(self, theme: str = "dark", font_size: int = 13):
        super().__init__()
        self.theme = theme
        self.font_size = font_size
        self.is_updating_programmatically = False
        
        # Thiết lập timer debounce 800ms để tự động dịch khi người dùng dừng gõ
        self.debounce_timer = QTimer(self)
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self._on_debounce_timeout)
        
        # Biến phục vụ di chuyển cửa sổ (Window Dragging)
        self.drag_position = None
        self.target_lang_code = "vi" # Mặc định ngôn ngữ đích là tiếng Việt
        self.source_lang_code = "en" # Mặc định ngôn ngữ nguồn là tiếng Anh
        self.source_text = ""
        self.translation_text = ""
        self.last_move_resize_time = 0.0
        
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowCloseButtonHint | 
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowTitle("TransMart - Dịch nhanh")
        self.setWindowIcon(create_tray_icon())
        
        # 2. Xây dựng giao diện
        self._init_ui()
        self.setStyleSheet(get_translation_popup_style(self.theme, self.font_size))
        
        # Đặt kích thước mặc định cho hộp thoại
        self.setFixedSize(380, 320)

    def _init_ui(self):
        """Khởi tạo bố cục và các widget bên trong."""
        # Layout chính của QWidget (chứa lề ngoài để tránh bo góc bị cắt)
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(6, 6, 6, 6)
        
        # Card chứa toàn bộ giao diện (dùng để vẽ nền Glassmorphism bằng CSS)
        self.card = QWidget()
        self.card.setObjectName("PopupCard")
        card_layout = QVBoxLayout(self.card)
        card_layout.setContentsMargins(12, 12, 12, 12)
        card_layout.setSpacing(8)
        
        # --- HEADER LAYOUT (Tiêu đề ngôn ngữ) ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        
        self.lang_label = QLabel("ĐANG DỊCH...")
        self.lang_label.setObjectName("LangLabel")
        
        header_layout.addWidget(self.lang_label)
        header_layout.addStretch()
        
        # --- BODY LAYOUT (Văn bản gốc & Văn bản dịch) ---
        # Ô chứa văn bản gốc (Nhỏ hơn)
        self.source_text_edit = QTextEdit()
        self.source_text_edit.setReadOnly(False)
        self.source_text_edit.setPlaceholderText("Nhập hoặc chỉnh sửa văn bản gốc...")
        self.source_text_edit.setMaximumHeight(70)
        self.source_text_edit.installEventFilter(self)
        self.source_text_edit.textChanged.connect(self._on_source_text_changed)
        
        # Ô chứa văn bản dịch + giải thích (Rộng hơn)
        self.target_text_edit = QTextEdit()
        self.target_text_edit.setReadOnly(True)
        self.target_text_edit.setPlaceholderText("Kết quả dịch...")
        
        # --- FOOTER LAYOUT (Copy, TTS & Thương hiệu) ---
        self.footer_frame = QFrame()
        self.footer_frame.setObjectName("FooterFrame")
        footer_layout = QHBoxLayout(self.footer_frame)
        footer_layout.setContentsMargins(0, 8, 0, 0)
        footer_layout.setSpacing(8)
        
        # Nút Copy nhanh
        self.copy_btn = QPushButton("📋 Sao chép")
        self.copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.copy_btn.clicked.connect(self._on_copy_clicked)
        
        # Nút Phát âm Bản gốc (TTS Source)
        self.tts_src_btn = QPushButton("🔊 Đọc gốc")
        self.tts_src_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tts_src_btn.clicked.connect(self._on_tts_src_clicked)
        
        # Nút Phát âm Bản dịch (TTS Target)
        self.tts_btn = QPushButton("🔊 Đọc dịch")
        self.tts_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.tts_btn.clicked.connect(self._on_tts_clicked)
        
        # Nút Lịch sử (History)
        self.history_btn = QPushButton()
        self.history_btn.setObjectName("HistoryBtn")
        self.history_btn.setFont(QFont("Segoe MDL2 Assets", 10))
        self.history_btn.setText("\uE81C") # Biểu tượng Lịch sử (Recent/Clock)
        self.history_btn.setFixedSize(28, 28)
        self.history_btn.setToolTip("Lịch sử dịch")
        self.history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.history_btn.clicked.connect(self._on_history_clicked)
        
        # Nút API Key
        self.api_btn = QPushButton()
        self.api_btn.setObjectName("ApiBtn")
        self.api_btn.setFont(QFont("Segoe MDL2 Assets", 10))
        self.api_btn.setText("\uE8D7") # Biểu tượng Chìa khóa (API Key/Credentials)
        self.api_btn.setFixedSize(28, 28)
        self.api_btn.setToolTip("Cấu hình API Key")
        self.api_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.api_btn.clicked.connect(self._on_api_clicked)
        
        # Nút Cài đặt (Settings)
        self.settings_btn = QPushButton()
        self.settings_btn.setObjectName("SettingsBtn")
        self.settings_btn.setFont(QFont("Segoe MDL2 Assets", 10))
        self.settings_btn.setText("\uE713") # Biểu tượng Bánh răng (Settings)
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.setToolTip("Cài đặt hệ thống")
        self.settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.settings_btn.clicked.connect(self._on_settings_clicked)
        
        # Mác ứng dụng ở góc phải
        brand_label = QLabel("TransMart")
        brand_label.setStyleSheet("color: rgba(128, 128, 128, 0.6); font-size: 10px; font-weight: bold;")
        
        footer_layout.addWidget(self.copy_btn)
        footer_layout.addWidget(self.tts_src_btn)
        footer_layout.addWidget(self.tts_btn)
        footer_layout.addWidget(self.history_btn)
        footer_layout.addWidget(self.api_btn)
        footer_layout.addWidget(self.settings_btn)
        footer_layout.addStretch()
        footer_layout.addWidget(brand_label)
        
        # Thêm các thành phần vào Card chính
        card_layout.addLayout(header_layout)
        card_layout.addWidget(self.source_text_edit)
        card_layout.addWidget(self.target_text_edit)
        card_layout.addWidget(self.footer_frame)
        
        # Thêm Card chính vào Layout của Widget
        main_layout.addWidget(self.card)

    def show_loading(self, raw_text: str, x: int, y: int, source_lang: str = "Tự động", target_lang: str = "Tiếng Việt"):
        """
        Hiển thị hộp thoại ngay lập tức tại vị trí chuột ở trạng thái 'Đang dịch'.
        Giúp tăng trải nghiệm UX, người dùng biết app đang xử lý, không bị cảm giác đơ click.
        """
        self.is_updating_programmatically = True
        self.source_text_edit.setPlainText(raw_text)
        self.is_updating_programmatically = False
        self.target_text_edit.setPlainText("Đang dịch bằng AI, vui lòng chờ trong giây lát...")
        self.lang_label.setText(f"{source_lang.upper()} ➜ {target_lang.upper()}")
        
        # Di chuyển hộp thoại đến vị trí chuột (lệch xuống dưới 20px)
        self.move(x + 10, y + 20)
        self.last_shown_time = time.time()
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        
        # Đưa con trỏ chuột ra ngoài để người dùng có thể đọc ngay
        self.raise_()
        self.activateWindow()

    def display_result(self, raw_text: str, result_dict: dict, target_lang: str = "Vietnamese"):
        """
        Đổ kết quả dịch thuật chi tiết từ AI vào hộp thoại.
        
        Args:
            raw_text (str): Văn bản gốc.
            result_dict (dict): Từ điển kết quả dịch có cấu trúc từ AI.
                                 Ví dụ: {"translation": "...", "explanation": "..."}
            target_lang (str): Tên ngôn ngữ đích cài đặt.
        """
        self.source_text = raw_text
        self.is_updating_programmatically = True
        self.source_text_edit.setPlainText(raw_text)
        self.is_updating_programmatically = False
        
        translation = result_dict.get("translation", "")
        self.translation_text = translation
        explanation = result_dict.get("explanation", "")
        summary = result_dict.get("summary", "")
        detected_lang = result_dict.get("detected_lang", "")
        
        # Ánh xạ ngôn ngữ đích sang mã ngôn ngữ
        lang_to_code = {
            "Vietnamese": "vi",
            "English": "en",
            "Japanese": "ja",
            "Korean": "ko",
            "Chinese": "zh",
            "French": "fr",
            "German": "de",
            "Spanish": "es",
            "Russian": "ru"
        }
        self.target_lang_code = lang_to_code.get(target_lang, "vi")
        self.source_lang_code = detected_lang.lower() if detected_lang else "en"
        
        # Get target language friendly name
        from config.constants import SUPPORTED_LANGUAGES
        target_lang_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang).upper()
        
        # Cập nhật tiêu đề ngôn ngữ
        if detected_lang:
            self.lang_label.setText(f"{detected_lang.upper()} ➜ {target_lang_name}")
        else:
            self.lang_label.setText(f"AI ➜ {target_lang_name}")
            
        # Định dạng văn bản hiển thị đẹp mắt
        display_html = f"<b>Bản dịch:</b><br>{translation}"
        if summary:
            display_html += f"<br><br><b>Tóm tắt chính:</b><br>{summary}"
        if explanation:
            display_html += f"<br><br><b>Giải thích chi tiết:</b><br>{explanation.replace(chr(10), '<br>')}"
            
        self.target_text_edit.setHtml(display_html)

    def update_theme(self, new_theme: str, new_font_size: int):
        """Cập nhật font chữ và giao diện màu sắc."""
        self.theme = new_theme
        self.font_size = new_font_size
        self.setStyleSheet(get_translation_popup_style(self.theme, self.font_size))

    def _on_copy_clicked(self):
        """Xử lý sự kiện sao chép bản dịch."""
        # Lấy nội dung text thuần từ ô kết quả dịch
        translated_text = self.target_text_edit.toPlainText()
        # Nếu có chữ giải thích chi tiết, ta chỉ lấy phần bản dịch chính (trước dòng Giải thích)
        if "Bản dịch:" in translated_text:
            translated_text = translated_text.split("Bản dịch:\n")[-1]
        if "Giải thích chi tiết:" in translated_text:
            translated_text = translated_text.split("\n\nGiải thích chi tiết:")[0]
            
        pyperclip.copy(translated_text.strip())
        self.copy_btn.setText("✓ Đã sao chép")
        # Khôi phục chữ 'Sao chép' sau 1.5 giây
        QTimer.singleShot(1500, lambda: self.copy_btn.setText("📋 Sao chép"))

    def _on_tts_clicked(self):
        """Xử lý phát âm văn bản dịch."""
        if hasattr(self, "translation_text") and self.translation_text:
            self.speak_triggered.emit(self.translation_text.strip(), self.target_lang_code)

    def _on_tts_src_clicked(self):
        """Xử lý phát âm văn bản gốc."""
        if hasattr(self, "source_text") and self.source_text:
            self.speak_triggered.emit(self.source_text.strip(), self.source_lang_code)

    def _on_history_clicked(self):
        """Xử lý sự kiện click nút Lịch sử dịch."""
        self.history_triggered.emit()

    def _on_api_clicked(self):
        """Xử lý sự kiện click nút Cấu hình API Key."""
        self.api_triggered.emit()

    def _on_settings_clicked(self):
        """Xử lý sự kiện click nút Cài đặt."""
        self.settings_triggered.emit()

    def moveEvent(self, event):
        self.last_move_resize_time = time.time()
        super().moveEvent(event)

    def resizeEvent(self, event):
        self.last_move_resize_time = time.time()
        super().resizeEvent(event)

    def changeEvent(self, event):
        """Ẩn bảng dịch nếu click ra ngoài ứng dụng (mất focus)."""
        if event and event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                self.last_minimize_time = time.time()
        if event and event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                # Bỏ qua nếu cửa sổ vừa mới được mở/khôi phục gần đây
                if time.time() - getattr(self, "last_shown_time", 0.0) < 0.5:
                    event.accept()
                    return
                from PyQt6.QtWidgets import QApplication
                # Kiểm tra xem có đang giữ chuột trái (đang kéo) hoặc đã phóng to/Aero Snap không
                if QApplication.mouseButtons() & Qt.MouseButton.LeftButton or self.isMaximized():
                    event.accept()
                    return
                    
                # Bỏ qua ẩn nếu vừa xảy ra kéo cửa sổ hoặc Aero Snap gần đây
                if time.time() - self.last_move_resize_time < 1.0:
                    event.accept()
                    return
                    
                # Kiểm tra xem con trỏ chuột hoặc vị trí cửa sổ có sát rìa màn hình không
                cursor_pos = QCursor.pos()
                screen = QApplication.screenAt(cursor_pos)
                if not screen:
                    screen = self.screen()
                if screen:
                    geom = screen.geometry()
                    margin = 40
                    # Con trỏ chuột ở sát rìa
                    if (abs(cursor_pos.x() - geom.left()) < margin or
                        abs(cursor_pos.x() - geom.right()) < margin or
                        abs(cursor_pos.y() - geom.top()) < margin or
                        abs(cursor_pos.y() - geom.bottom()) < margin):
                        event.accept()
                        return
                    # Khung cửa sổ ở sát hoặc vượt ngoài màn hình
                    win_geom = self.frameGeometry()
                    if (abs(win_geom.left() - geom.left()) < margin or
                        abs(win_geom.right() - geom.right()) < margin or
                        abs(win_geom.top() - geom.top()) < margin or
                        abs(win_geom.bottom() - geom.bottom()) < margin or
                        win_geom.left() < geom.left() or
                        win_geom.right() > geom.right() or
                        win_geom.top() < geom.top() or
                        win_geom.bottom() > geom.bottom()):
                        event.accept()
                        return

                active_win = QApplication.activeWindow()
                # Chỉ thu nhỏ xuống thanh Taskbar khi click ra ngoài ứng dụng hoàn toàn (activeWindow() là None)
                if active_win is None:
                    self.showMinimized()
        super().changeEvent(event)

    def show_translation_loading(self):
        """Hiển thị trạng thái loading chỉ riêng cho ô kết quả dịch (khi người dùng đang tự gõ)."""
        self.target_text_edit.setPlainText("Đang dịch bằng AI, vui lòng chờ trong giây lát...")

    def _on_source_text_changed(self):
        if self.is_updating_programmatically:
            return
        # Bắt đầu đếm ngược debounce 800ms
        self.debounce_timer.start(800)

    def _on_debounce_timeout(self):
        text = self.source_text_edit.toPlainText().strip()
        if text:
            self.source_text = text
            self.translation_requested.emit(text)

    def eventFilter(self, obj, event):
        if obj == self.source_text_edit and event and event.type() == QEvent.Type.KeyPress:
            # Nếu nhấn Enter (không giữ Shift) hoặc Ctrl+Enter
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if event.modifiers() & Qt.KeyboardModifier.ControlModifier or not (event.modifiers() & Qt.KeyboardModifier.ShiftModifier):
                    # Kích hoạt dịch ngay lập tức
                    self.debounce_timer.stop()
                    self._on_debounce_timeout()
                    return True # Đã xử lý sự kiện
        return super().eventFilter(obj, event)
