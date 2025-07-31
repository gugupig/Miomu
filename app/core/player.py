from typing import List
from PySide6.QtCore import QObject, Signal
from app.models.models import Cue

class SubtitlePlayer(QObject):
    """
    播放控制器。
    只负责管理播放状态（当前行），不负责加载数据。
    """
    # 信号：当台词行发生变化时发射
    cueChanged = Signal(Cue)

    def __init__(self, cues: List[Cue], parent: QObject = None):
        super().__init__(parent)
        self.cues: List[Cue] = cues
        self.idx: int = -1 # 初始索引为-1，表示尚未开始

    # ---------- Public control API ----------
    def next(self):
        self.go(self.idx + 1)

    def prev(self):
        self.go(self.idx - 1)

    def go(self, i: int):
        if not self.cues:
            return
        
        new_idx = max(0, min(i, len(self.cues) - 1))
        
        # 只有在索引真正改变时才发射信号
        if new_idx != self.idx:
            self.idx = new_idx
            self.cueChanged.emit(self.cues[self.idx])

    def go_by_cue_obj(self, cue: Cue):
        """提供一个通过Cue对象跳转的便捷方法"""
        self.go(cue.id - 1)
