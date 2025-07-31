import logging
from PySide6.QtCore import QObject, Signal

class QtLogHandler(logging.Handler):
    """
    一个将日志记录发送到Qt信号的自定义Handler。
    """
    class _SignalEmitter(QObject):
        # 定义信号，携带 消息(str) 和 日志级别(int)
        message_written = Signal(str, int)

    def __init__(self, parent=None):
        super().__init__()
        self.emitter = self._SignalEmitter()

    def emit(self, record):
        """
        当有日志需要处理时，此方法被logging模块调用。
        """
        message = self.format(record)
        levelno = record.levelno
        self.emitter.message_written.emit(message, levelno)