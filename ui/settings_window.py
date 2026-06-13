from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QCheckBox, QPushButton, 
                             QGroupBox, QFormLayout, QSpinBox, QMessageBox, QTabWidget)
from ui.styles import get_settings_window_style
from config.settings import settings_manager
from config.constants import SUPPORTED_LANGUAGES

class SettingsWindow(QWidget):
    # Phát ra khi lưu thành công cấu hình để thông báo cho main.py cập nhật nóng listener
    settings_saved = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("SettingsWindow")
        self.setWindowTitle("TransMart - Dashboard Cài đặt")
        self.setFixedSize(500, 420)
        
        self.setup_ui()
        self.load_values()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Tiêu đề chính
        header_label = QLabel("Cấu hình hệ thống TransMart")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #0078D4;")
        main_layout.addWidget(header_label)
        
        # Tạo Tab Widget để phân chia các phần cấu hình rõ ràng
        self.tabs = QTabWidget()
        
        # --- TAB 1: AI SERVICE CONFIG ---
        self.tab_ai = QWidget()
        ai_layout = QVBoxLayout(self.tab_ai)
        ai_layout.setContentsMargins(10, 10, 10, 10)
        
        group_ai = QGroupBox("Dịch vụ Trí tuệ Nhân tạo (AI)")
        ai_form = QFormLayout(group_ai)
        ai_form.setSpacing(10)
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["gemini", "openai"])
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        ai_form.addRow("Nhà cung cấp API:", self.provider_combo)
        
        # API Key (có chế độ ẩn/hiện)
        key_layout = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Nhập API Key cá nhân của bạn tại đây...")
        key_layout.addWidget(self.api_key_input)
        
        self.toggle_key_btn = QPushButton("👁")
        self.toggle_key_btn.setFixedSize(30, 28)
        self.toggle_key_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.toggle_key_btn.clicked.connect(self._toggle_api_key_visibility)
        key_layout.addWidget(self.toggle_key_btn)
        
        ai_form.addRow("API Key:", key_layout)
        
        self.gemini_model_combo = QComboBox()
        self.gemini_model_combo.addItems(["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"])
        ai_form.addRow("Model Gemini:", self.gemini_model_combo)
        
        self.openai_model_input = QLineEdit()
        self.openai_model_input.setPlaceholderText("Ví dụ: gpt-4o-mini, gpt-4o, deepseek-chat")
        ai_form.addRow("Model OpenAI:", self.openai_model_input)
        
        self.openai_url_input = QLineEdit()
        self.openai_url_input.setPlaceholderText("https://api.openai.com/v1")
        ai_form.addRow("OpenAI Base URL:", self.openai_url_input)
        
        ai_layout.addWidget(group_ai)
        ai_layout.addStretch()
        self.tabs.addTab(self.tab_ai, "API & AI Models")
        
        # --- TAB 2: TRANSLATE & HOTKEYS ---
        self.tab_translate = QWidget()
        trans_layout = QVBoxLayout(self.tab_translate)
        trans_layout.setContentsMargins(10, 10, 10, 10)
        
        group_trans = QGroupBox("Cấu hình Dịch & Phím tắt")
        trans_form = QFormLayout(group_trans)
        trans_form.setSpacing(10)
        
        self.src_lang_combo = QComboBox()
        self.tgt_lang_combo = QComboBox()
        for key, name in SUPPORTED_LANGUAGES.items():
            self.src_lang_combo.addItem(name, key)
            if key != "Auto": # Ngôn ngữ đích không thể là Tự động phát hiện
                self.tgt_lang_combo.addItem(name, key)
                
        trans_form.addRow("Ngôn ngữ nguồn:", self.src_lang_combo)
        trans_form.addRow("Ngôn ngữ dịch:", self.tgt_lang_combo)
        
        self.hotkey_input = QLineEdit()
        self.hotkey_input.setPlaceholderText("Ví dụ: alt+d, ctrl+shift+d")
        trans_form.addRow("Phím tắt dịch nhanh:", self.hotkey_input)
        
        self.ocr_hotkey_input = QLineEdit()
        self.ocr_hotkey_input.setPlaceholderText("Ví dụ: alt+q, ctrl+shift+q")
        trans_form.addRow("Phím tắt chụp ảnh OCR:", self.ocr_hotkey_input)
        
        self.show_icon_cb = QCheckBox("Hiển thị nút tròn dịch thuật nhanh dưới chuột khi bôi đen text")
        trans_form.addRow("", self.show_icon_cb)
        
        trans_layout.addWidget(group_trans)
        trans_layout.addStretch()
        self.tabs.addTab(self.tab_translate, "Dịch & Phím tắt")
        
        # --- TAB 3: THEME & APPEARANCE ---
        self.tab_theme = QWidget()
        theme_layout = QVBoxLayout(self.tab_theme)
        theme_layout.setContentsMargins(10, 10, 10, 10)
        
        group_theme = QGroupBox("Giao diện ứng dụng")
        theme_form = QFormLayout(group_theme)
        theme_form.setSpacing(12)
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["dark", "light"])
        theme_form.addRow("Chế độ màu (Theme):", self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(10, 20)
        self.font_size_spin.setSuffix(" pt")
        theme_form.addRow("Kích thước font dịch:", self.font_size_spin)
        
        theme_layout.addWidget(group_theme)
        theme_layout.addStretch()
        self.tabs.addTab(self.tab_theme, "Giao diện")
        
        main_layout.addWidget(self.tabs)
        
        # Hàng nút Lưu & Hủy
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.close)
        cancel_btn.setStyleSheet("padding: 7px 15px; font-size: 13px;")
        footer_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Lưu cấu hình")
        save_btn.setObjectName("SaveBtn")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._on_save_clicked)
        footer_layout.addWidget(save_btn)
        
        main_layout.addLayout(footer_layout)
        
        # Thiết lập style sheet ban đầu
        self.update_style()

    def update_style(self):
        theme = settings_manager.get("theme", "dark")
        self.setStyleSheet(get_settings_window_style(theme))

    def load_values(self):
        """Đổ các giá trị cấu hình hiện tại lên form điều khiển."""
        self.provider_combo.setCurrentText(settings_manager.get("provider", "gemini"))
        self.api_key_input.setText(settings_manager.get("api_key", ""))
        self.gemini_model_combo.setCurrentText(settings_manager.get("gemini_model", "gemini-1.5-flash"))
        self.openai_model_input.setText(settings_manager.get("openai_model", "gpt-4o-mini"))
        self.openai_url_input.setText(settings_manager.get("openai_base_url", "https://api.openai.com/v1"))
        
        # Load ngôn ngữ
        src_lang = settings_manager.get("source_lang", "Auto")
        tgt_lang = settings_manager.get("target_lang", "Vietnamese")
        
        src_idx = self.src_lang_combo.findData(src_lang)
        if src_idx != -1:
            self.src_lang_combo.setCurrentIndex(src_idx)
            
        tgt_idx = self.tgt_lang_combo.findData(tgt_lang)
        if tgt_idx != -1:
            self.tgt_lang_combo.setCurrentIndex(tgt_idx)
            
        self.hotkey_input.setText(settings_manager.get("hotkey", "alt+d"))
        self.ocr_hotkey_input.setText(settings_manager.get("ocr_hotkey", "alt+q"))
        self.show_icon_cb.setChecked(settings_manager.get("show_pop_icon", True))
        
        self.theme_combo.setCurrentText(settings_manager.get("theme", "dark"))
        self.font_size_spin.setValue(settings_manager.get("font_size", 13))
        
        # Ẩn hiện các trường OpenAI/Gemini dựa trên provider
        self._on_provider_changed()

    def _on_provider_changed(self):
        is_openai = self.provider_combo.currentText() == "openai"
        self.openai_model_input.setEnabled(is_openai)
        self.openai_url_input.setEnabled(is_openai)
        self.gemini_model_combo.setEnabled(not is_openai)

    def _toggle_api_key_visibility(self):
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_key_btn.setText("🔒")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_key_btn.setText("👁")

    def _on_save_clicked(self):
        """Lưu trữ các cài đặt mới xuống storage."""
        new_settings = {
            "provider": self.provider_combo.currentText(),
            "api_key": self.api_key_input.text().strip(),
            "gemini_model": self.gemini_model_combo.currentText(),
            "openai_model": self.openai_model_input.text().strip(),
            "openai_base_url": self.openai_url_input.text().strip(),
            "source_lang": self.src_lang_combo.currentData(),
            "target_lang": self.tgt_lang_combo.currentData(),
            "hotkey": self.hotkey_input.text().strip().lower(),
            "ocr_hotkey": self.ocr_hotkey_input.text().strip().lower(),
            "show_pop_icon": self.show_icon_cb.isChecked(),
            "theme": self.theme_combo.currentText(),
            "font_size": self.font_size_spin.value()
        }
        
        # Kiểm tra nhanh phím tắt hợp lệ
        if not new_settings["hotkey"] or not new_settings["ocr_hotkey"]:
            QMessageBox.warning(self, "Lỗi đầu vào", "Phím tắt kích hoạt không được để trống!")
            return
            
        # Lưu cài đặt
        if settings_manager.save_settings(new_settings):
            self.update_style()
            self.settings_saved.emit()
            QMessageBox.information(self, "Thành công", "Đã lưu cài đặt cấu hình thành công!")
            self.close()
        else:
            QMessageBox.critical(self, "Thất bại", "Lỗi xảy ra trong quá trình lưu cấu hình!")
