# Định nghĩa QSS (Qt Style Sheets) cho giao diện Glassmorphism & Sleek Dark/Light

def get_pop_icon_style(theme: str = "dark") -> str:
    """Style sheet cho nút tròn nhỏ xuất hiện dưới con trỏ chuột."""
    if theme == "dark":
        bg = "rgba(45, 45, 45, 0.95)"
        border = "1px solid rgba(255, 255, 255, 0.2)"
        hover_bg = "rgba(0, 120, 212, 0.9)"
        shadow = "rgba(0, 0, 0, 0.4)"
    else:
        bg = "rgba(255, 255, 255, 0.95)"
        border = "1px solid rgba(0, 0, 0, 0.15)"
        hover_bg = "rgba(0, 120, 212, 0.95)"
        shadow = "rgba(0, 0, 0, 0.15)"

    return f"""
        QPushButton {{
            background-color: {bg};
            border: {border};
            border-radius: 20px;
            padding: 8px;
        }}
        QPushButton:hover {{
            background-color: {hover_bg};
            border-color: #0078D4;
        }}
    """

def get_translation_popup_style(theme: str = "dark", font_size: int = 13) -> str:
    """Style sheet cho cửa sổ hiển thị bản dịch."""
    if theme == "dark":
        window_bg = "rgba(28, 28, 28, 0.92)"
        border = "1px solid rgba(255, 255, 255, 0.12)"
        text_primary = "#FFFFFF"
        text_secondary = "#B0B0B0"
        tab_bg = "rgba(40, 40, 40, 0.6)"
        tab_active_bg = "rgba(60, 60, 60, 0.9)"
        btn_bg = "rgba(50, 50, 50, 0.8)"
        btn_hover = "rgba(70, 70, 70, 0.9)"
    else:
        window_bg = "rgba(255, 255, 255, 0.95)"
        border = "1px solid rgba(0, 0, 0, 0.12)"
        text_primary = "#1A1A1A"
        text_secondary = "#606060"
        tab_bg = "rgba(240, 240, 240, 0.8)"
        tab_active_bg = "rgba(255, 255, 255, 0.95)"
        btn_bg = "rgba(230, 230, 230, 0.8)"
        btn_hover = "rgba(210, 210, 210, 0.9)"

    return f"""
        QWidget#MainWindow {{
            background-color: {window_bg};
            border: {border};
            border-radius: 12px;
        }}
        
        QLabel#TitleLabel {{
            color: #0078D4;
            font-weight: bold;
            font-size: {font_size + 2}px;
        }}
        
        QLabel#LangLabel {{
            color: {text_secondary};
            font-size: {font_size - 1}px;
            font-weight: 500;
        }}
        
        QTextBrowser {{
            background-color: transparent;
            border: none;
            color: {text_primary};
            font-size: {font_size}px;
            line-height: 1.4;
        }}
        
        /* Cấu hình Tabs */
        QTabWidget::pane {{
            border: none;
            background-color: transparent;
        }}
        
        QTabBar::tab {{
            background: {tab_bg};
            color: {text_secondary};
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            padding: 6px 12px;
            margin-right: 4px;
            font-size: {font_size - 1}px;
            font-weight: 500;
        }}
        
        QTabBar::tab:selected {{
            background: {tab_active_bg};
            color: {text_primary};
            border-bottom: 2px solid #0078D4;
        }}
        
        QTabBar::tab:hover {{
            background: {btn_hover};
            color: {text_primary};
        }}

        /* Buttons chung */
        QPushButton {{
            background-color: {btn_bg};
            border: none;
            border-radius: 6px;
            padding: 5px 10px;
            color: {text_primary};
            font-size: {font_size - 1}px;
        }}
        
        QPushButton:hover {{
            background-color: {btn_hover};
        }}

        QPushButton#SpeakBtn {{
            background-color: #0078D4;
            color: white;
            border-radius: 15px;
            width: 30px;
            height: 30px;
            padding: 0px;
        }}
        
        QPushButton#SpeakBtn:hover {{
            background-color: #0086F0;
        }}
    """

def get_settings_window_style(theme: str = "dark") -> str:
    """Style sheet cho Dashboard cài đặt chính."""
    if theme == "dark":
        bg = "#1E1E1E"
        border = "1px solid #2D2D2D"
        card_bg = "#252526"
        text_primary = "#F5F5F5"
        text_secondary = "#CCCCCC"
        input_bg = "#3C3C3C"
        input_border = "1px solid #555555"
        btn_primary = "#0078D4"
        btn_primary_hover = "#0086F0"
    else:
        bg = "#F3F3F3"
        border = "1px solid #E0E0E0"
        card_bg = "#FFFFFF"
        text_primary = "#202020"
        text_secondary = "#616161"
        input_bg = "#FFFFFF"
        input_border = "1px solid #D0D0D0"
        btn_primary = "#0078D4"
        btn_primary_hover = "#0086F0"

    return f"""
        QWidget#SettingsWindow {{
            background-color: {bg};
            color: {text_primary};
            font-family: 'Segoe UI', Arial, sans-serif;
        }}
        
        QGroupBox {{
            background-color: {card_bg};
            border: {border};
            border-radius: 8px;
            margin-top: 15px;
            padding: 15px;
            font-weight: bold;
            color: #0078D4;
        }}
        
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            left: 10px;
            padding: 0 5px;
        }}
        
        QLabel {{
            color: {text_primary};
            font-size: 13px;
        }}
        
        QLabel#DescriptionLabel {{
            color: {text_secondary};
            font-size: 12px;
        }}
        
        QLineEdit, QComboBox {{
            background-color: {input_bg};
            border: {input_border};
            border-radius: 4px;
            padding: 6px 10px;
            color: {text_primary};
            font-size: 13px;
        }}
        
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid #0078D4;
        }}
        
        QPushButton#SaveBtn {{
            background-color: {btn_primary};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 20px;
            font-weight: bold;
            font-size: 13px;
        }}
        
        QPushButton#SaveBtn:hover {{
            background-color: {btn_primary_hover};
        }}
        
        QCheckBox {{
            spacing: 8px;
            font-size: 13px;
            color: {text_primary};
        }}
    """
