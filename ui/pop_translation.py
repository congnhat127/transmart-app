from PyQt6.QtCore import Qt, QPropertyAnimation, QPoint
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTabWidget, QTextBrowser, QGraphicsDropShadowEffect)
from PyQt6.QtGui import QColor, QCursor
from ui.styles import get_translation_popup_style
from config.settings import settings_manager
from services.tts_service import tts_service

class PopTranslationWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Cấu hình cửa sổ không viền, luôn hiển thị trên cùng và là công cụ phụ trợ
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("MainWindow")
        
        # Đặt kích thước mặc định cho cửa sổ dịch
        self.setFixedSize(450, 320)
        
        # Biến phục vụ di chuyển cửa sổ bằng cách kéo thả tiêu đề
        self.drag_position = QPoint()
        
        self.text_to_speak = ""
        self.detected_lang = ""
        
        self.setup_ui()

    def setup_ui(self):
        # Layout chính của cửa sổ
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(10)
        
        # --- HEADER ---
        header_layout = QHBoxLayout()
        
        # Tiêu đề App
        title_label = QLabel("TransMart")
        title_label.setObjectName("TitleLabel")
        header_layout.addWidget(title_label)
        
        # Hiển thị ngôn ngữ phát hiện
        self.lang_label = QLabel("Detecting...")
        self.lang_label.setObjectName("LangLabel")
        self.lang_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(self.lang_label)
        
        header_layout.addStretch()
        
        # Nút đóng cửa sổ dịch (X)
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 14px;
                font-weight: bold;
                color: #888888;
            }
            QPushButton:hover {
                color: #FF5A5F;
            }
        """)
        close_btn.clicked.connect(self.close)
        header_layout.addWidget(close_btn)
        
        main_layout.addLayout(header_layout)
        
        # --- TABS NỘI DUNG ---
        self.tabs = QTabWidget()
        
        # Tab 1: Bản dịch chính
        self.tab_translation = QWidget()
        trans_layout = QVBoxLayout(self.tab_translation)
        trans_layout.setContentsMargins(0, 10, 0, 0)
        
        self.translation_browser = QTextBrowser()
        self.translation_browser.setOpenExternalLinks(True)
        trans_layout.addWidget(self.translation_browser)
        
        # Hàng nút thao tác trong tab dịch (ví dụ: phát âm)
        trans_action_layout = QHBoxLayout()
        trans_action_layout.addStretch()
        
        # Nút phát âm văn bản gốc
        self.speak_btn = QPushButton("🔊")
        self.speak_btn.setObjectName("SpeakBtn")
        self.speak_btn.setToolTip("Phát âm văn bản gốc")
        self.speak_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.speak_btn.clicked.connect(self._on_speak_clicked)
        trans_action_layout.addWidget(self.speak_btn)
        
        trans_layout.addLayout(trans_action_layout)
        self.tabs.addTab(self.tab_translation, "Bản dịch")
        
        # Tab 2: Giải nghĩa ngữ pháp và ngữ cảnh
        self.tab_explanation = QWidget()
        expl_layout = QVBoxLayout(self.tab_explanation)
        expl_layout.setContentsMargins(0, 10, 0, 0)
        
        self.explanation_browser = QTextBrowser()
        expl_layout.addWidget(self.explanation_browser)
        self.tabs.addTab(self.tab_explanation, "Giải thích từ")
        
        # Tab 3: Ví dụ & Đồng nghĩa
        self.tab_examples = QWidget()
        ex_layout = QVBoxLayout(self.tab_examples)
        ex_layout.setContentsMargins(0, 10, 0, 0)
        
        self.examples_browser = QTextBrowser()
        ex_layout.addWidget(self.examples_browser)
        self.tabs.addTab(self.tab_examples, "Ví dụ & Đồng nghĩa")
        
        main_layout.addWidget(self.tabs)
        
        # --- HIỆU ỨNG ĐỔ BÓNG (SHADOW) ---
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 120))
        shadow.setOffset(0, 6)
        self.setGraphicsEffect(shadow)

    def display_result(self, raw_text: str, result_dict: dict):
        """Đổ dữ liệu JSON từ AI vào các tab UI và hiển thị popup."""
        self.text_to_speak = raw_text
        self.detected_lang = result_dict.get("detected_lang", "Auto")
        
        # 1. Cập nhật nhãn ngôn ngữ
        target_lang = settings_manager.get("target_lang", "Vietnamese")
        self.lang_label.setText(f"{self.detected_lang} ➔ {target_lang}")
        
        # 2. Cập nhật Tab Bản dịch (Hiển thị văn bản dịch và phiên âm nếu có)
        translated_text = result_dict.get("translated_text", "")
        phonetic = result_dict.get("phonetic", "")
        
        trans_html = f"<h3>{translated_text}</h3>"
        if phonetic:
            trans_html += f"<p style='color: #0078D4; font-style: italic; font-weight: bold;'>Phát âm: {phonetic}</p>"
        trans_html += f"<p style='color: gray; margin-top: 10px;'>Gốc: {raw_text}</p>"
        
        self.translation_browser.setHtml(trans_html)
        
        # 3. Cập nhật Tab Giải thích
        explanation = result_dict.get("explanation", "Không có giải thích bổ sung.")
        # Định dạng văn bản thô xuống dòng thành HTML
        expl_html = f"<div style='line-height: 1.4;'>{explanation.replace(chr(10), '<br>')}</div>"
        self.explanation_browser.setHtml(expl_html)
        
        # 4. Cập nhật Tab Ví dụ & Từ đồng nghĩa
        synonyms = result_dict.get("synonyms", [])
        examples = result_dict.get("examples", [])
        
        ex_html = ""
        if synonyms:
            ex_html += "<h4>Từ đồng nghĩa:</h4><p>"
            ex_html += ", ".join([f"<span style='background-color: rgba(0, 120, 212, 0.15); padding: 2px 6px; border-radius: 4px;'>{s}</span>" for s in synonyms])
            ex_html += "</p><hr>"
            
        if examples:
            ex_html += "<h4>Ví dụ minh họa:</h4><ul>"
            for item in examples:
                ex_html += f"<li style='margin-bottom: 8px;'><b>{item.get('original', '')}</b><br><span style='color: gray;'>➔ {item.get('translated', '')}</span></li>"
            ex_html += "</ul>"
        else:
            ex_html += "<p style='color: gray;'>Không có ví dụ mẫu.</p>"
            
        self.examples_browser.setHtml(ex_html)
        
        # 5. Cập nhật styles theo Theme & Font Size từ cài đặt hiện tại
        theme = settings_manager.get("theme", "dark")
        font_size = settings_manager.get("font_size", 13)
        self.setStyleSheet(get_translation_popup_style(theme, font_size))
        
        # 6. Mở Tab đầu tiên mặc định
        self.tabs.setCurrentIndex(0)
        
        # 7. Di chuyển cửa sổ dịch tới vị trí con trỏ chuột và hiển thị
        pos = QCursor.pos()
        self.move(pos.x() + 15, pos.y() + 15)
        
        # 8. Chạy hiệu ứng Fade in mượt mà
        self.show()
        self.fade_in()

    def fade_in(self):
        self.setWindowOpacity(0.0)
        self.anim = QPropertyAnimation(self, b"windowOpacity")
        self.anim.setDuration(220)
        self.anim.setStartValue(0.0)
        # Giới hạn mờ tối đa là 0.95 để giữ hiệu ứng thủy tinh nhẹ
        self.anim.setEndValue(0.95)
        self.anim.start()

    def _on_speak_clicked(self):
        """Kích hoạt giọng đọc TTS cho đoạn văn bản gốc."""
        if self.text_to_speak:
            tts_service.speak(self.text_to_speak, self.detected_lang)

    # --- Hỗ trợ di chuyển cửa sổ (Drag Window) ---
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()
            
    def keyPressEvent(self, event):
        # Đóng popup bằng phím Esc để tiện lợi
        if event.key() == Qt.Key.Key_Escape:
            self.close()
            event.accept()
        else:
            super().keyPressEvent(event)
