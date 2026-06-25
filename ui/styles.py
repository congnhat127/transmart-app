# ui/styles.py
# Định nghĩa các hàm trả về chuỗi QSS (stylesheets) cho giao diện với thiết kế Glassmorphism
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import Qt

def create_tray_icon() -> QIcon:
    """Tạo một icon động hình tròn màu xanh với chữ T màu trắng cho System Tray."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    # Vẽ nền hình tròn màu xanh accent (#0078D4)
    painter.setBrush(QColor(0, 120, 212))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawEllipse(2, 2, 28, 28)
    
    # Vẽ chữ "T" màu trắng ở giữa
    painter.setPen(QColor(255, 255, 255))
    font = QFont("Segoe UI", 16, QFont.Weight.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "T")
    
    painter.end()
    return QIcon(pixmap)

def get_pop_icon_style(theme: str) -> str:
    """Trả về CSS cho nút dịch nhanh hình tròn nổi."""
    if theme == "dark":
        return """
        QPushButton {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(40, 40, 40, 0.95), stop:1 rgba(25, 25, 25, 0.95));
            border: 1.5px solid rgba(255, 255, 255, 0.18);
            border-radius: 18px; /* Vì size nút là 36x36 */
            color: #FFFFFF;
        }
        QPushButton:hover {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0078D4, stop:1 #005A9E);
            border: 1.5px solid rgba(255, 255, 255, 0.3);
            /* Tạo cảm giác nút to lên nhẹ */
        }
        """
    else:
        return """
        QPushButton {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(255, 255, 255, 0.95), stop:1 rgba(240, 240, 240, 0.95));
            border: 1.5px solid rgba(0, 0, 0, 0.12);
            border-radius: 18px; /* Vì size nút là 36x36 */
            color: #1A1A1A;
        }
        QPushButton:hover {
            background-color: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0078D4, stop:1 #005A9E);
            border: 1.5px solid rgba(0, 0, 0, 0.2);
            color: #FFFFFF;
        }
        """

def get_translation_popup_style(theme: str, font_size: int) -> str:
    """Trả về CSS cho hộp thoại dịch nổi Glassmorphism."""
    if theme == "dark":
        return f"""
        /* Khung chính của Popup */
        QWidget#PopupCard {{
            background-color: rgba(30, 30, 30, 0.88);
            border: 1.5px solid rgba(255, 255, 255, 0.12);
            border-radius: 16px;
        }}
        
        /* Nhãn tiêu đề ngôn ngữ & Mũi tên */
        QLabel#LangLabel, QLabel#ArrowLabel {{
            color: rgba(255, 255, 255, 0.7);
            font-size: 12px;
            font-weight: bold;
            font-family: 'Segoe UI', 'Outfit', sans-serif;
            background: transparent;
            margin: 0 4px;
        }}
        
        /* Ô nhập/hiển thị văn bản */
        QTextEdit {{
            background-color: rgba(45, 45, 45, 0.5);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 10px;
            color: #FFFFFF;
            font-size: {font_size}px;
            font-family: 'Segoe UI', sans-serif;
            padding: 8px;
        }}
        QTextEdit:focus {{
            border: 1px solid #0078D4;
        }}
        
        /* Khu vực nút chức năng ở dưới */
        QFrame#FooterFrame {{
            background: transparent;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
        }}
        
        /* Nút chức năng tròn hoặc bo góc (Copy, TTS, Close...) */
        QPushButton {{
            background-color: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 8px;
            color: #FFFFFF;
            font-family: 'Segoe UI', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif;
            font-size: 12px;
            font-weight: 500;
            padding: 6px 12px;
            min-height: 18px;
        }}
        QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.15);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}
        QPushButton:pressed {{
            background-color: rgba(255, 255, 255, 0.1);
        }}
        
        /* 3 nút điều hướng tiêu chuẩn Windows (Min, Max, Close) */
        QPushButton#MinBtn, QPushButton#MaxBtn, QPushButton#CloseBtn {{
            background-color: rgba(255, 255, 255, 0.05);
            border: 1.5px solid rgba(255, 255, 255, 0.25);
            color: #E0E0E0;
            font-family: 'Segoe MDL2 Assets';
            font-size: 9px;
            border-radius: 12px;
            padding: 0px;
        }}
        QPushButton#MinBtn:hover {{
            background-color: rgba(255, 255, 255, 0.15);
            border: 1.5px solid rgba(255, 255, 255, 0.4);
        }}
        QPushButton#MaxBtn:disabled {{
            background-color: rgba(255, 255, 255, 0.02);
            border: 1.5px solid rgba(255, 255, 255, 0.1);
            color: rgba(255, 255, 255, 0.2);
        }}
        QPushButton#CloseBtn:hover {{
            background-color: #E81123;
            border: 1.5px solid #E81123;
            color: #FFFFFF;
        }}
        
        /* Nút chức năng phụ (History, Api, Settings) dùng font icon Segoe MDL2 Assets */
        QPushButton#HistoryBtn, QPushButton#ApiBtn, QPushButton#SettingsBtn {{
            font-family: 'Segoe MDL2 Assets';
            font-size: 11px;
            padding: 0px;
        }}
        
        /* Tùy chỉnh thanh cuộn Scrollbar siêu thanh lịch */
        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 8px;
            margin: 4px 0 4px 0;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(255, 255, 255, 0.2);
            min-height: 20px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(255, 255, 255, 0.35);
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: transparent;
        }}
        
        /* Combobox tùy chọn ngôn ngữ trên Popup */
        QComboBox#PopSrcLangCombo, QComboBox#PopTgtLangCombo {{
            background-color: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 6px;
            color: #FFFFFF;
            padding: 2px 20px 2px 8px;
            font-size: 11px;
            font-family: 'Segoe UI', sans-serif;
            font-weight: 500;
            min-width: 90px;
            height: 22px;
        }}
        QComboBox#PopSrcLangCombo::drop-down, QComboBox#PopTgtLangCombo::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 16px;
            border-left: none;
        }}
        QComboBox#PopSrcLangCombo::down-arrow, QComboBox#PopTgtLangCombo::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid rgba(255, 255, 255, 0.7);
            width: 0;
            height: 0;
            margin-right: 6px;
        }}
        QComboBox#PopSrcLangCombo QAbstractItemView, QComboBox#PopTgtLangCombo QAbstractItemView {{
            background-color: #1e1e1e;
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 6px;
            color: #FFFFFF;
            selection-background-color: #0078D4;
            selection-color: #FFFFFF;
        }}
        """
    else:
        return f"""
        /* Khung chính của Popup */
        QWidget#PopupCard {{
            background-color: rgba(255, 255, 255, 0.90);
            border: 1.5px solid rgba(0, 0, 0, 0.08);
            border-radius: 16px;
        }}
        
        /* Nhãn tiêu đề ngôn ngữ & Mũi tên */
        QLabel#LangLabel, QLabel#ArrowLabel {{
            color: rgba(0, 0, 0, 0.7);
            font-size: 12px;
            font-weight: bold;
            font-family: 'Segoe UI', 'Outfit', sans-serif;
            background: transparent;
            margin: 0 4px;
        }}
        
        /* Ô nhập/hiển thị văn bản */
        QTextEdit {{
            background-color: rgba(245, 245, 245, 0.6);
            border: 1px solid rgba(0, 0, 0, 0.06);
            border-radius: 10px;
            color: #1A1A1A;
            font-size: {font_size}px;
            font-family: 'Segoe UI', sans-serif;
            padding: 8px;
        }}
        QTextEdit:focus {{
            border: 1px solid #0078D4;
        }}
        
        /* Khu vực nút chức năng ở dưới */
        QFrame#FooterFrame {{
            background: transparent;
            border-top: 1px solid rgba(0, 0, 0, 0.06);
        }}
        
        /* Nút chức năng tròn hoặc bo góc (Copy, TTS, Close...) */
        QPushButton {{
            background-color: rgba(0, 0, 0, 0.04);
            border: 1px solid rgba(0, 0, 0, 0.08);
            border-radius: 8px;
            color: #1A1A1A;
            font-family: 'Segoe UI', 'Segoe UI Emoji', 'Segoe UI Symbol', sans-serif;
            font-size: 12px;
            font-weight: 500;
            padding: 6px 12px;
            min-height: 18px;
        }}
        QPushButton:hover {{
            background-color: rgba(0, 0, 0, 0.08);
            border: 1px solid rgba(0, 0, 0, 0.15);
        }}
        QPushButton:pressed {{
            background-color: rgba(0, 0, 0, 0.12);
        }}
        
        /* 3 nút điều hướng tiêu chuẩn Windows (Min, Max, Close) */
        QPushButton#MinBtn, QPushButton#MaxBtn, QPushButton#CloseBtn {{
            background-color: rgba(0, 0, 0, 0.03);
            border: 1.5px solid rgba(0, 0, 0, 0.18);
            color: #333333;
            font-family: 'Segoe MDL2 Assets';
            font-size: 9px;
            border-radius: 12px;
            padding: 0px;
        }}
        QPushButton#MinBtn:hover {{
            background-color: rgba(0, 0, 0, 0.08);
            border: 1.5px solid rgba(0, 0, 0, 0.3);
        }}
        QPushButton#MaxBtn:disabled {{
            background-color: rgba(0, 0, 0, 0.01);
            border: 1.5px solid rgba(0, 0, 0, 0.08);
            color: rgba(0, 0, 0, 0.25);
        }}
        QPushButton#CloseBtn:hover {{
            background-color: #E81123;
            border: 1.5px solid #E81123;
            color: #FFFFFF;
        }}
        
        /* Nút chức năng phụ (History, Api, Settings) dùng font icon Segoe MDL2 Assets */
        QPushButton#HistoryBtn, QPushButton#ApiBtn, QPushButton#SettingsBtn {{
            font-family: 'Segoe MDL2 Assets';
            font-size: 11px;
            padding: 0px;
        }}
        
        /* Tùy chỉnh thanh cuộn Scrollbar siêu thanh lịch */
        QScrollBar:vertical {{
            border: none;
            background: transparent;
            width: 8px;
            margin: 4px 0 4px 0;
        }}
        QScrollBar::handle:vertical {{
            background: rgba(0, 0, 0, 0.15);
            min-height: 20px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: rgba(0, 0, 0, 0.25);
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            border: none;
            background: transparent;
        }}
        
        /* Combobox tùy chọn ngôn ngữ trên Popup */
        QComboBox#PopSrcLangCombo, QComboBox#PopTgtLangCombo {{
            background-color: rgba(0, 0, 0, 0.05);
            border: 1px solid rgba(0, 0, 0, 0.1);
            border-radius: 6px;
            color: #1A1A1A;
            padding: 2px 20px 2px 8px;
            font-size: 11px;
            font-family: 'Segoe UI', sans-serif;
            font-weight: 500;
            min-width: 90px;
            height: 22px;
        }}
        QComboBox#PopSrcLangCombo::drop-down, QComboBox#PopTgtLangCombo::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 16px;
            border-left: none;
        }}
        QComboBox#PopSrcLangCombo::down-arrow, QComboBox#PopTgtLangCombo::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 4px solid rgba(0, 0, 0, 0.6);
            width: 0;
            height: 0;
            margin-right: 6px;
        }}
        QComboBox#PopSrcLangCombo QAbstractItemView, QComboBox#PopTgtLangCombo QAbstractItemView {{
            background-color: #FFFFFF;
            border: 1px solid rgba(0, 0, 0, 0.15);
            border-radius: 6px;
            color: #1A1A1A;
            selection-background-color: #0078D4;
            selection-color: #FFFFFF;
        }}
        """

def get_settings_window_style(theme: str) -> str:
    """Trả về CSS cho cửa sổ Dashboard cài đặt chính."""
    # Sẽ được xây dựng sau ở nhánh Settings UI
    return ""
