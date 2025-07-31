from abc import ABC, abstractmethod
from typing import List

class G2PConverter(ABC):
    """
    G2P（字素到音素）转换器的抽象基类接口。
    """
    @abstractmethod
    def convert(self, text: str) -> str:
        """转换单个文本字符串。"""
        raise NotImplementedError

    def batch_convert(self, texts: List[str]) -> List[str]:
        """
        （可选优化）批量转换文本字符串列表。
        如果子类不实现，则默认逐个调用convert方法。
        """
        return [self.convert(text) for text in texts]