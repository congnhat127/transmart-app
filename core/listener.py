import time
import os
import ctypes
# pyrefly: ignore [missing-import]
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import keyboard
import pynput

from core.clipboard_manager import ClipboardManager

def get_active_window_process_name() -> str:
    """Lấy tên file thực thi (.exe) của cửa sổ đang active/foreground trên Windows (Hỗ trợ tốt UWP Apps)."""
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return ""
        pid = ctypes.c_ulong()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        # Nếu cửa sổ thuộc nhóm UWP (như ScreenSketch.exe chạy ẩn dưới ApplicationFrameHost.exe)
        buf_class = ctypes.create_unicode_buffer(260)
        ctypes.windll.user32.GetClassNameW(hwnd, buf_class, 260)
        if buf_class.value == "ApplicationFrameWindow":
            # Hàm callback để tìm đúng PID của tiến trình con thực tế
            def enum_child_proc(child_hwnd, lparam):
                child_pid = ctypes.c_ulong()
                ctypes.windll.user32.GetWindowThreadProcessId(child_hwnd, ctypes.byref(child_pid))
                if child_pid.value != pid.value:
                    # Ghi đè PID của tiến trình con thực tế vào con trỏ lparam
                    ctypes.cast(lparam, ctypes.POINTER(ctypes.c_ulong))[0] = child_pid.value
                    return False  # Dừng đệ quy
                return True
            
            real_pid = ctypes.c_ulong(pid.value)
            enum_child_callback = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
            ctypes.windll.user32.EnumChildWindows(hwnd, enum_child_callback(enum_child_proc), ctypes.byref(real_pid))
            pid = real_pid

        # PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h_process = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
        if not h_process:
            return ""
            
        buf_size = ctypes.c_ulong(260)
        buf = ctypes.create_unicode_buffer(260)
        success = ctypes.windll.kernel32.QueryFullProcessImageNameW(h_process, 0, buf, ctypes.byref(buf_size))
        ctypes.windll.kernel32.CloseHandle(h_process)
        
        if success:
            return os.path.basename(buf.value).lower()
    except Exception:
        pass
    return ""

def is_ibeam_cursor() -> bool:
    """Kiểm tra xem con trỏ chuột hiện tại có phải là con trỏ soạn thảo văn bản (I-Beam) hay không."""
    try:
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
            
        class CURSORINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_ulong),
                ("flags", ctypes.c_ulong),
                ("hCursor", ctypes.c_void_p),
                ("ptScreenPos", POINT)
            ]
            
        cursor_info = CURSORINFO()
        cursor_info.cbSize = ctypes.sizeof(CURSORINFO)
        if ctypes.windll.user32.GetCursorInfo(ctypes.byref(cursor_info)):
            if cursor_info.flags & 1:  # CURSOR_SHOWING = 0x00000001
                # IDC_IBEAM = 32513
                h_ibeam = ctypes.windll.user32.LoadCursorW(None, 32513)
                return cursor_info.hCursor == h_ibeam
    except Exception:
        pass
    return False

class SystemListener(QObject):
    """
    Lớp lắng nghe sự kiện Hệ thống (Bàn phím và Chuột).
    Kế thừa từ QObject để sử dụng hệ thống Signal (Tín hiệu) của PyQt6,
    giúp truyền sự kiện từ luồng chạy ngầm sang giao diện chính (UI Thread) một cách an toàn.
    """
    # Định nghĩa các tín hiệu để giao diện chính (main.py) kết nối và xử lý:
    # 1. Phát ra văn bản cần dịch trực tiếp khi ấn phím tắt Alt+D
    trigger_translation = pyqtSignal(str)
    # 2. Phát ra sự kiện yêu cầu mở vùng chụp màn hình để dịch OCR khi ấn Alt+Q
    trigger_ocr = pyqtSignal()
    # 3. Phát ra khi người dùng vừa bôi đen xong văn bản bằng chuột: (văn bản bôi đen, tọa độ x, tọa độ y)
    text_selected = pyqtSignal(str, int, int)
    # 4. Tín hiệu nội bộ truyền tọa độ bôi đen từ luồng hook chuột sang luồng GUI chính
    _check_selection_sig = pyqtSignal(int, int, int, int)
    # 5. Phát ra khi phát hiện cú click chuột trái thông thường (làm mất bôi đen)
    click_detected = pyqtSignal(int, int)
    # 6. Tín hiệu nội bộ truyền sự kiện click chuột trái sang luồng GUI chính
    _click_sig = pyqtSignal(int, int)

    def __init__(self):
        super().__init__()
        # Trạng thái theo dõi chuột
        self.is_left_pressed = False      # Lưu trạng thái chuột trái có đang đè xuống không
        self.drag_start_pos = None        # Tọa độ (x, y) lúc bắt đầu nhấn chuột trái
        self.is_starting_with_ibeam = False # Xác định thao tác bắt đầu bằng con trỏ soạn thảo văn bản
        self.mouse_listener = None        # Bộ lắng nghe sự kiện chuột
        
        # Kết nối tín hiệu nội bộ để nhận tọa độ và xử lý an toàn trên GUI Thread
        self._check_selection_sig.connect(self._check_selection_async)
        self._click_sig.connect(self._on_click_async)
        
        # Ngưỡng khoảng cách tối thiểu (pixel) để coi là một hành động kéo bôi đen
        # Nhấp chuột thông thường (click) thường dịch chuyển từ 0-5px. 
        # Chúng ta đặt 12px để chắc chắn người dùng đang kéo bôi đen chữ.
        self.drag_threshold = 12 

    def start(self, hotkey: str = "alt+z", ocr_hotkey: str = "alt+q"):
        """Khởi chạy bộ lắng nghe phím tắt và chuột."""
        try:
            # 1. Đăng ký phím tắt hệ thống bằng thư viện `keyboard`
            # Lệnh này sẽ chạy ngầm để bắt phím kể cả khi app đang ẩn
            keyboard.add_hotkey(hotkey, self._on_translate_hotkey)
            keyboard.add_hotkey(ocr_hotkey, self._on_ocr_hotkey)
            
            # 2. Đăng ký lắng nghe chuột bằng `pynput.mouse`
            # Khởi chạy một luồng daemon chạy ngầm để lắng nghe
            self.mouse_listener = pynput.mouse.Listener(on_click=self._on_click)
            self.mouse_listener.start()
            
            print(f"[Listener] Đang lắng nghe phím tắt ({hotkey}, {ocr_hotkey}) và sự kiện chuột...")
        except Exception as e:
            print(f"[Listener] Lỗi khởi động bộ lắng nghe: {e}")

    def stop(self):
        """Dừng tất cả bộ lắng nghe và giải phóng tài nguyên."""
        try:
            # Hủy đăng ký tất cả phím tắt
            keyboard.unhook_all()
            
            # Dừng lắng nghe chuột
            if self.mouse_listener:
                self.mouse_listener.stop()
                
            print("[Listener] Đã dừng bộ lắng nghe hệ thống.")
        except Exception as e:
            print(f"[Listener] Lỗi khi dừng bộ lắng nghe: {e}")

    def _on_translate_hotkey(self):
        """Hàm callback được gọi khi phím tắt Alt+Z được nhấn."""
        print("\n[DEBUG] Bộ lắng nghe đã bắt được phím tắt Alt+Z!")
        text = ClipboardManager.get_selected_text(dismiss_menu=True)
        print(f"[DEBUG] Văn bản bôi đen lấy được từ clipboard: '{text}'")
        if text:
            # Nếu có chữ, phát tín hiệu yêu cầu dịch thẳng
            self.trigger_translation.emit(text)
        else:
            print("[DEBUG] Không lấy được văn bản bôi đen nào (hoặc chuỗi rỗng).")

    def _on_ocr_hotkey(self):
        """Hàm callback được gọi khi phím tắt Alt+Q được nhấn."""
        # Phát tín hiệu yêu cầu mở màn hình chụp ảnh OCR
        self.trigger_ocr.emit()

    def _on_click(self, x, y, button, pressed):
        """
        Hàm callback xử lý sự kiện click chuột.
        Được gọi mỗi khi người dùng click chuột xuống hoặc nhả chuột ra.
        """
        # Chúng ta chỉ quan tâm tới chuột trái (chuột dùng để bôi đen chữ)
        if button == pynput.mouse.Button.left:
            if pressed:
                # Chuột trái được nhấn xuống: Ghi lại trạng thái, tọa độ và kiểm tra loại con trỏ
                self.is_left_pressed = True
                self.drag_start_pos = (x, y)
                self.is_starting_with_ibeam = is_ibeam_cursor()
            else:
                # Chuột trái được nhả ra: Tính toán khoảng cách kéo
                self.is_left_pressed = False
                if self.drag_start_pos:
                    start_x, start_y = self.drag_start_pos
                    # Công thức tính khoảng cách dịch chuyển (d = sqrt(dx^2 + dy^2))
                    distance = ((x - start_x) ** 2 + (y - start_y) ** 2) ** 0.5
                    
                    # Nếu khoảng cách kéo lớn hơn ngưỡng và thao tác bắt đầu bằng con trỏ chữ I (soạn thảo)
                    if distance > self.drag_threshold:
                        if self.is_starting_with_ibeam:
                            # Phát tín hiệu nội bộ để chuyển xử lý từ luồng background pynput
                            # sang luồng GUI chính (Main GUI Thread) một cách an toàn và không gây block chuột.
                            self._check_selection_sig.emit(start_x, start_y, x, y)
                    else:
                        # Nhấp chuột thông thường (click): Emit sự kiện click để ẩn các popup
                        self._click_sig.emit(x, y)
                            
                # Reset trạng thái kéo
                self.drag_start_pos = None
                self.is_starting_with_ibeam = False

    def _on_click_async(self, x: int, y: int):
        """Được gọi trên Main GUI Thread khi phát hiện click chuột trái thông thường."""
        self.click_detected.emit(x, y)

    def _check_selection_async(self, start_x: int, start_y: int, end_x: int, end_y: int):
        """Được kích hoạt trên Main GUI Thread. Đặt lịch kiểm tra sau 80ms để clipboard sẵn sàng."""
        QTimer.singleShot(80, lambda: self._do_check_selection(start_x, start_y, end_x, end_y))

    def _do_check_selection(self, start_x: int, start_y: int, end_x: int, end_y: int):
        """Đọc văn bản chọn từ clipboard và phát tín hiệu trên Main GUI Thread."""
        # Tránh can thiệp clipboard khi người dùng đang sử dụng các công cụ chụp ảnh màn hình kéo-thả
        active_exe = get_active_window_process_name()
        screenshot_apps = {
            "screensketch.exe", "snippingtool.exe", "sharex.exe", 
            "greenshot.exe", "lightshot.exe", "snagit.exe", 
            "snagit32.exe", "snagit64.exe"
        }
        if active_exe in screenshot_apps:
            # Trả về ngay lập tức để không xóa hay chiếm quyền clipboard của công cụ chụp ảnh
            return

        text = ClipboardManager.get_selected_text(dismiss_menu=False)
        if text:
            # Tính toán tọa độ góc dưới bên phải của vùng văn bản bôi đen (tọa độ vật lý)
            right_x = max(start_x, end_x)
            bottom_y = max(start_y, end_y)
            # Phát tín hiệu bôi đen kèm theo tọa độ vật lý góc dưới bên phải
            self.text_selected.emit(text, right_x, bottom_y)
