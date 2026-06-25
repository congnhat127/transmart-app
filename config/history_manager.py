import os
import json
import time

# Đường dẫn gốc dự án và đường dẫn file lưu lịch sử dịch thuật
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HISTORY_PATH = os.path.join(ROOT_DIR, "storage", "history.json")

class HistoryManager:
    """Quản lý lưu trữ lịch sử dịch thuật dưới dạng JSON cục bộ."""
    def __init__(self):
        self.history = []
        self.load_history()

    def load_history(self) -> list:
        """Đọc lịch sử dịch từ file history.json."""
        try:
            if os.path.exists(HISTORY_PATH):
                with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                    self.history = json.load(f)
            else:
                self.history = []
        except Exception as e:
            print(f"[History] Lỗi đọc lịch sử: {e}")
            self.history = []
        return self.history

    def add_record(self, source: str, translation: str, explanation: str, detected_lang: str, target_lang: str = "Vietnamese", summary: str = "") -> bool:
        """
        Thêm một bản ghi dịch thuật mới vào lịch sử.
        Bản ghi mới sẽ được đưa lên đầu danh sách để dễ theo dõi.
        """
        if not source.strip():
            return False
            
        record = {
            "source": source.strip(),
            "translation": translation.strip(),
            "explanation": explanation.strip(),
            "summary": summary.strip(),
            "detected_lang": detected_lang,
            "target_lang": target_lang.strip(),
            "timestamp": time.time()
        }
        
        # Đưa lên đầu danh sách
        self.history.insert(0, record)
        
        # Giới hạn tối đa 500 bản ghi để tránh tệp tin phình to quá mức
        if len(self.history) > 500:
            self.history = self.history[:500]
            
        return self.save_history()

    def find_cached_record(self, source: str, target_lang: str) -> dict:
        """Tìm bản ghi dịch thuật trùng khớp trong lịch sử để sử dụng làm bộ nhớ đệm (Cache)."""
        src_clean = source.strip().lower()
        tgt_clean = target_lang.strip().lower()
        for record in self.history:
            # So khớp cả văn bản gốc và ngôn ngữ đích mong muốn
            if record.get("source", "").lower() == src_clean and record.get("target_lang", "vietnamese").lower() == tgt_clean:
                return record
        return None

    def delete_record(self, index: int) -> bool:
        """Xóa một bản ghi dịch thuật theo chỉ mục."""
        try:
            if 0 <= index < len(self.history):
                self.history.pop(index)
                return self.save_history()
        except Exception as e:
            print(f"[History] Lỗi xóa bản ghi: {e}")
        return False

    def clear_all(self) -> bool:
        """Xóa sạch toàn bộ lịch sử dịch thuật."""
        self.history = []
        return self.save_history()

    def save_history(self) -> bool:
        """Ghi danh sách lịch sử dịch thuật hiện tại xuống file json."""
        try:
            os.makedirs(os.path.dirname(HISTORY_PATH), exist_ok=True)
            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[History] Lỗi lưu lịch sử: {e}")
            return False

# Khởi tạo đối tượng quản lý lịch sử toàn cục
history_manager = HistoryManager()
