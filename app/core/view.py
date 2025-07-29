import sys
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QKeyEvent
from app.core.player import SubtitlePlayer
from app.models.models import Cue

class SubtitleWindow(QMainWindow):
    def __init__(self, player: SubtitlePlayer):
        super().__init__()
        self.player = player

        # 纯显示配置
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.showFullScreen()
        self.setCursor(Qt.BlankCursor)

        self.label = QLabel("", self, alignment=Qt.AlignCenter, wordWrap=True)
        self.label.setFont(QFont("Arial", 64, QFont.Bold))
        self.label.setStyleSheet("color:#fff;background:#000;padding:40px;")
        self.setCentralWidget(self.label)

        # 连接信号——视图只关心“Cue 改变”这一件事
        self.player.cueChanged.connect(self.display_cue)
        self.player.go(0)                        # 显示首句

    # ---------- Slots ----------
    def display_cue(self, cue: Cue):
        self.label.setText(f"{cue.character}:\n{cue.line}")

    # ---------- Key events (视图层只把交互转给 Player) ----------
    def keyPressEvent(self, ev: QKeyEvent):
        key = ev.key()
        if key in (Qt.Key_Down, Qt.Key_Space, Qt.Key_PageDown):
            self.player.next()
        elif key in (Qt.Key_Up, Qt.Key_PageUp):
            self.player.prev()
        elif key == Qt.Key_Home:
            self.player.go(0)
        elif key == Qt.Key_End:
            self.player.go(len(self.player.cues) - 1)
        elif key == Qt.Key_Escape:
            self.close()
