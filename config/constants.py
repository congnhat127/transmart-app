# Tên và phiên bản ứng dụng
APP_NAME = "TransMart"
APP_VERSION = "1.0.0"

# Danh sách ngôn ngữ hỗ trợ (Mã ngôn ngữ -> Tên hiển thị)
SUPPORTED_LANGUAGES = {
    "Auto": "Tự động phát hiện",
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

# Cấu hình mặc định của ứng dụng
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
    "show_pop_icon": True,
    "theme": "dark",
    "font_size": 13
}

# Bảng màu cho Theme tối (Dark Theme) - Kiểu Sleek Acrylic / HSL
DARK_THEME = {
    "window_bg": "rgba(30, 30, 30, 0.92)",
    "card_bg": "rgba(45, 45, 45, 0.95)",
    "text_primary": "#FFFFFF",
    "text_secondary": "#B0B0B0",
    "accent_color": "#0078D4",
    "accent_hover": "#0086F0",
    "border_color": "rgba(255, 255, 255, 0.12)",
    "shadow_color": "rgba(0, 0, 0, 0.5)"
}

# Bảng màu cho Theme sáng (Light Theme)
LIGHT_THEME = {
    "window_bg": "rgba(255, 255, 255, 0.95)",
    "card_bg": "rgba(242, 242, 242, 0.98)",
    "text_primary": "#1A1A1A",
    "text_secondary": "#5F5F5F",
    "accent_color": "#0078D4",
    "accent_hover": "#0086F0",
    "border_color": "rgba(0, 0, 0, 0.10)",
    "shadow_color": "rgba(0, 0, 0, 0.15)"
}
