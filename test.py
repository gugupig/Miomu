'''
import sys
import json
import argparse
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QSizePolicy, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QFont


class SubtitleModel:
    """管理字幕列表与当前索引"""
    def __init__(self, cues):
        self.cues = cues
        self.idx = 0

    def current(self):
        return self.cues[self.idx]

    def next(self):
        if self.idx < len(self.cues) - 1:
            self.idx += 1
        return self.current()

    def prev(self):
        if self.idx > 0:
            self.idx -= 1
        return self.current()

    def count(self):
        return len(self.cues)

    def position(self):
        return self.idx + 1


class MainWindow(QMainWindow):
    def __init__(self, json_path):
        super().__init__()
        # —— 窗口 & 浮层配置 ——
        self.setGeometry(200, 200, 1000, 200)
        flags = self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # —— 字幕显示 Label ——
        self.subtitle_label = QLabel(self)
        self.subtitle_label.setAlignment(Qt.AlignCenter)
        self.subtitle_label.setFont(QFont("Arial", 36, QFont.Bold))
        self.subtitle_label.setStyleSheet("""
            color: white;
            background-color: rgba(0, 0, 0, 180);
            padding: 20px;
        """)
        self.subtitle_label.setWordWrap(True)
        self.subtitle_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setCentralWidget(self.subtitle_label)

        # —— 加载模型 & 显示首条 ——
        cues = self.load_cues(json_path)
        self.model = SubtitleModel(cues)
        if self.model.count():
            self.show_cue()
        else:
            self.subtitle_label.setText("错误：无可用字幕")

    def load_cues(self, path):
        """从 JSON 文件读取 'cues' 列表"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cues = data.get("cues", [])
            print(f"✔ 成功加载 {len(cues)} 条字幕")
            return cues
        except Exception as e:
            print(f"✘ 加载失败：{e}")
            return []

    def show_cue(self):
        """根据当前索引渲染字幕及窗口标题"""
        cue = self.model.current()
        # 原文 + 双语
        text = f"{cue.get('character','')}: {cue.get('line','')}"
        if cue.get("translation"):
            text += f"\n\n{cue.get('translation')}"
        self.subtitle_label.setText(text)
        # 进度提示
        pos, total = self.model.position(), self.model.count()
        self.setWindowTitle(f"{pos}/{total} — 基本字幕播放器")

    def keyPressEvent(self, event: QKeyEvent):
        """上下箭头切换，Esc 退出"""
        key = event.key()
        if key == Qt.Key_Down:
            self.model.next()
            self.show_cue()
        elif key == Qt.Key_Up:
            self.model.prev()
            self.show_cue()
        elif key == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


def main():
    parser = argparse.ArgumentParser(description="Basic Subtitle Player")
    parser.add_argument("file", nargs="?", help="字幕 JSON 文件路径")
    args = parser.parse_args()

    json_path = args.file
    if not json_path:
        # 弹窗选择
        app = QApplication(sys.argv)
        json_path, _ = QFileDialog.getOpenFileName(
            None, "选择字幕文件", "", "JSON 文件 (*.json)"
        )
        if not json_path:
            sys.exit()

    
    window = MainWindow(json_path)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
'''
import os, sys
os.add_dll_directory(
    r"C:\Program Files\NVIDIA\CUDNN\v9.1\bin\12.4")
import sys, signal, numpy as np
from PySide6.QtCore    import QCoreApplication          # 轻量级，无 GUI
from app.core.audio.audio_hub     import AudioHub
from app.core.stt.whisper_engine  import WhisperEngine

# 1) 启动 Qt 事件循环
app = QCoreApplication(sys.argv)

# 2) 耳朵 + 大脑
hub     = AudioHub(channels=1, samplerate=16_000, frames_per_block=1600)
engine  = WhisperEngine(model_size="tiny", device="cuda", language="zh")

# 3) 接线
hub.blockReady.connect(lambda ch, blk: engine.feed(blk))
engine.segmentReady.connect(lambda ch, piece: print(f"[ch{ch}] {piece.text}"))

engine.start()
hub.start()

print("🎤 Speak into the mic.  Ctrl-C to exit.")
signal.signal(signal.SIGINT, lambda *_: app.quit())

sys.exit(app.exec())     


