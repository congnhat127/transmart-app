from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import QPushButton, QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor
from ui.styles import get_pop_icon_style
from config.settings import settings_manager

class PopIconWidget(QPushButton):
    # Phát ra khi người dùng click vào icon nổi, chuyển tiếp đoạn text bôi đen
    clicked_trigger = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # Cấu hình cửa sổ không viền, luôn hiển thị trên cùng và không hiện ở thanh Taskbar
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Thiết lập kích thước nút
        self.setFixedSize(40, 40)
        
        # Sử dụng ký tự Unicode dịch thuật "文" hoặc quả địa cầu "🌐" làm biểu tượng
        self.setText("文")
        
        # Font chữ biểu tượng nổi bật
        font = self.font()
        font.setPointSize(14)
        font.setBold(True)
        self.setFont(font)
        
        # Áp dụng màu sắc chữ mặc định là trắng/xanh
        self.setStyleSheet("color: #0078D4;")
        
        # Thêm hiệu ứng đổ bóng cho nút nổi bật trên màn hình
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 80))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        # Lưu trữ văn bản đang bôi đen
        self.selected_text = ""
        
        # Timer tự động ẩn nút sau vài giây nếu không được click
        self.auto_hide_timer = QTimer(self)
        self.auto_hide_timer.setSingleShot(True)
        self.auto_hide_timer.timeout.connect(self.hide)
        
        # Kết nối sự kiện click
        self.clicked.connect(self._on_clicked)

    def show_at(self, text: str, x: int, y: int):
        """Hiển thị nút tròn dịch thuật tại tọa độ con trỏ chuột."""
        self.selected_text = text
        
        # Cập nhật style sheet theo theme hiện tại
        theme = settings_manager.get("theme", "dark")
        self.setStyleSheet(get_pop_icon_style(theme))
        
        # Đặt vị trí hiển thị hơi lệch xuống dưới và sang phải của con trỏ chuột
        # Tránh hiển thị đè trực tiếp lên con trỏ làm cản trở thao tác click tiếp theo
        self.move(x + 15, y + 15)
        
        self.show()
        
        # Tự động ẩn sau 3 giây
        self.auto_hide_timer.start(3000)

    def _on_clicked(self):
        self.auto_hide_timer.stop()
        self.hide()
        self.clicked_trigger.emit(self.selected_text)

    # Khi di chuột qua, dừng đếm ngược tự ẩn để người dùng kịp click
    def enterEvent(self, event):
        self.auto_hide_timer.stop()
        super().enterEvent(event)

    # Khi di chuột ra khỏi vùng nút, bắt đầu lại đếm ngược ẩn nút
    def leaveEvent(self, event):
        self.auto_hide_timer.start(1500)
        super().leaveEvent(event)
