import sys
import os
from PyQt6.QtWidgets import QApplication

import signal
from PyQt6.QtCore import QTimer

# Thêm đường dẫn thư mục gốc vào python path để tránh lỗi import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.listener import SystemListener

def on_translation_triggered(text):
    print(f"\n[HOTKEY TEST] Nhấn Alt+Z thành công!")
    print(f"-> Văn bản thu được: '{text}'")

def on_ocr_triggered():
    print(f"\n[HOTKEY TEST] Nhấn Alt+Q thành công! Yêu cầu mở màn hình chụp ảnh OCR.")

def on_text_selected(text, x, y):
    print(f"\n[MOUSE TEST] Người dùng vừa bôi đen xong chữ!")
    print(f"-> Văn bản: '{text}'")
    print(f"-> Nhả chuột tại tọa độ: (x={x}, y={y})")

def sigint_handler(*args):
    """Hàm xử lý khi nhận tín hiệu ngắt Ctrl+C từ hệ thống."""
    print("\n[Hệ thống] Nhận lệnh dừng chương trình (Ctrl+C). Đang dọn dẹp...")
    QApplication.quit()

def main():
    # Cấu hình xử lý tín hiệu Ctrl+C cấp hệ thống
    signal.signal(signal.SIGINT, sigint_handler)

    # Khởi tạo ứng dụng Qt bắt buộc
    app = QApplication(sys.argv)
    print("=== TransMart Core Test ===")
    print("Ứng dụng đang chạy ẩn...")
    print("Vui lòng thử thực hiện:")
    print("1. Ấn tổ hợp phím Alt + Z khi đang bôi đen chữ bất kỳ.")
    print("2. Ấn tổ hợp phím Alt + Q.")
    print("3. Dùng chuột trái kéo bôi đen một đoạn văn bản ở bất kỳ đâu rồi nhả ra.")
    print("Nhấn Ctrl + C tại Terminal này để dừng chương trình.")
    print("==========================")

    # Dùng QTimer chạy tuần hoàn để hệ điều hành có cơ hội truyền tín hiệu Ctrl+C cho Python
    timer = QTimer()
    timer.start(200)  # Chạy dummy function mỗi 200ms
    timer.timeout.connect(lambda: None)

    # 1. Khởi tạo đối tượng lắng nghe hệ thống
    listener = SystemListener()
    
    # 2. Kết nối các tín hiệu (Signals) tới các hàm in kiểm tra (Slots)
    listener.trigger_translation.connect(on_translation_triggered)
    listener.trigger_ocr.connect(on_ocr_triggered)
    listener.text_selected.connect(on_text_selected)
    
    # 3. Bắt đầu lắng nghe sự kiện hệ thống
    listener.start(hotkey="alt+z", ocr_hotkey="alt+q")

    # Chạy vòng lặp sự kiện của PyQt6
    exit_code = app.exec()
    
    # Dọn dẹp tài nguyên lắng nghe trước khi thoát hoàn toàn
    listener.stop()
    print("Đã dừng chương trình kiểm thử.")
    os._exit(exit_code)


if __name__ == "__main__":
    main()
