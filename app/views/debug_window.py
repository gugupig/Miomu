import logging
from PySide6.QtWidgets import QMainWindow, QTextEdit
from PySide6.QtCore import Slot

class DebugLogWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("调试日志 (Debug Log)")
        self.setGeometry(100, 100, 800, 600)
        
        self.log_display = QTextEdit(self)
        self.log_display.setReadOnly(True)
        self.setCentralWidget(self.log_display)

    @Slot(str, int)
    def add_log_message(self, message: str, level: int):
        """接收日志信号并添加到文本框中。"""
        # 这个窗口显示所有DEBUG及以上级别的日志
        if level >= logging.DEBUG:
            self.log_display.append(message)