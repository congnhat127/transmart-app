import os
import time
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QSpinBox, QPushButton, QTabWidget, QFormLayout, QGroupBox,
    QApplication, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QThread
from PyQt6.QtGui import QFont, QCursor
from config.settings import settings_manager
from config.constants import SUPPORTED_LANGUAGES

class ModelFetchThread(QThread):
    """Luồng phụ để tải danh sách mô hình trực tuyến tránh treo giao diện chính."""
    fetched = pyqtSignal(list)
    
    def __init__(self, provider: str, api_key: str, base_url: str = None):
        super().__init__()
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        
    def run(self):
        from services.ai_service import AIService
        if self.provider == "gemini":
            models = AIService.fetch_gemini_models(self.api_key)
        else:
            models = AIService.fetch_openai_models(self.api_key, self.base_url)
        self.fetched.emit(models)

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
        
        gemini_model_layout = QHBoxLayout()
        self.gemini_model_combo = QComboBox()
        self.gemini_model_combo.addItems([
            "gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", 
            "gemini-3.5-flash", "gemini-flash-latest", "gemini-pro-latest", 
            "gemini-1.5-flash", "gemini-1.5-pro"
        ])
        self.gemini_refresh_btn = QPushButton("🔄 Cập nhật")
        self.gemini_refresh_btn.setObjectName("RefreshModelBtn")
        self.gemini_refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.gemini_refresh_btn.setToolTip("Tải danh sách mô hình mới nhất từ API")
        self.gemini_refresh_btn.clicked.connect(self.refresh_gemini_models)
        gemini_model_layout.addWidget(self.gemini_model_combo, 1)
        gemini_model_layout.addWidget(self.gemini_refresh_btn)
        gemini_form.addRow("Dòng Model:", gemini_model_layout)
        
        # Nhóm cấu hình OpenAI API
        openai_group = QGroupBox("OpenAI GPT Cloud")
        openai_group.setObjectName("ApiGroupBox")
        openai_form = QFormLayout(openai_group)
        self.openai_key_input = QLineEdit()
        self.openai_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key_input.setPlaceholderText("Nhập OpenAI API Key tại đây...")
        openai_form.addRow("API Key:", self.openai_key_input)
        
        openai_model_layout = QHBoxLayout()
        self.openai_model_combo = QComboBox()
        self.openai_model_combo.addItems(["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
        self.openai_refresh_btn = QPushButton("🔄 Cập nhật")
        self.openai_refresh_btn.setObjectName("RefreshModelBtn")
        self.openai_refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.openai_refresh_btn.setToolTip("Tải danh sách mô hình mới nhất từ API")
        self.openai_refresh_btn.clicked.connect(self.refresh_openai_models)
        openai_model_layout.addWidget(self.openai_model_combo, 1)
        openai_model_layout.addWidget(self.openai_refresh_btn)
        openai_form.addRow("Dòng Model:", openai_model_layout)
        
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
        self.save_btn.clicked.connect(lambda: self.save_values(close_window=True))
        
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
        else:
            self.gemini_model_combo.addItem(gemini_model)
            self.gemini_model_combo.setCurrentIndex(self.gemini_model_combo.count() - 1)
            
        self.openai_key_input.setText(settings.get("openai_api_key", ""))
        openai_model = settings.get("openai_model", "gpt-4o-mini")
        idx_openai = self.openai_model_combo.findText(openai_model)
        if idx_openai >= 0:
            self.openai_model_combo.setCurrentIndex(idx_openai)
        else:
            self.openai_model_combo.addItem(openai_model)
            self.openai_model_combo.setCurrentIndex(self.openai_model_combo.count() - 1)

    def save_values(self, close_window: bool = True):
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
        if close_window:
            self.close()

    def cancel_changes(self):
        """Hủy bỏ thay đổi bằng cách nạp lại cấu hình cũ từ ổ đĩa và đóng cửa sổ."""
        self.load_values()
        self.close()

    def refresh_gemini_models(self):
        key = self.gemini_key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập Gemini API Key trước khi cập nhật.")
            return
            
        self.gemini_refresh_btn.setEnabled(False)
        self.gemini_refresh_btn.setText("🔄 Đang tải...")
        
        self.gemini_fetch_thread = ModelFetchThread("gemini", key)
        self.gemini_fetch_thread.fetched.connect(self.on_gemini_models_fetched)
        self.gemini_fetch_thread.start()
        
    def on_gemini_models_fetched(self, models):
        self.gemini_refresh_btn.setEnabled(True)
        self.gemini_refresh_btn.setText("🔄 Cập nhật")
        
        if not models:
            QMessageBox.critical(self, "Lỗi", "Không thể lấy danh sách mô hình. Vui lòng kiểm tra lại API Key hoặc kết nối mạng.")
            return
            
        current_model = self.gemini_model_combo.currentText()
        self.gemini_model_combo.clear()
        self.gemini_model_combo.addItems(models)
        
        idx = self.gemini_model_combo.findText(current_model)
        if idx >= 0:
            self.gemini_model_combo.setCurrentIndex(idx)
        else:
            self.gemini_model_combo.setCurrentIndex(0)
            
        QMessageBox.information(self, "Thành công", f"Đã cập nhật thành công {len(models)} mô hình Gemini!")
        
    def refresh_openai_models(self):
        key = self.openai_key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng nhập OpenAI API Key trước khi cập nhật.")
            return
            
        base_url = settings_manager.get("openai_base_url", "https://api.openai.com/v1")
        
        self.openai_refresh_btn.setEnabled(False)
        self.openai_refresh_btn.setText("🔄 Đang tải...")
        
        self.openai_fetch_thread = ModelFetchThread("openai", key, base_url)
        self.openai_fetch_thread.fetched.connect(self.on_openai_models_fetched)
        self.openai_fetch_thread.start()
        
    def on_openai_models_fetched(self, models):
        self.openai_refresh_btn.setEnabled(True)
        self.openai_refresh_btn.setText("🔄 Cập nhật")
        
        if not models:
            QMessageBox.critical(self, "Lỗi", "Không thể lấy danh sách mô hình. Vui lòng kiểm tra lại API Key, Base URL hoặc kết nối mạng.")
            return
            
        current_model = self.openai_model_combo.currentText()
        self.openai_model_combo.clear()
        self.openai_model_combo.addItems(models)
        
        idx = self.openai_model_combo.findText(current_model)
        if idx >= 0:
            self.openai_model_combo.setCurrentIndex(idx)
        else:
            self.openai_model_combo.setCurrentIndex(0)
            
        QMessageBox.information(self, "Thành công", f"Đã cập nhật thành công {len(models)} mô hình OpenAI!")

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
        if event and event.type() == QEvent.Type.WindowStateChange:
            if self.isMinimized():
                self.last_minimize_time = time.time()
        super().changeEvent(event)
