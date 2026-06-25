import os
import sys
import asyncio
import tempfile
import uuid
import edge_tts
from PyQt6.QtCore import QThread, pyqtSignal, QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput

is_windows = sys.platform == "win32"
if is_windows:
    import ctypes

# Bản đồ ánh xạ mã ngôn ngữ sang giọng đọc tương ứng của Microsoft Edge TTS
VOICE_MAPPING = {
    "vi": "vi-VN-HoaiMyNeural",
    "en": "en-US-EmmaMultilingualNeural",
    "ja": "ja-JP-NanamiNeural",
    "ko": "ko-KR-SunHiNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "es": "es-ES-ElviraNeural",
    "ru": "ru-RU-SvetlanaNeural"
}

class TTSDownloadThread(QThread):
    """Luồng chạy ngầm để tải âm thanh từ Edge TTS, không gây treo giao diện (GUI Freeze)."""
    download_finished = pyqtSignal(str)  # Phát ra đường dẫn tệp âm thanh mp3 tạm thời
    download_failed = pyqtSignal(str)

    def __init__(self, text: str, voice: str):
        super().__init__()
        self.text = text
        self.voice = voice

    def run(self):
        try:
            # Tạo đường dẫn tệp tạm thời trong hệ thống
            temp_dir = tempfile.gettempdir()
            # Đặt tên tệp hoàn toàn ngẫu nhiên bằng UUID để tránh bị tranh chấp hoặc lock tệp bởi media engine
            temp_file_path = os.path.join(temp_dir, f"transmart_tts_{uuid.uuid4().hex}.mp3")
            
            # Khởi tạo tiến trình tải edge-tts
            communicate = edge_tts.Communicate(self.text, self.voice)
            
            # Do QThread có Event Loop riêng biệt nên ta khởi tạo một Event Loop mới của asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(communicate.save(temp_file_path))
            loop.close()
            
            self.download_finished.emit(temp_file_path)
        except Exception as e:
            self.download_failed.emit(str(e))

class TTSService:
    """Xử lý chuyển đổi văn bản thành giọng nói (Text-to-Speech) bằng Edge TTS và phát âm thanh."""
    def __init__(self):
        self.player = QMediaPlayer()
        # Khởi tạo QAudioOutput với player làm cha để tránh bị GC thu hồi
        self.audio_output = QAudioOutput(self.player)
        self.player.setAudioOutput(self.audio_output)
        self.audio_output.setVolume(1.0)  # Âm lượng tối đa (0.0 -> 1.0)
        self.thread = None
        self.current_file_path = None

    def speak(self, text: str, language_code: str):
        """Phát âm đoạn văn bản bằng giọng nói tương thích ngôn ngữ."""
        if not text.strip():
            return
            
        # Dừng phát luồng hiện tại trước
        self.stop()
        
        # Chuẩn hóa mã ngôn ngữ (ví dụ: 'en-US' -> 'en', 'vi-VN' -> 'vi')
        lang = (language_code or "en").lower().split("-")[0]
        voice = VOICE_MAPPING.get(lang, VOICE_MAPPING["en"])
        
        # Nếu đang có luồng tải âm thanh chạy trước đó thì dừng lại
        if self.thread and self.thread.isRunning():
            self.thread.terminate()
            self.thread.wait()
            
        # Khởi chạy luồng mới
        self.thread = TTSDownloadThread(text, voice)
        self.thread.download_finished.connect(self._play_audio)
        self.thread.download_failed.connect(lambda err: print(f"[TTS] Lỗi tải giọng đọc: {err}"))
        self.thread.start()

    def _play_audio(self, file_path: str):
        """Nạp tệp mp3 và phát âm thanh qua QMediaPlayer."""
        if not os.path.exists(file_path):
            return

        try:
            self.player.stop()
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.player.play()
            
            # Dọn dẹp tệp tạm của lần phát trước đó
            if self.current_file_path and self.current_file_path != file_path:
                try:
                    if os.path.exists(self.current_file_path):
                        os.remove(self.current_file_path)
                except Exception as clean_err:
                    print(f"[TTS] Lỗi dọn dẹp tệp tạm: {clean_err}")
                    
            self.current_file_path = file_path
        except Exception as e:
            print(f"[TTS] Lỗi phát âm qua QMediaPlayer: {e}")

    def stop(self):
        """Dừng phát âm thanh."""
        self.player.stop()
