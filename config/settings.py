import os
import json
from config.constants import DEFAULT_SETTINGS

# Đường dẫn gốc dự án và đường dẫn file lưu cấu hình
import sys
if hasattr(sys, 'frozen'):
    # Khi chạy file đóng gói, lưu vào AppData/Local/TransMart để đảm bảo quyền ghi và bảo toàn khi update app
    ROOT_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "TransMart")
else:
    # Khi dev, lưu trực tiếp tại thư mục dự án cho dễ debug
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONFIG_PATH = os.path.join(ROOT_DIR, "storage", "config.json")

class SettingsManager:
    """Quản lý đọc và ghi các cài đặt cấu hình cục bộ của ứng dụng."""
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.load_settings()

    def load_settings(self) -> dict:
        """Đọc file cấu hình config.json. Nếu không tồn tại hoặc lỗi, sử dụng mặc định."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    user_settings = json.load(f)
                    
                    # Cập nhật các giá trị cấu hình, giữ lại giá trị mặc định nếu cấu hình thiếu trường
                    for key, val in user_settings.items():
                        if key in self.settings:
                            self.settings[key] = val
            else:
                # Nếu chưa có file config, tiến hành tự tạo mới bằng cấu hình mặc định
                self.save_settings()
        except Exception as e:
            print(f"[Settings] Lỗi đọc cấu hình: {e}")
        return self.settings

    def save_settings(self, new_settings: dict = None) -> bool:
        """Lưu toàn bộ hoặc một phần cấu hình mới xuống file config.json."""
        if new_settings:
            self.settings.update(new_settings)
            # Log cụ thể các giá trị quan trọng để người dùng dễ kiểm chứng trên Terminal
            g_key = new_settings.get("gemini_api_key")
            o_key = new_settings.get("openai_api_key")
            prov = new_settings.get("provider")
            if prov is not None:
                print(f"[Cấu hình] Đã chuyển nhà cung cấp dịch vụ AI sang: {prov}")
            if g_key is not None:
                g_show = f"{g_key[:6]}...{g_key[-4:]}" if len(g_key) > 10 else ("trống" if not g_key else g_key)
                print(f"[Cấu hình] Lưu Gemini API Key mới: {g_show}")
            if o_key is not None:
                o_show = f"{o_key[:6]}...{o_key[-4:]}" if len(o_key) > 10 else ("trống" if not o_key else o_key)
                print(f"[Cấu hình] Lưu OpenAI API Key mới: {o_show}")
        try:
            # Tạo thư mục chứa file cấu hình nếu chưa tồn tại (ví dụ: storage)
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[Settings] Lỗi lưu cấu hình: {e}")
            return False

    def get(self, key: str, default=None):
        """Lấy giá trị của một cài đặt."""
        return self.settings.get(key, default)

    def set(self, key: str, value) -> bool:
        """Thay đổi giá trị của một cài đặt và lưu ngay lập tức."""
        self.settings[key] = value
        return self.save_settings()

# Tạo đối tượng quản lý cấu hình toàn cục
settings_manager = SettingsManager()
