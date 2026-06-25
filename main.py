import sys
import os
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

# Thêm đường dẫn thư mục gốc vào python path để tránh lỗi import
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.app_controller import TransMartApp

def create_shortcuts():
    """Tự động tạo phím tắt ngoài Desktop và Start Menu khi chạy file build (.exe)."""
    import sys
    import os
    import subprocess
    
    # Chỉ tạo shortcut khi chạy bản đóng gói (.exe)
    if not hasattr(sys, 'frozen'):
        return
        
    exe_path = os.path.abspath(sys.executable)
    working_dir = os.path.dirname(exe_path)
    app_name = "TransMart"
    
    desktop_dir = os.path.expandvars(r"%USERPROFILE%\Desktop")
    start_menu_dir = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs")
    
    desktop_shortcut = os.path.join(desktop_dir, f"{app_name}.lnk")
    start_menu_shortcut = os.path.join(start_menu_dir, f"{app_name}.lnk")
    
    # Nếu đã tồn tại cả hai shortcut thì không cần tạo lại
    if os.path.exists(desktop_shortcut) and os.path.exists(start_menu_shortcut):
        return
        
    # Tạo PowerShell Script sinh shortcut thông qua COM
    ps_script = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    
    if (-not (Test-Path "{desktop_shortcut}")) {{
        $Shortcut = $WshShell.CreateShortcut("{desktop_shortcut}")
        $Shortcut.TargetPath = "{exe_path}"
        $Shortcut.WorkingDirectory = "{working_dir}"
        $Shortcut.IconLocation = "{exe_path},0"
        $Shortcut.Save()
    }}
    
    if (-not (Test-Path "{start_menu_shortcut}")) {{
        $Shortcut = $WshShell.CreateShortcut("{start_menu_shortcut}")
        $Shortcut.TargetPath = "{exe_path}"
        $Shortcut.WorkingDirectory = "{working_dir}"
        $Shortcut.IconLocation = "{exe_path},0"
        $Shortcut.Save()
    }}
    """
    
    try:
        # Chạy ẩn tiến trình PowerShell để tránh nháy màn hình cmd đen
        subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            creationflags=0x08000000, # CREATE_NO_WINDOW
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print("[Hệ thống] Đã tự động tạo các phím tắt (Shortcut) trên Desktop và Start Menu.")
    except Exception as e:
        print(f"[Hệ thống] Không thể tự động tạo shortcut: {e}")

def sigint_handler(app_instance):
    """Hàm xử lý bắt phím tắt Ctrl+C để thoát ứng dụng."""
    def handler(*args):
        print("\n[Hệ thống] Nhận lệnh dừng (Ctrl+C). Đang dọn dẹp và thoát...")
        app_instance.stop()
        os._exit(0)
    return handler

def main():
    # Hỗ trợ in ký tự tiếng Việt ra console trên Windows mà không bị lỗi UnicodeEncodeError
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')
        
    # Ẩn các cảnh báo hệ thống font DirectWrite không cần thiết của Qt trên Windows
    os.environ["QT_LOGGING_RULES"] = "qt.qpa.fonts.warning=false"
    
    # Khởi tạo ứng dụng PyQt6
    app = QApplication(sys.argv)
    
    # Tự động tạo Shortcut nếu cần thiết
    try:
        create_shortcuts()
    except Exception as create_err:
        print(f"[Hệ thống] Lỗi khi tạo phím tắt: {create_err}")
    
    # Đảm bảo ứng dụng chạy ngầm không tự động thoát khi ẩn các cửa sổ nổi
    app.setQuitOnLastWindowClosed(False)
    
    # Khởi tạo App Controller điều phối chung
    app_controller = TransMartApp()
    app_controller.start()

    # Thiết lập hệ thống bắt tín hiệu Ctrl+C từ terminal
    signal.signal(signal.SIGINT, sigint_handler(app_controller))
    
    # QTimer chạy tuần hoàn giúp Python thông dịch nhận tín hiệu Ctrl+C
    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    print("=== TransMart Floating UI System ===")
    print("Ứng dụng đang chạy ẩn...")
    print("Vui lòng thử thực hiện:")
    print("1. Kéo chuột bôi đen chữ bất kỳ ở Chrome/Word ➔ Hiện nút tròn 🌐 ➔ Click để xem kết quả dịch nổi.")
    print("2. Bôi đen chữ bất kỳ rồi nhấn Alt + Z ➔ Bảng dịch nổi lên trực tiếp tại chuột.")
    print("3. Bấm thử nút 'Sao chép' hoặc 'Phát âm' trên bảng dịch nổi để kiểm tra.")
    print("Nhấn Ctrl + C tại Terminal này để dừng chương trình.")
    print("==================================")

    # Chạy vòng lặp sự kiện giao diện
    exit_code = app.exec()
    app_controller.stop()
    os._exit(exit_code)

if __name__ == "__main__":
    main()
