import time
import os
import ctypes
# pyrefly: ignore [missing-import]
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from pynput import keyboard, mouse

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
            
        class ICONINFO(ctypes.Structure):
            _fields_ = [
                ("fIcon", ctypes.c_bool),
                ("xHotspot", ctypes.c_ulong),
                ("yHotspot", ctypes.c_ulong),
                ("hbmMask", ctypes.c_void_p),
                ("hbmColor", ctypes.c_void_p)
            ]
            
        cursor_info = CURSORINFO()
        cursor_info.cbSize = ctypes.sizeof(CURSORINFO)
        if ctypes.windll.user32.GetCursorInfo(ctypes.byref(cursor_info)):
            if cursor_info.flags & 1:  # CURSOR_SHOWING = 0x00000001
                h_cursor = cursor_info.hCursor
                
                # 1. So sánh trực tiếp với I-Beam mặc định
                h_ibeam = ctypes.windll.user32.LoadCursorW(None, 32513)
                if h_cursor == h_ibeam:
                    return True
                    
                # 2. Hỗ trợ trường hợp dùng theme chuột Aero/Custom (GetIconInfo phân tích Hotspot)
                icon_info = ICONINFO()
                if ctypes.windll.user32.GetIconInfo(h_cursor, ctypes.byref(icon_info)):
                    x_hot = icon_info.xHotspot
                    y_hot = icon_info.yHotspot
                    
                    # Giải phóng bitmap của GetIconInfo để tránh rò rỉ bộ nhớ (memory leak)
                    # Thiết lập argtypes để tránh lỗi tràn số (overflow) trên Windows 64-bit
                    ctypes.windll.gdi32.DeleteObject.argtypes = [ctypes.c_void_p]
                    if icon_info.hbmMask:
                        ctypes.windll.gdi32.DeleteObject(icon_info.hbmMask)
                    if icon_info.hbmColor:
                        ctypes.windll.gdi32.DeleteObject(icon_info.hbmColor)
                        
                    # Loại trừ con trỏ Arrow (hotspot luôn là 0, 0)
                    h_arrow = ctypes.windll.user32.LoadCursorW(None, 32512)
                    if h_cursor == h_arrow:
                        return False
                        
                    # Loại trừ con trỏ Hand click link (hotspot thường là 5, 0 hoặc 8, 0)
                    h_hand = ctypes.windll.user32.LoadCursorW(None, 32649)
                    if h_cursor == h_hand:
                        return False
                        
                    # Đặc trưng của I-Beam: hotspot nằm ở giữa thanh dọc (x_hot > 0) và chiều cao tương đối ngắn (y_hot >= 2)
                    # Điều này tương thích hoàn toàn với DPI scaling và các cỡ chuột lớn của Windows.
                    if x_hot > 0 and y_hot >= 2:
                        return True
    except Exception as e:
        print(f"[Listener] Lỗi phân tích con trỏ: {e}")
    return False

def to_pynput_hotkey(hotkey_str: str) -> str:
    """Chuyển đổi phím tắt định dạng 'alt+z' sang '<alt>+z' để phù hợp với pynput."""
    parts = hotkey_str.lower().split('+')
    pynput_parts = []
    for part in parts:
        part = part.strip()
        if part in ('alt', 'ctrl', 'shift', 'cmd', 'win'):
            pynput_parts.append(f"<{part}>")
        else:
            pynput_parts.append(part)
    return "+".join(pynput_parts)

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
    # 3. Phát ra khi người dùng vừa bôi đen xong văn bản bằng chuột: (văn bản bôi đen, start_x, start_y, end_x, end_y)
    text_selected = pyqtSignal(str, int, int, int, int)
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
        self.last_release_time = 0.0      # Thời gian của cú nhả chuột trước đó (phục vụ click đúp)
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
            # 1. Đăng ký phím tắt hệ thống bằng pynput.keyboard.GlobalHotKeys
            # Sử dụng thư viện pynput giúp tránh xung đột với phím PrtSc (Print Screen) của Windows
            pynput_hotkey = to_pynput_hotkey(hotkey)
            pynput_ocr_hotkey = to_pynput_hotkey(ocr_hotkey)
            
            self.hotkey_listener = keyboard.GlobalHotKeys({
                pynput_hotkey: self._on_translate_hotkey,
                pynput_ocr_hotkey: self._on_ocr_hotkey
            })
            self.hotkey_listener.start()
            
            # 2. Đăng ký lắng nghe chuột bằng `mouse.Listener`
            # Khởi chạy một luồng daemon chạy ngầm để lắng nghe
            self.mouse_listener = mouse.Listener(on_click=self._on_click)
            self.mouse_listener.start()
            
            print(f"[Listener] Đang lắng nghe phím tắt ({hotkey}, {ocr_hotkey}) và sự kiện chuột...")
        except Exception as e:
            print(f"[Listener] Lỗi khởi động bộ lắng nghe: {e}")

    def stop(self):
        """Dừng tất cả bộ lắng nghe và giải phóng tài nguyên."""
        try:
            # Dừng lắng nghe phím tắt
            if hasattr(self, "hotkey_listener") and self.hotkey_listener:
                self.hotkey_listener.stop()
            
            # Dừng lắng nghe chuột
            if hasattr(self, "mouse_listener") and self.mouse_listener:
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
        if button == mouse.Button.left:
            if pressed:
                # Chuột trái được nhấn xuống: Ghi lại trạng thái, tọa độ và kiểm tra loại con trỏ
                self.is_left_pressed = True
                self.drag_start_pos = (x, y)
                self.is_starting_with_ibeam = is_ibeam_cursor()
                print(f"[DEBUG] Nhấn chuột trái: cursor_is_ibeam={self.is_starting_with_ibeam}")
            else:
                # Chuột trái được nhả ra: Tính toán khoảng cách kéo và click đúp
                self.is_left_pressed = False
                current_time = time.time()
                is_double_click = (current_time - self.last_release_time < 0.35) # Cú click đúp trong vòng 350ms
                self.last_release_time = current_time
                
                if self.drag_start_pos:
                    start_x, start_y = self.drag_start_pos
                    # Công thức tính khoảng cách dịch chuyển (d = sqrt(dx^2 + dy^2))
                    distance = ((x - start_x) ** 2 + (y - start_y) ** 2) ** 0.5
                    
                    # Kiểm tra xem con trỏ lúc bắt đầu kéo HOẶC lúc nhả chuột có phải là I-Beam không
                    is_ibeam = self.is_starting_with_ibeam or is_ibeam_cursor()
                    
                    # Danh sách các ứng dụng soạn thảo văn bản, trình duyệt, đọc tài liệu hay bôi đen kéo chuột ra ngoài
                    active_exe = get_active_window_process_name().lower()
                    
                    # Tránh can thiệp khi người dùng chụp ảnh màn hình bằng Snipping Tool hoặc các app chụp ảnh khác
                    blacklist_apps = {
                        "screenclippinghost.exe", "snippingtool.exe", "screensketch.exe", 
                        "lightshot.exe", "sharex.exe"
                    }
                    if active_exe in blacklist_apps:
                        self.is_left_pressed = False
                        self.drag_start_pos = None
                        return
                        
                    lenient_apps = {
                        "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", 
                        "vivaldi.exe", "iexplore.exe", "safari.exe", "winword.exe", "excel.exe", 
                        "powerpnt.exe", "notepad.exe", "code.exe", "sublime_text.exe", 
                        "notepad++.exe", "devenv.exe", "obsidian.exe", "acrobat.exe", 
                        "acrord32.exe", "foxitpdfreader.exe", "foxitreader.exe", "pdf24.exe"
                    }
                    is_lenient_app = active_exe in lenient_apps
                    
                    print(f"[DEBUG] Nhả chuột trái: distance={distance:.1f}, is_double_click={is_double_click}, is_ibeam={is_ibeam}, is_lenient_app={is_lenient_app} ({active_exe})")
                    
                    # Nếu khoảng cách kéo lớn hơn ngưỡng và (con trỏ là chữ I HOẶC thuộc ứng dụng ưu tiên)
                    # HOẶC đó là một cú click đúp và (con trỏ là chữ I HOẶC thuộc ứng dụng ưu tiên)
                    if (distance > self.drag_threshold and (is_ibeam or is_lenient_app)) or (is_double_click and (is_ibeam or is_lenient_app)):
                        # Phát tín hiệu nội bộ để chuyển xử lý từ luồng background pynput
                        # sang luồng GUI chính (Main GUI Thread).
                        self._check_selection_sig.emit(start_x, start_y, x, y)
                    else:
                        # Chỉ phát click ẩn nếu không phải là cú click đúp
                        if not is_double_click:
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
        print(f"[DEBUG] Kết quả kiểm tra Clipboard: '{text}'")
        if text:
            # Phát tín hiệu bôi đen kèm theo tọa độ bắt đầu và kết thúc vật lý
            self.text_selected.emit(text, start_x, start_y, end_x, end_y)
