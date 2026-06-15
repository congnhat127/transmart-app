# ui/pop_icon.py
from PyQt6.QtWidgets import QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QEvent
from PyQt6.QtGui import QEnterEvent

from ui.styles import get_pop_icon_style

class PopIconWidget(QPushButton):
    """
    Nút bấm hình tròn nổi nhỏ xuất hiện dưới con trỏ chuột khi người dùng bôi đen văn bản.
    Nhấn vào nút này sẽ kích hoạt hộp thoại dịch thuật chính.
    """
    # Tín hiệu phát ra khi người dùng click vào nút, gửi kèm văn bản bôi đen cần dịch
    text_triggered = pyqtSignal(str)

    def __init__(self, theme: str = "dark"):
        super().__init__()
        self.theme = theme
        self.selected_text = ""
        
        # 1. Cấu hình các đặc tính cửa sổ nổi (Floating Tool Window)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |      # Bỏ viền tiêu đề Windows
            Qt.WindowType.WindowStaysOnTopHint |     # Luôn hiển thị trên cùng các app khác
            Qt.WindowType.Tool |                     # Không hiển thị icon dưới thanh Taskbar
            Qt.WindowType.NoDropShadowWindowHint     # Bỏ bóng mặc định của Windows (chúng ta tự xử lý)
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground) # Hỗ trợ nền trong suốt (Glass)
        
        # 2. Thiết lập kích thước nút tròn
        self.setFixedSize(36, 36)
        self.setText("🌐") # Icon đại diện dịch thuật (Unicode)
        self.setCursor(Qt.CursorShape.PointingHandCursor) # Đổi con trỏ chuột thành hình bàn tay chỉ
        
        # Áp dụng stylesheet Glassmorphism từ ui/styles.py
        self.setStyleSheet(get_pop_icon_style(self.theme))

        # 3. Cấu hình bộ đếm thời gian tự động ẩn (Auto-hide Timer)
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(self.hide)

        # Kết nối sự kiện click của nút bấm vào hàm xử lý nội bộ
        self.clicked.connect(self._on_clicked)

    def show_at(self, text: str, x: int, y: int):
        """
        Hiển thị nút dịch nhanh tại trung tâm bên dưới vùng bôi đen.
        
        Args:
            text (str): Văn bản người dùng vừa bôi đen.
            x (int): Tọa độ x trung tâm vùng chọn.
            y (int): Tọa độ y đáy của vùng chọn.
        """
        if not text.strip():
            return
            
        self.selected_text = text
        
        # Đặt nút ở góc dưới bên phải của tọa độ bên phải cùng của văn bản được chọn
        self.move(x + 5, y + 5)
        self.show()
        
        # Bắt đầu đếm ngược 3 giây để tự động ẩn nếu người dùng không tương tác
        self.hide_timer.start(3000)

    def update_theme(self, new_theme: str):
        """Cập nhật lại giao diện khi người dùng thay đổi theme."""
        self.theme = new_theme
        self.setStyleSheet(get_pop_icon_style(self.theme))

    def _on_clicked(self):
        """Xử lý khi người dùng nhấn vào nút tròn dịch nhanh."""
        self.hide_timer.stop()
        self.hide() # Ẩn nút tròn đi
        self.text_triggered.emit(self.selected_text) # Phát tín hiệu dịch kèm chữ

    # === Ghi đè các sự kiện rê chuột (Hover) để tối ưu trải nghiệm ===
    
    def enterEvent(self, event: QEnterEvent) -> None:
        """Khi người dùng rê chuột VÀO nút tròn: Tạm dừng bộ đếm thời gian ẩn."""
        self.hide_timer.stop()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        """Khi người dùng rê chuột RA KHỎI nút tròn: Tiếp tục đếm ngược để ẩn."""
        self.hide_timer.start(2000) # Cho thêm 2 giây trước khi ẩn
        super().leaveEvent(event)
