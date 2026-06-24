# core/ocr_engine.py
import time
from io import BytesIO
from PIL import Image
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QPoint, QRect, QBuffer, QIODevice
from PyQt6.QtGui import QPainter, QPen, QColor, QPixmap, QFont

def qpixmap_to_pil(pixmap: QPixmap) -> Image.Image:
    """Chuyển đổi QPixmap của Qt sang đối tượng Image của thư viện Pillow."""
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    pixmap.save(buffer, "PNG")
    image_bytes = buffer.data().data()
    return Image.open(BytesIO(image_bytes))

class ScreenCaptureWidget(QWidget):
    """
    Cửa sổ overlay phủ toàn màn hình để cho phép người dùng kéo thả chuột,
    chọn một phân vùng bất kỳ trên màn hình phục vụ cho quá trình nhận diện chữ (OCR).
    """
    capture_finished = pyqtSignal(QPixmap, QRect)  # Phát ra: (Ảnh đã crop, Tọa độ vùng quét trên màn hình)

    def __init__(self):
        super().__init__()
        # 1. Cấu hình đặc tính cửa sổ toàn màn hình, đè lên trên mọi cửa sổ khác
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setCursor(Qt.CursorShape.CrossCursor) # Con trỏ hình chữ thập phục vụ chọn vùng
        
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
        
        self.physical_screenshot = None
        self.full_screenshot = None
        self.dimmed_screenshot = None

    def start_capture(self):
        """Khởi chạy quá trình chụp màn hình toàn bộ desktop và hiển thị overlay."""
        # 1. Lấy thông tin màn hình hiện tại
        screen = QApplication.primaryScreen()
        if not screen:
            return
            
        geom = screen.geometry()
        device_ratio = screen.devicePixelRatio()
        
        # 2. Chụp ảnh màn hình chính xác theo vùng tọa độ màn hình chính (DPI-aware)
        self.physical_screenshot = screen.grabWindow(0, geom.x(), geom.y(), geom.width(), geom.height())
        
        # 3. Tạo phiên bản màn hình làm mờ (dimmed) ở kích thước vật lý trước
        self.dimmed_screenshot = QPixmap(self.physical_screenshot)
        painter = QPainter(self.dimmed_screenshot)
        painter.fillRect(self.dimmed_screenshot.rect(), QColor(0, 0, 0, 130)) # 50% opacity đen
        painter.end()
        
        # 4. Tạo phiên bản màn hình đầy đủ kích thước logic
        self.full_screenshot = QPixmap(self.physical_screenshot)
        
        # Cấu hình Device Pixel Ratio để đồng bộ hóa kích thước vật lý sang kích thước logic của Qt (High DPI / 4K Windows Scaling)
        self.full_screenshot.setDevicePixelRatio(device_ratio)
        self.dimmed_screenshot.setDevicePixelRatio(device_ratio)
        
        # 5. Đặt kích thước widget bằng đúng kích thước màn hình và hiển thị full screen
        self.setGeometry(geom)
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.position().toPoint()
            self.end_pos = self.start_pos
            self.is_selecting = True
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            # Nhấp chuột phải để hủy bỏ nhanh
            self.close()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.end_pos = event.position().toPoint()
            self.is_selecting = False
            
            # Tính toán hình chữ nhật vùng quét thực tế (ở tọa độ logic)
            selection_rect = QRect(self.start_pos, self.end_pos).normalized()
            
            # Nếu vùng quét đủ lớn (tránh cú click vô tình)
            if selection_rect.width() > 8 and selection_rect.height() > 8:
                screen = QApplication.primaryScreen()
                device_ratio = screen.devicePixelRatio() if screen else 1.0
                
                # Nhân tọa độ vùng chọn với device_ratio để lấy tọa độ vật lý chính xác trên QPixmap gốc
                physical_rect = QRect(
                    int(selection_rect.x() * device_ratio),
                    int(selection_rect.y() * device_ratio),
                    int(selection_rect.width() * device_ratio),
                    int(selection_rect.height() * device_ratio)
                )
                
                # Cắt trực tiếp từ ảnh vật lý gốc không có tỷ lệ làm tròn lỗi
                cropped_pixmap = self.physical_screenshot.copy(physical_rect)
                
                # Áp dụng tọa độ tuyệt đối trên màn hình
                global_rect = QRect(
                    self.mapToGlobal(selection_rect.topLeft()),
                    self.mapToGlobal(selection_rect.bottomRight())
                ).normalized()
                
                self.capture_finished.emit(cropped_pixmap, global_rect)
            
            self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            # Nhấn Esc để hủy bỏ
            self.close()
        super().keyPressEvent(event)

    def paintEvent(self, event):
        if not self.full_screenshot:
            return
            
        painter = QPainter(self)
        
        # 1. Vẽ nền mờ toàn màn hình
        painter.drawPixmap(self.rect(), self.dimmed_screenshot)
        
        # 2. Vẽ vùng sáng nguyên bản nếu người dùng đang kéo chuột chọn
        if self.start_pos and self.end_pos:
            rect = QRect(self.start_pos, self.end_pos).normalized()
            
            # Sử dụng cơ chế Clipping để vẽ vùng sáng đè lên. 
            # Cách này triệt tiêu hoàn toàn lỗi lệch tọa độ khi vẽ giữa logic và vật lý của QPainter.
            painter.save()
            painter.setClipRect(rect)
            painter.drawPixmap(self.rect(), self.full_screenshot)
            painter.restore()
            
            # Vẽ đường viền xung quanh vùng chọn
            pen = QPen(QColor(66, 133, 244), 2)  # Màu xanh Google Accent
            painter.setPen(pen)
            painter.drawRect(rect)
            
            # Hiển thị kích thước vùng chọn (ví dụ: 120 x 80)
            size_text = f"{rect.width()} x {rect.height()}"
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            painter.drawText(rect.topLeft() + QPoint(5, -5), size_text)
        else:
            # Vẽ thông báo hướng dẫn khi chưa chọn
            painter.setPen(QColor(255, 255, 255, 200))
            painter.setFont(QFont("Segoe UI", 13, QFont.Weight.Medium))
            instruction = "Kéo thả chuột trái để quét vùng dịch, nhấn chuột phải hoặc Esc để hủy"
            # Vẽ căn giữa ở nửa trên màn hình
            text_rect = QRect(0, self.height() // 4, self.width(), 50)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, instruction)

class OcrEngine:
    """Lớp bọc động cơ nhận diện văn bản OCR (Tính năng chính xử lý thông qua Multimodal AI)."""
    @staticmethod
    def extract_text(image) -> str:
        pass
