# ui/pop_translation.py
import pyperclip
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QTimer
from PyQt6.QtGui import QMouseEvent, QFont

from ui.styles import get_translation_popup_style

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

    def __init__(self, theme: str = "dark", font_size: int = 13):
        super().__init__()
        self.theme = theme
        self.font_size = font_size
        
        # Biến phục vụ di chuyển cửa sổ (Window Dragging)
        self.drag_position = None
        self.target_lang_code = "vi" # Mặc định ngôn ngữ đích là tiếng Việt
        
        # 1. Cấu hình đặc tính cửa sổ nổi
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |      # Bỏ viền Windows
            Qt.WindowType.WindowStaysOnTopHint |     # Luôn hiển thị trên cùng
            Qt.WindowType.Tool                       # Không hiện ở Taskbar
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) # Trong suốt nền
        
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
        
        # --- HEADER LAYOUT (Tiêu đề ngôn ngữ & Nút đóng) ---
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        
        self.lang_label = QLabel("ĐANG DỊCH...")
        self.lang_label.setObjectName("LangLabel")
        
        # Nút thu nhỏ (Minimize)
        self.minimize_btn = QPushButton("\uE921")
        self.minimize_btn.setObjectName("MinBtn")
        self.minimize_btn.setFixedSize(24, 24)
        self.minimize_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.minimize_btn.setToolTip("Thu nhỏ ứng dụng")
        self.minimize_btn.clicked.connect(self.showMinimized)
        
        # Nút phóng to / đổi kích thước (Disabled)
        self.maximize_btn = QPushButton("\uE922")
        self.maximize_btn.setObjectName("MaxBtn")
        self.maximize_btn.setFixedSize(24, 24)
        self.maximize_btn.setEnabled(False)
        self.maximize_btn.setToolTip("Phóng to (Không khả dụng)")
        
        # Nút đóng (Close)
        self.close_btn = QPushButton("\uE8BB")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setToolTip("Đóng")
        self.close_btn.clicked.connect(self.hide)
        
        header_layout.addWidget(self.lang_label)
        header_layout.addStretch()
        header_layout.addWidget(self.minimize_btn)
        header_layout.addWidget(self.maximize_btn)
        header_layout.addWidget(self.close_btn)
        
        # --- BODY LAYOUT (Văn bản gốc & Văn bản dịch) ---
        # Ô chứa văn bản gốc (Nhỏ hơn)
        self.source_text_edit = QTextEdit()
        self.source_text_edit.setReadOnly(True)
        self.source_text_edit.setPlaceholderText("Văn bản gốc...")
        self.source_text_edit.setMaximumHeight(70)
        
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
        
        # Nút Phát âm (TTS)
        self.tts_btn = QPushButton("🔊 Phát âm")
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
        self.source_text_edit.setPlainText(raw_text)
        self.target_text_edit.setPlainText("Đang dịch bằng AI, vui lòng chờ trong giây lát...")
        self.lang_label.setText(f"{source_lang.upper()} ➜ {target_lang.upper()}")
        
        # Di chuyển hộp thoại đến vị trí chuột (lệch xuống dưới 20px)
        self.move(x + 10, y + 20)
        self.show()
        
        # Đưa con trỏ chuột ra ngoài để người dùng có thể đọc ngay
        self.raise_()
        self.activateWindow()

    def display_result(self, raw_text: str, result_dict: dict):
        """
        Đổ kết quả dịch thuật chi tiết từ AI vào hộp thoại.
        
        Args:
            raw_text (str): Văn bản gốc.
            result_dict (dict): Từ điển kết quả dịch có cấu trúc từ AI.
                                Ví dụ: {"translation": "...", "explanation": "..."}
        """
        self.source_text_edit.setPlainText(raw_text)
        
        translation = result_dict.get("translation", "")
        explanation = result_dict.get("explanation", "")
        detected_lang = result_dict.get("detected_lang", "")
        
        # Cập nhật tiêu đề ngôn ngữ nếu có thông tin phát hiện ngôn ngữ tự động
        if detected_lang:
            self.lang_label.setText(f"{detected_lang.upper()} ➜ TIẾNG VIỆT")
            self.target_lang_code = "vi" # Đặt ngôn ngữ đọc cho TTS
            
        # Định dạng văn bản hiển thị đẹp mắt
        display_html = f"<b>Bản dịch:</b><br>{translation}"
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
        translated_text = self.target_text_edit.toPlainText()
        if "Bản dịch:" in translated_text:
            translated_text = translated_text.split("Bản dịch:\n")[-1]
        if "Giải thích chi tiết:" in translated_text:
            translated_text = translated_text.split("\n\nGiải thích chi tiết:")[0]
            
        text_to_read = translated_text.strip()
        if text_to_read:
            # Phát tín hiệu yêu cầu controller xử lý đọc bằng Edge TTS
            self.speak_triggered.emit(text_to_read, self.target_lang_code)

    def _on_history_clicked(self):
        """Xử lý sự kiện click nút Lịch sử dịch."""
        self.history_triggered.emit()

    def _on_api_clicked(self):
        """Xử lý sự kiện click nút Cấu hình API Key."""
        self.api_triggered.emit()

    def _on_settings_clicked(self):
        """Xử lý sự kiện click nút Cài đặt."""
        self.settings_triggered.emit()

    # === Các sự kiện đè chuột kéo để di chuyển cửa sổ (Window Dragging) ===
    
    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            # Ghi lại vị trí tương đối của chuột so với góc trái cửa sổ
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton and self.drag_position is not None:
            # Cập nhật vị trí cửa sổ theo chuyển động chuột
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_position = None
        event.accept()
