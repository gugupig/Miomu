from typing import List
from .base import G2PConverter

try:
    from phonemizer.phonemize import phonemize
    PHONEMIZER_AVAILABLE = True
except ImportError:
    PHONEMIZER_AVAILABLE = False

class PhonemizerG2P(G2PConverter):
    def __init__(self, language: str = 'fr-fr', njobs: int = 4):
        if not PHONEMIZER_AVAILABLE:
            raise ImportError("Phonemizer library is not installed. Please run 'pip install phonemizer'.")
        self.language = language
        self.njobs = njobs
        print(f"[PhonemizerG2P] Initialized for language: {self.language}")

    def convert(self, text: str) -> str:
        # njobs=1 确保在被高频调用时线程安全
        return phonemize(text, language=self.language, backend='espeak', strip=True, njobs=1)

    def batch_convert(self, texts: List[str]) -> List[str]:
        # 批量处理时可以使用多核
        return phonemize(
            texts,
            language=self.language,
            backend="espeak",
            strip=True,
            preserve_punctuation=True,
            njobs=self.njobs
        )