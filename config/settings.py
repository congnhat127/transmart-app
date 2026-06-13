import os
import json
from config.constants import DEFAULT_SETTINGS

# Đường dẫn tới thư mục gốc và file config
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(ROOT_DIR, "storage", "config.json")

class SettingsManager:
    def __init__(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.load_settings()

    def load_settings(self) -> dict:
        """Đọc cấu hình từ file config.json. Nếu không tồn tại hoặc lỗi, sử dụng mặc định."""
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    user_settings = json.load(f)
                    # Ghi đè cấu hình mặc định bằng cấu hình của người dùng để tránh thiếu trường
                    for key, val in user_settings.items():
                        if key in self.settings:
                            self.settings[key] = val
            else:
                self.save_settings()
        except Exception as e:
            print(f"Lỗi khi đọc file cấu hình: {e}")
        return self.settings

    def save_settings(self, new_settings: dict = None) -> bool:
        """Lưu cấu hình xuống file config.json."""
        if new_settings:
            self.settings.update(new_settings)
        try:
            # Đảm bảo thư mục storage tồn tại
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Lỗi khi lưu file cấu hình: {e}")
            return False

    def get(self, key, default=None):
        """Lấy giá trị của một thuộc tính cấu hình."""
        return self.settings.get(key, default)

    def set(self, key, value) -> bool:
        """Gán giá trị cho một thuộc tính và lưu lại."""
        self.settings[key] = value
        return self.save_settings()

# Tạo một instance toàn cục để các module khác dễ dàng sử dụng
settings_manager = SettingsManager()
