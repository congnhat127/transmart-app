import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QListWidget, QListWidgetItem, QPushButton, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

class HistoryWindow(QWidget):
    """
    Giao diện Quản lý Lịch sử dịch thuật.
    Hiển thị danh sách các từ/đoạn văn bản đã dịch, hỗ trợ tìm kiếm và xem lại chi tiết.
    """
    history_cleared = pyqtSignal()

    def __init__(self, theme: str = "dark"):
        super().__init__()
        self.theme = theme
        self.setWindowTitle("TransMart - Lịch sử dịch thuật")
        self.setMinimumSize(500, 400)
        self.resize(550, 450)
        
        self.setWindowFlags(
            Qt.WindowType.Window | 
            Qt.WindowType.WindowCloseButtonHint | 
            Qt.WindowType.WindowMinimizeButtonHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        self._apply_style()
        self._init_ui()
        self.load_history()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Header Title
        header_layout = QHBoxLayout()
        header_title = QLabel("LỊCH SỬ DỊCH THUẬT")
        header_title.setObjectName("HeaderTitle")
        header_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Search Bar
        self.search_input = QLineEdit()
        self.search_input.setObjectName("SearchInput")
        self.search_input.setPlaceholderText("🔍 Tìm kiếm trong lịch sử...")
        self.search_input.textChanged.connect(self.filter_history)
        main_layout.addWidget(self.search_input)

        # Split Layout: Danh sách bên trái, Chi tiết bên phải
        split_layout = QHBoxLayout()
        split_layout.setSpacing(10)

        # Danh sách lịch sử
        self.history_list = QListWidget()
        self.history_list.setObjectName("HistoryList")
        self.history_list.setFixedWidth(220)
        self.history_list.currentItemChanged.connect(self.display_item_detail)
        split_layout.addWidget(self.history_list)

        # Vùng xem chi tiết bản dịch
        detail_layout = QVBoxLayout()
        detail_layout.setSpacing(8)

        detail_layout.addWidget(QLabel("Văn bản gốc:"))
        self.source_view = QTextEdit()
        self.source_view.setReadOnly(True)
        self.source_view.setObjectName("DetailText")
        detail_layout.addWidget(self.source_view)

        detail_layout.addWidget(QLabel("Bản dịch & Giải thích:"))
        self.target_view = QTextEdit()
        self.target_view.setReadOnly(True)
        self.target_view.setObjectName("DetailText")
        detail_layout.addWidget(self.target_view)

        split_layout.addLayout(detail_layout)
        main_layout.addLayout(split_layout)

        # Bottom Buttons
        bottom_layout = QHBoxLayout()
        self.delete_btn = QPushButton("Xóa bản ghi")
        self.delete_btn.setObjectName("DeleteBtn")
        self.delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.delete_btn.clicked.connect(self.delete_selected_item)

        self.clear_all_btn = QPushButton("Xóa tất cả")
        self.clear_all_btn.setObjectName("ClearAllBtn")
        self.clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_all_btn.clicked.connect(self.clear_all_history)

        self.close_btn = QPushButton("Đóng")
        self.close_btn.setObjectName("CloseBtn")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)

        bottom_layout.addWidget(self.delete_btn)
        bottom_layout.addWidget(self.clear_all_btn)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.close_btn)
        main_layout.addLayout(bottom_layout)

    def load_history(self):
        """Nạp danh sách lịch sử dịch (Placeholder/Mock - sẽ đấu nối với DB/JSON sau)."""
        self.history_list.clear()
        
        # Dữ liệu mẫu (Mock Data)
        self.history_items = [
            {"source": "Hello World", "translation": "Xin chào thế giới", "explanation": "Lời chào lập trình kinh điển."},
            {"source": "Machine learning", "translation": "Học máy", "explanation": "Một phân ngành của Trí tuệ nhân tạo (AI)."},
            {"source": "Git workflow", "translation": "Luồng làm việc Git", "explanation": "Các bước phối hợp code sử dụng Git."}
        ]
        
        for idx, item in enumerate(self.history_items):
            list_item = QListWidgetItem(item["source"])
            # Lưu trữ dữ liệu tùy chỉnh vào item để truy xuất sau
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.history_list.addItem(list_item)

    def display_item_detail(self, current, previous):
        """Hiển thị chi tiết bản dịch khi click chọn phần tử trong danh sách."""
        if current:
            item_data = current.data(Qt.ItemDataRole.UserRole)
            if item_data:
                self.source_view.setPlainText(item_data.get("source", ""))
                
                translation = item_data.get("translation", "")
                explanation = item_data.get("explanation", "")
                
                detail_text = f"Dịch: {translation}\n\nGiải thích:\n{explanation}"
                self.target_view.setPlainText(detail_text)
        else:
            self.source_view.clear()
            self.target_view.clear()

    def filter_history(self, text):
        """Lọc danh sách lịch sử theo từ khóa tìm kiếm."""
        for i in range(self.history_list.count()):
            item = self.history_list.item(i)
            # Ẩn nếu từ khóa không khớp
            item.setHidden(text.lower() not in item.text().lower())

    def delete_selected_item(self):
        """Xóa bản ghi đang chọn."""
        current_item = self.history_list.currentItem()
        if current_item:
            self.history_list.takeItem(self.history_list.row(current_item))
            QMessageBox.information(self, "Thông báo", "Đã xóa bản ghi được chọn thành công.")
        else:
            QMessageBox.warning(self, "Cảnh báo", "Vui lòng chọn một bản ghi để xóa.")

    def clear_all_history(self):
        """Xóa toàn bộ danh sách lịch sử dịch."""
        reply = QMessageBox.question(
            self, "Xác nhận", "Bạn có chắc chắn muốn xóa toàn bộ lịch sử dịch thuật?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.history_list.clear()
            self.source_view.clear()
            self.target_view.clear()
            self.history_cleared.emit()
            QMessageBox.information(self, "Thông báo", "Đã xóa toàn bộ lịch sử dịch thuật.")

    def _apply_style(self):
        """Áp dụng StyleSheet CSS cho History Window."""
        if self.theme == "dark":
            self.setStyleSheet("""
                QWidget {
                    background-color: #1E1E1E;
                    color: #E0E0E0;
                    font-family: 'Segoe UI', sans-serif;
                }
                QLabel#HeaderTitle {
                    color: #FFFFFF;
                }
                QLineEdit#SearchInput {
                    background-color: #2D2D2D;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                    padding: 6px 10px;
                    color: #FFFFFF;
                }
                QLineEdit#SearchInput:focus {
                    border: 1px solid #0078D4;
                }
                QListWidget#HistoryList {
                    background-color: #252526;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                    padding: 5px;
                }
                QListWidget#HistoryList::item {
                    padding: 8px 10px;
                    border-radius: 4px;
                    color: #CCCCCC;
                }
                QListWidget#HistoryList::item:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                    color: #FFFFFF;
                }
                QListWidget#HistoryList::item:selected {
                    background-color: #0078D4;
                    color: #FFFFFF;
                }
                QTextEdit#DetailText {
                    background-color: #252526;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                    padding: 8px;
                    color: #FFFFFF;
                }
                QPushButton {
                    padding: 6px 14px;
                    border-radius: 4px;
                    font-weight: 600;
                }
                QPushButton#DeleteBtn {
                    background-color: transparent;
                    border: 1px solid #E81123;
                    color: #E81123;
                }
                QPushButton#DeleteBtn:hover {
                    background-color: #E81123;
                    color: #FFFFFF;
                }
                QPushButton#ClearAllBtn {
                    background-color: transparent;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: #CCCCCC;
                }
                QPushButton#ClearAllBtn:hover {
                    background-color: rgba(255, 255, 255, 0.05);
                    color: #FFFFFF;
                }
                QPushButton#CloseBtn {
                    background-color: #333333;
                    color: #FFFFFF;
                    border: none;
                }
                QPushButton#CloseBtn:hover {
                    background-color: #444444;
                }
            """)
        else:
            self.setStyleSheet("""
                QWidget {
                    background-color: #F3F3F3;
                    color: #333333;
                    font-family: 'Segoe UI', sans-serif;
                }
                QLabel#HeaderTitle {
                    color: #1A1A1A;
                }
                QLineEdit#SearchInput {
                    background-color: #FFFFFF;
                    border: 1px solid rgba(0, 0, 0, 0.15);
                    border-radius: 4px;
                    padding: 6px 10px;
                    color: #333333;
                }
                QLineEdit#SearchInput:focus {
                    border: 1px solid #0078D4;
                }
                QListWidget#HistoryList {
                    background-color: #FFFFFF;
                    border: 1px solid rgba(0, 0, 0, 0.15);
                    border-radius: 4px;
                    padding: 5px;
                }
                QListWidget#HistoryList::item {
                    padding: 8px 10px;
                    border-radius: 4px;
                    color: #333333;
                }
                QListWidget#HistoryList::item:hover {
                    background-color: rgba(0, 0, 0, 0.05);
                }
                QListWidget#HistoryList::item:selected {
                    background-color: #0078D4;
                    color: #FFFFFF;
                }
                QTextEdit#DetailText {
                    background-color: #FFFFFF;
                    border: 1px solid rgba(0, 0, 0, 0.15);
                    border-radius: 4px;
                    padding: 8px;
                    color: #333333;
                }
                QPushButton {
                    padding: 6px 14px;
                    border-radius: 4px;
                    font-weight: 600;
                }
                QPushButton#DeleteBtn {
                    background-color: transparent;
                    border: 1px solid #E81123;
                    color: #E81123;
                }
                QPushButton#DeleteBtn:hover {
                    background-color: #E81123;
                    color: #FFFFFF;
                }
                QPushButton#ClearAllBtn {
                    background-color: transparent;
                    border: 1px solid rgba(0, 0, 0, 0.15);
                    color: #666666;
                }
                QPushButton#ClearAllBtn:hover {
                    background-color: rgba(0, 0, 0, 0.05);
                    color: #1A1A1A;
                }
                QPushButton#CloseBtn {
                    background-color: #E5E5E5;
                    color: #333333;
                    border: none;
                }
                QPushButton#CloseBtn:hover {
                    background-color: #CCCCCC;
                }
            """)
