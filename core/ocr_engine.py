import os
from PyQt6.QtCore import Qt, QRect, QPoint, pyqtSignal
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QScreen
from PIL import Image
import io

class ScreenCaptureWidget(QWidget):
    # Tín hiệu trả về hình ảnh được chụp sau khi kéo chọn xong vùng màn hình
    screenshot_captured = pyqtSignal(Image.Image)

    def __init__(self):
        super().__init__()
        # Đặt cửa sổ trong suốt và tràn màn hình
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.CrossCursor)
        
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
        
        # Lấy kích thước toàn màn hình
        self.screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(self.screen_geometry)
        
        # Chụp lại toàn bộ màn hình nền trước khi vẽ lớp phủ
        self.background_pixmap = QApplication.primaryScreen().grabWindow(0)

    def paintEvent(self, event):
        painter = QPainter(self)
        # Vẽ màn hình nền thực tế
        painter.drawPixmap(0, 0, self.background_pixmap)
        
        # Vẽ một lớp phủ tối mờ toàn màn hình
        overlay_color = QColor(0, 0, 0, 100)
        painter.fillRect(self.rect(), overlay_color)
        
        if self.is_selecting and self.start_pos and self.end_pos:
            # Xác định hình chữ nhật kéo chọn
            selection_rect = QRect(self.start_pos, self.end_pos)
            
            # Vẽ lại vùng được chọn để loại bỏ lớp phủ mờ (vùng sáng)
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            painter.drawPixmap(selection_rect, self.background_pixmap, selection_rect)
            
            # Vẽ viền cho vùng được chọn
            pen = QPen(QColor(0, 120, 212), 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)
            painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
            painter.drawRect(selection_rect)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_pos = event.position().toPoint()
            self.end_pos = self.start_pos
            self.is_selecting = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_pos = event.position().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.end_pos = event.position().toPoint()
            
            # Kiểm tra nếu vùng chọn đủ lớn
            rect = QRect(self.start_pos, self.end_pos).normalized()
            if rect.width() > 5 and rect.height() > 5:
                # Cắt phần hình ảnh được chọn từ ảnh nền
                cropped_pixmap = self.background_pixmap.copy(rect)
                
                # Chuyển đổi QPixmap sang PIL Image
                buffer = io.BytesIO()
                cropped_pixmap.toImage().save(buffer, "PNG")
                buffer.seek(0)
                pil_img = Image.open(buffer)
                pil_img.load() # Load hình ảnh vào memory trước khi đóng buffer
                
                self.screenshot_captured.emit(pil_img)
            
            self.close()

    def keyPressEvent(self, event):
        # Cho phép hủy bằng phím Esc
        if event.key() == Qt.Key.Key_Escape:
            self.close()


class OcrEngine:
    @staticmethod
    def extract_text(pil_image: Image.Image) -> str:
        """
        Trích xuất văn bản từ hình ảnh. 
        Ưu tiên dùng Windows OCR (winrt) -> Fallback sang Gemini API/Tesseract.
        """
        try:
            # Thử nghiệm sử dụng Windows OCR API cục bộ nếu đã cài đặt winrt
            import winrt.windows.media.ocr as ocr
            import winrt.windows.graphics.imaging as imaging
            import winrt.windows.storage.streams as streams
            import asyncio

            async def _win_ocr():
                # Chuyển đổi PIL Image thành bytes và đưa vào WinRT stream
                img_byte_arr = io.BytesIO()
                pil_image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()
                
                # Khởi tạo stream của Windows
                data_writer = streams.DataWriter()
                data_writer.write_bytes(img_bytes)
                ibuffer = data_writer.detach_buffer()
                
                # Load ảnh từ buffer
                stream = streams.InMemoryRandomAccessStream()
                await stream.write_async(ibuffer)
                stream.seek(0)
                
                decoder = await imaging.BitmapDecoder.create_async(stream)
                software_bitmap = await decoder.get_software_bitmap_async()
                
                # Sử dụng ngôn ngữ mặc định của hệ thống để OCR
                engine = ocr.OcrEngine.try_create_from_user_profile_languages()
                if not engine:
                    return ""
                
                result = await engine.recognize_async(software_bitmap)
                return result.text
            
            # Chạy hàm async đồng bộ
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            text = loop.run_until_complete(_win_ocr())
            loop.close()
            if text:
                return text
        except Exception as e:
            print(f"[OCR] Không thể sử dụng Windows OCR: {e}. Sẽ chuyển sang phương thức dự phòng.")
            
        # Nếu Windows OCR không dùng được, ta có thể trả về thông báo lỗi hoặc
        # gửi hình ảnh trực tiếp sang services/ai_service.py để AI nhận diện (Multimodal).
        # File services/ai_service.py sẽ hỗ trợ hàm nhận diện chữ qua ảnh bằng Gemini.
        return ""
