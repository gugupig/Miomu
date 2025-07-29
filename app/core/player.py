import json
from pathlib import Path
from typing import List, Optional
from PySide6.QtCore import QObject, Signal
from app.models.models import Cue

class SubtitlePlayer(QObject):
    cueChanged = Signal(Cue)                       # <- 核心信号

    def __init__(self, script_path: Path | str):
        super().__init__()
        self.cues: List[Cue] = self._load_cues(script_path)
        self.idx: int = 0                          # 起始行

    # ---------- Public control API ----------
    def next(self):
        self.go(self.idx + 1)

    def prev(self):
        self.go(self.idx - 1)

    def go(self, i: int):
        if not self.cues:
            return
        self.idx = max(0, min(i, len(self.cues) - 1))
        self.cueChanged.emit(self.cues[self.idx])

    # ---------- Helpers ----------
    @staticmethod
    def _load_cues(fp) -> List[Cue]:
        with open(fp, encoding="utf-8") as f:
            raw = json.load(f).get("cues", [])
        cues = []
        for r in raw:
            try:
                cues.append(Cue(int(r["id"]), r["character"], r["line"]))
            except KeyError as e:
                print(f"⚠️ 缺字段 {e} -> {r}")
        print(f"Loaded {len(cues)} cues.")
        return cues
