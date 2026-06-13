# TransMart - Smart Translator Desktop App

Ứng dụng dịch thuật thông minh chạy ngầm trên Windows. Cho phép người dùng bôi đen văn bản ở bất kỳ đâu (Word, Excel, Chrome, Edge, Slack, v.v.) và bấm phím tắt để hiển thị bản dịch từ AI (Gemini/OpenAI) kèm theo các giải nghĩa chi tiết và phát âm (TTS).

---

## ✨ Tính năng chính

1. **Dịch nhanh toàn hệ thống (Global Hotkey)**: Bôi đen văn bản và nhấn phím tắt (mặc định: `Alt + D` hoặc `Ctrl + Shift + D`) để dịch ngay lập tức.
2. **Icon nổi thông minh (Smart Pop-up Icon)**: Xuất hiện nút tròn nhỏ dưới con trỏ chuột ngay sau khi bôi đen văn bản, bấm vào để dịch mà không cần phím tắt.
3. **Dịch thuật bằng AI**: Sử dụng Gemini API (hoặc OpenAI/DeepSeek) để dịch chuẩn ngữ cảnh, giải nghĩa từ vựng chuyên ngành, giải thích ngữ pháp.
4. **Phát âm AI (Edge TTS)**: Nghe giọng đọc tự nhiên bằng nhiều ngôn ngữ từ dịch vụ Edge Text-To-Speech.
5. **Chụp vùng màn hình & OCR**: Khi văn bản bị chặn sao chép (ví dụ: file PDF bảo mật, ảnh, game, app bảo mật), người dùng có thể quét vùng màn hình để dịch bằng OCR.
6. **Giao diện hiện đại (Glassmorphism & Dark Mode)**: Thiết kế PyQt6 bo góc, đổ bóng, màu sắc hài hòa và hỗ trợ chế độ tối (Dark Mode).

---

## 📂 Cấu trúc thư mục dự án

Xem chi tiết trong [Kế hoạch triển khai](.gemini/antigravity/brain/65028a3b-ba84-4496-a649-59d642ed0322/artifacts/implementation_plan.md).

```
smart-translator-app/
│
├── .gitignore               # Chặn các file rác và cấu hình chứa API Key
├── README.md                # Tài liệu hướng dẫn cài đặt và sử dụng
├── requirements.txt         # Các thư viện Python cần cài đặt
├── main.py                  # File khởi chạy ứng dụng (Entrypoint)
│
├── config/                  # Quản lý cấu hình
│   ├── __init__.py
│   ├── settings.py          # Logic đọc/ghi cài đặt từ storage
│   └── constants.py         # Các hằng số hệ thống (Màu sắc, phím tắt)
│
├── core/                    # Hệ thống chạy ngầm can thiệp OS
│   ├── __init__.py
│   ├── listener.py          # Lắng nghe sự kiện bàn phím/chuột toàn hệ thống
│   ├── clipboard_manager.py # Giả lập Ctrl+C, đọc bộ nhớ đệm
│   └── ocr_engine.py        # Module quét ảnh màn hình khi bị chặn copy
│
├── services/                # Kết nối dịch vụ AI & TTS
│   ├── __init__.py
│   ├── ai_service.py        # Gọi API Gemini/OpenAI (Ép xuất JSON chuẩn)
│   └── tts_service.py       # Xử lý phát âm (Edge TTS)
│
├── storage/                 # Nơi lưu trữ cục bộ
│   ├── config.json.example  # File mẫu cấu hình để hướng dẫn
│   └── config.json          # File thật (Bị Git chặn, chứa API Key cá nhân)
│
└── ui/                      # Giao diện người dùng PyQt6
    ├── __init__.py
    ├── pop_icon.py          # Icon tròn nhỏ xuất hiện dưới con trỏ chuột khi bôi đen
    ├── pop_translation.py   # Ô dịch thông minh hiển thị kết quả từ AI
    ├── settings_window.py   # Giao diện Dashboard cấu hình ứng dụng
    └── resources/           # Icon, hình ảnh, file QSS stylesheet
```

---

## 🛠️ Hướng dẫn cài đặt & Khởi chạy

### 1. Chuẩn bị môi trường
Yêu cầu máy tính chạy **Windows 10/11** và đã cài đặt **Python 3.8+**.

### 2. Cài đặt các thư viện cần thiết
Mở Command Prompt hoặc PowerShell tại thư mục dự án và chạy lệnh:
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Cấu hình API Key
1. Copy file `storage/config.json.example` thành `storage/config.json`.
2. Mở file `storage/config.json` và điền Gemini API Key của bạn:
   ```json
   {
       "api_key": "YOUR_GEMINI_API_KEY_HERE",
       "provider": "gemini",
       "source_lang": "Auto",
       "target_lang": "Vietnamese",
       "hotkey": "alt+d",
       "theme": "dark"
   }
   ```

### 4. Chạy ứng dụng
```bash
python main.py
```
Ứng dụng sẽ xuất hiện dưới dạng một Icon khay hệ thống (System Tray Icon) ở góc phải màn hình.
