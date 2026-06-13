# Tên và phiên bản ứng dụng
APP_NAME = "TransMart"
APP_VERSION = "1.0.0"

# Danh sách ngôn ngữ hỗ trợ
SUPPORTED_LANGUAGES = {
    "Auto": "Phát hiện ngôn ngữ",
    "Vietnamese": "Tiếng Việt",
    "English": "Tiếng Anh",
    "Japanese": "Tiếng Nhật",
    "Korean": "Tiếng Hàn",
    "Chinese": "Tiếng Trung",
    "French": "Tiếng Pháp",
    "German": "Tiếng Đức",
    "Russian": "Tiếng Nga",
    "Spanish": "Tiếng Tây Ban Nha"
}

# Cấu hình mặc định
DEFAULT_SETTINGS = {
    "api_key": "",
    "provider": "gemini",
    "gemini_model": "gemini-1.5-flash",
    "openai_model": "gpt-4o-mini",
    "openai_base_url": "https://api.openai.com/v1",
    "source_lang": "Auto",
    "target_lang": "Vietnamese",
    "hotkey": "alt+d",
    "ocr_hotkey": "alt+q",
    "show_pop_icon": true,
    "theme": "dark",
    "font_size": 13
}

# Định nghĩa bảng màu UI (CSS/QSS)
# Dark Mode (Sleek Dark HSL/RGBA)
DARK_THEME = {
    "window_bg": "rgba(30, 30, 30, 0.85)",        # Thủy tinh mờ (Glassmorphism)
    "card_bg": "rgba(45, 45, 45, 0.9)",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B0B0B0",
    "accent_color": "#0078D4",                    # Xanh dương Microsoft nổi bật
    "accent_hover": "#0086F0",
    "border_color": "rgba(255, 255, 255, 0.15)",
    "shadow_color": "rgba(0, 0, 0, 0.5)"
}

# Light Mode
LIGHT_THEME = {
    "window_bg": "rgba(255, 255, 255, 0.9)",
    "card_bg": "rgba(240, 240, 240, 0.95)",
    "text_primary": "#1A1A1A",
    "text_secondary": "#5F5F5F",
    "accent_color": "#0078D4",
    "accent_hover": "#0086F0",
    "border_color": "rgba(0, 0, 0, 0.1)",
    "shadow_color": "rgba(0, 0, 0, 0.15)"
}
