from typing import List
from .base import G2PConverter

class SimpleG2P(G2PConverter):
    """
    简单的G2P转换器，用作后备方案
    仅返回原文本作为"音素"结果
    """
    def __init__(self, language: str = 'zh'):
        self.language = language
        print(f"[SimpleG2P] 使用简单G2P转换器，语言: {self.language}")

    def convert(self, text: str) -> str:
        """简单转换：返回原文本"""
        return text.strip()

    def batch_convert(self, texts: List[str]) -> List[str]:
        """批量转换：返回原文本列表"""
        return [text.strip() for text in texts]
