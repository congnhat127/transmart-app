import os
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QSpinBox, QPushButton, QTabWidget, QFormLayout, QGroupBox,
    QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QFont, QCursor
from config.settings import settings_manager
from config.constants import SUPPORTED_LANGUAGES

class SettingsWindow(QWidget):
    """
    Giao diện Dashboard cấu hình ứng dụng (API Key, phím tắt, giao diện...).
    Được thiết kế hiện đại, đồng bộ phong cách với toàn bộ ứng dụng TransMart.
    """
    settings_saved = pyqtSignal()  # Tín hiệu phát ra sau khi lưu cấu hình thành công

    def __init__(self, theme: str = "dark"):
        super().__init__()
        self.theme = theme
        self.last_move_resize_time = 0.0
        self.setWindowTitle("TransMart - Cài đặt hệ thống")
        self.setMinimumSize(420, 480)
        self.resize(450, 500)
        
        # Thiết lập cờ cửa sổ (có viền chuẩn và luôn nổi trên cùng để đè lên pop-up chính)
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowCloseButtonHint | 
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        # Áp dụng stylesheet đồng bộ phong cách
        self._apply_style()
        self._init_ui()
        self.load_values()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        # Tiêu đề Header
        header_layout = QHBoxLayout()
        header_title = QLabel("CÀI ĐẶT HỆ THỐNG")
        header_title.setObjectName("HeaderTitle")
        header_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Thanh Tabs chính
        self.tabs = QTabWidget()
        self.tabs.setObjectName("SettingsTabs")
        
        # --- TAB 1: CÀI ĐẶT CHUNG ---
        tab_general = QWidget()
        general_layout = QVBoxLayout(tab_general)
        general_layout.setContentsMargins(10, 15, 10, 15)
        general_layout.setSpacing(12)
        
        form_general = QFormLayout()
        form_general.setSpacing(10)
        form_general.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Giao diện (Theme)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Tối (Dark Mode)", "Sáng (Light Mode)"])
        form_general.addRow("Giao diện:", self.theme_combo)
        
        # Cỡ chữ (Font Size)
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 20)
        self.font_size_spin.setValue(13)
        self.font_size_spin.setSuffix(" px")
        form_general.addRow("Cỡ chữ dịch:", self.font_size_spin)
        
        # Phím tắt dịch (Hotkey)
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText("Ví dụ: alt+z")
        form_general.addRow("Phím tắt dịch:", self.hotkey_input)
        
        # Phím tắt OCR (OCR Hotkey)
        self.ocr_hotkey_input = QLineEdit()
        self.ocr_hotkey_input.setPlaceholderText("Ví dụ: alt+q")
        form_general.addRow("Phím tắt OCR:", self.ocr_hotkey_input)
        
        # Ngôn ngữ nguồn (Source Language)
        self.source_lang_combo = QComboBox()
        for lang_key, lang_name in SUPPORTED_LANGUAGES.items():
            self.source_lang_combo.addItem(lang_name, lang_key)
        form_general.addRow("Dịch từ (Nguồn):", self.source_lang_combo)
        
        # Ngôn ngữ đích (Target Language)
        self.target_lang_combo = QComboBox()
        for lang_key, lang_name in SUPPORTED_LANGUAGES.items():
            if lang_key != "Auto":
                self.target_lang_combo.addItem(lang_name, lang_key)
        form_general.addRow("Dịch sang (Đích):", self.target_lang_combo)
        
        general_layout.addLayout(form_general)
        general_layout.addStretch()
        self.tabs.addTab(tab_general, "Cài đặt chung")
        
        # --- TAB 2: CẤU HÌNH API KEY ---
        tab_api = QWidget()
        api_layout = QVBoxLayout(tab_api)
        api_layout.setContentsMargins(10, 15, 10, 15)
        api_layout.setSpacing(12)
        
        # Nhóm cấu hình Gemini API
        gemini_group = QGroupBox("Google Gemini Cloud (Khuyên dùng)")
        gemini_group.setObjectName("ApiGroupBox")
        gemini_form = QFormLayout(gemini_group)
        self.gemini_key_input = QLineEdit()
        self.gemini_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.gemini_key_input.setPlaceholderText("Nhập Gemini API Key tại đây...")
        gemini_form.addRow("API Key:", self.gemini_key_input)
        
        self.gemini_model_combo = QComboBox()
        self.gemini_model_combo.addItems([
            "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", 
            "gemini-3.5-flash", "gemini-flash-latest", "gemini-pro-latest", 
            "gemini-1.5-flash", "gemini-1.5-pro"
        ])
        gemini_form.addRow("Dòng Model:", self.gemini_model_combo)
        
        # Nhóm cấu hình OpenAI API
        openai_group = QGroupBox("OpenAI GPT Cloud")
        openai_group.setObjectName("ApiGroupBox")
        openai_form = QFormLayout(openai_group)
        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key_input.setPlaceholderText("Nhập OpenAI API Key tại đây...")
        openai_form.addRow("API Key:", self.openai_key_input)
        
        self.openai_model_combo = QComboBox()
        self.openai_model_combo.addItems(["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
        openai_form.addRow("Dòng Model:", self.openai_model_combo)
        
        api_layout.addWidget(gemini_group)
        api_layout.addWidget(openai_group)
        api_layout.addStretch()
        
        self.tabs.addTab(tab_api, "Cấu hình AI API")
        
        main_layout.addWidget(self.tabs)

        # --- FOOTER BUTTONS ---
        footer_buttons = QHBoxLayout()
        self.save_btn = QPushButton("Lưu cấu hình")
        self.save_btn.setObjectName("SaveBtn")
        self.save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_btn.clicked.connect(self.save_values)
        
        self.cancel_btn = QPushButton("Hủy")
        self.cancel_btn.setObjectName("CancelBtn")
        self.cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_btn.clicked.connect(self.cancel_changes)
        
        footer_buttons.addStretch()
        footer_buttons.addWidget(self.cancel_btn)
        footer_buttons.addWidget(self.save_btn)
        main_layout.addLayout(footer_buttons)

    def load_values(self):
        """Đọc và nạp dữ liệu từ file settings.json lên UI."""
        settings = settings_manager.load_settings()
        
        # Nạp cài đặt chung
        theme_val = settings.get("theme", "dark")
        self.theme_combo.setCurrentIndex(0 if theme_val == "dark" else 1)
        self.font_size_spin.setValue(settings.get("font_size", 13))
        self.hotkey_input.setText(settings.get("hotkey", "alt+z"))
        self.ocr_hotkey_input.setText(settings.get("ocr_hotkey", "alt+q"))
        
        # Nạp cài đặt ngôn ngữ
        source_lang = settings.get("source_lang", "Auto")
        idx_source = self.source_lang_combo.findData(source_lang)
        if idx_source >= 0:
            self.source_lang_combo.setCurrentIndex(idx_source)
            
        target_lang = settings.get("target_lang", "Vietnamese")
        idx_target = self.target_lang_combo.findData(target_lang)
        if idx_target >= 0:
            self.target_lang_combo.setCurrentIndex(idx_target)
        
        # Nạp cài đặt API
        self.gemini_key_input.setText(settings.get("gemini_api_key", ""))
        gemini_model = settings.get("gemini_model", "gemini-1.5-flash")
        idx_gemini = self.gemini_model_combo.findText(gemini_model)
        if idx_gemini >= 0:
            self.gemini_model_combo.setCurrentIndex(idx_gemini)
            
        self.openai_key_input.setText(settings.get("openai_api_key", ""))
        openai_model = settings.get("openai_model", "gpt-4o-mini")
        idx_openai = self.openai_model_combo.findText(openai_model)
        if idx_openai >= 0:
            self.openai_model_combo.setCurrentIndex(idx_openai)

    def save_values(self):
        """Lưu toàn bộ cài đặt từ UI xuống file settings.json."""
        theme_val = "dark" if self.theme_combo.currentIndex() == 0 else "light"
        
        new_settings = {
            "theme": theme_val,
            "font_size": self.font_size_spin.value(),
            "hotkey": self.hotkey_input.text().strip().lower(),
            "ocr_hotkey": self.ocr_hotkey_input.text().strip().lower(),
            "source_lang": self.source_lang_combo.currentData(),
            "target_lang": self.target_lang_combo.currentData(),
            "gemini_api_key": self.gemini_key_input.text().strip(),
            "gemini_model": self.gemini_model_combo.currentText(),
            "openai_api_key": self.openai_key_input.text().strip(),
            "openai_model": self.openai_model_combo.currentText()
        }
        
        settings_manager.save_settings(new_settings)
        self.settings_saved.emit()
        self.close()

    def cancel_changes(self):
        """Hủy bỏ thay đổi bằng cách nạp lại cấu hình cũ từ ổ đĩa và đóng cửa sổ."""
        self.load_values()
        self.close()

    def _apply_style(self):
        """Thiết lập Style CSS cho Settings Window."""
        if self.theme == "dark":
            self.setStyleSheet("""
                QWidget {
                    background-color: #1E1E1E;
                    color: #E0E0E0;
                    font-family: 'Segoe UI', sans-serif;
                }
                QLabel#HeaderTitle {
                    color: #FFFFFF;
                }
                QTabWidget::pane {
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 6px;
                    background-color: #252526;
                }
                QTabBar::tab {
                    background-color: #2D2D2D;
                    color: #888888;
                    padding: 8px 16px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    border: 1px solid rgba(255, 255, 255, 0.05);
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #252526;
                    color: #FFFFFF;
                    border-bottom-color: transparent;
                }
                QGroupBox#ApiGroupBox {
                    font-weight: bold;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 6px;
                    margin-top: 15px;
                    padding-top: 15px;
                }
                QGroupBox#ApiGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 10px;
                    padding: 0 5px;
                    color: #0078D4;
                }
                QLineEdit, QComboBox, QSpinBox {
                    background-color: #2D2D2D;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                    padding: 5px 8px;
                    color: #FFFFFF;
                }
                QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                    border: 1px solid #0078D4;
                }
                QPushButton {
                    padding: 6px 16px;
                    border-radius: 4px;
                    font-weight: 600;
                }
                QPushButton#SaveBtn {
                    background-color: #0078D4;
                    color: #FFFFFF;
                    border: none;
                }
                QPushButton#SaveBtn:hover {
                    background-color: #1084E3;
                }
                QPushButton#CancelBtn {
                    background-color: transparent;
                    color: #888888;
                    border: 1px solid rgba(255, 255, 255, 0.15);
                }
                QPushButton#CancelBtn:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                    color: #FFFFFF;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #F3F3F3;
                    color: #333333;
                    font-family: 'Segoe UI', sans-serif;
                }
                QLabel#HeaderTitle {
                    color: #1A1A1A;
                }
                QTabWidget::pane {
                    border: 1px solid rgba(0, 0, 0, 0.1);
                    border-radius: 6px;
                    background-color: #FFFFFF;
                }
                QTabBar::tab {
                    background-color: #E5E5E5;
                    color: #666666;
                    padding: 8px 16px;
                    border-top-left-radius: 4px;
                    border-top-right-radius: 4px;
                    border: 1px solid rgba(0, 0, 0, 0.05);
                    margin-right: 2px;
                }
                QTabBar::tab:selected {
                    background-color: #FFFFFF;
                    color: #0078D4;
                    border-bottom-color: transparent;
                    font-weight: bold;
                }
                QGroupBox#ApiGroupBox {
                    font-weight: bold;
                    border: 1px solid rgba(0, 0, 0, 0.15);
                    border-radius: 6px;
                    margin-top: 15px;
                    padding-top: 15px;
                }
                QGroupBox#ApiGroupBox::title {
                    subcontrol-origin: margin;
                    subcontrol-position: top left;
                    left: 10px;
                    padding: 0 5px;
                    color: #0078D4;
                }
                QLineEdit, QComboBox, QSpinBox {
                    background-color: #FFFFFF;
                    border: 1px solid rgba(0, 0, 0, 0.15);
                    border-radius: 4px;
                    padding: 5px 8px;
                    color: #333333;
                }
                QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                    border: 1px solid #0078D4;
                }
                QPushButton {
                    padding: 6px 16px;
                    border-radius: 4px;
                    font-weight: 600;
                }
                QPushButton#SaveBtn {
                    background-color: #0078D4;
                    color: #FFFFFF;
                    border: none;
                }
                QPushButton#SaveBtn:hover {
                    background-color: #1084E3;
                }
                QPushButton#CancelBtn {
                    background-color: transparent;
                    color: #666666;
                    border: 1px solid rgba(0, 0, 0, 0.15);
                }
                QPushButton#CancelBtn:hover {
                    background-color: rgba(0, 0, 0, 0.05);
                    color: #1A1A1A;
                }
            """)

    def moveEvent(self, event):
        self.last_move_resize_time = time.time()
        super().moveEvent(event)

    def resizeEvent(self, event):
        self.last_move_resize_time = time.time()
        super().resizeEvent(event)

    def changeEvent(self, event):
        """Ẩn cửa sổ cài đặt nếu người dùng click ra ngoài (mất focus)."""
        if event and event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow():
                # Kiểm tra xem có đang giữ chuột trái (đang kéo) hoặc đã phóng to/Aero Snap không
                if QApplication.mouseButtons() & Qt.MouseButton.LeftButton or self.isMaximized():
                    event.accept()
                    return

                # Bỏ qua nếu vừa xảy ra kéo cửa sổ hoặc Aero Snap gần đây
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

                self.save_values()
        super().changeEvent(event)
