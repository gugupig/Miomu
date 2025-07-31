from dataclasses import dataclass
from typing import Optional

@dataclass
class Cue:
    id: int
    character: str
    line: str
    phonemes: Optional[str] = ""  # 音素转换结果
