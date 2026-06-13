import os
import asyncio
import threading
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from PyQt6.QtCore import QUrl, QObject
from config.settings import ROOT_DIR

class TTSService(QObject):
    def __init__(self):
        super().__init__()
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        
        # Thư mục lưu file âm thanh tạm thời
        self.temp_dir = os.path.join(ROOT_DIR, "storage")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.temp_audio_path = os.path.join(self.temp_dir, "temp_tts.mp3")
        
        # Map mã ngôn ngữ tương ứng giọng đọc của Edge TTS
        self.voice_map = {
            "Vietnamese": "vi-VN-HoaiMyNeural",
            "English": "en-US-AriaNeural",
            "Japanese": "ja-JP-NanamiNeural",
            "Korean": "ko-KR-SunHiNeural",
            "Chinese": "zh-CN-XiaoxiaoNeural",
            "French": "fr-FR-DeniseNeural",
            "German": "de-DE-AmalaNeural",
            "Russian": "ru-RU-SvetlanaNeural",
            "Spanish": "es-ES-ElviraNeural"
        }

    def speak(self, text: str, language: str):
        """Phát âm văn bản bằng cách chạy một thread riêng để tránh làm treo giao diện."""
        threading.Thread(target=self._generate_and_play, args=(text, language), daemon=True).start()

    def _generate_and_play(self, text: str, language: str):
        try:
            # Chọn giọng đọc tương ứng. Mặc định là tiếng Anh nếu không map được
            voice = self.voice_map.get(language, "en-US-AriaNeural")
            
            # Khởi tạo tiến trình async của edge-tts
            import edge_tts
            
            communicate = edge_tts.Communicate(text, voice)
            
            # Đảm bảo vòng lặp sự kiện async hoạt động chính xác trong thread mới
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(communicate.save(self.temp_audio_path))
            loop.close()
            
            # Phát file âm thanh đã lưu thông qua QMediaPlayer của PyQt6
            # Cần chạy trên thread chính của Qt hoặc gọi trực tiếp vì QMediaPlayer là bất đồng bộ
            url = QUrl.fromLocalFile(self.temp_audio_path)
            self.player.setSource(url)
            self.player.play()
            
        except Exception as e:
            print(f"[TTS] Lỗi phát âm văn bản: {e}")

# Instance toàn cục của TTSService
tts_service = TTSService()
