import sys
from PyQt6.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    print("TransMart App - Khởi chạy cấu trúc sơ bộ")
    # Khởi chạy các thành phần tại đây sau
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
