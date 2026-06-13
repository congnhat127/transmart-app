from PyQt6.QtWidgets import QPushButton

class PopIconWidget(QPushButton):
    """Nút bấm Icon nổi nhỏ xuất hiện dưới con trỏ chuột khi người dùng bôi đen văn bản."""
    def __init__(self):
        super().__init__()
        pass

    def show_at(self, text: str, x: int, y: int):
        pass
