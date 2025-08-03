from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional
from PySide6.QtCore import QObject, Signal

# ---------- 数据结构 ----------
@dataclass
class TranscriptPiece:
    """
    一段增量识别文本
    """
    text: str
    confidence: float           # 0–1 or logprob
    start_ms: Optional[int] = None # 毫秒时间戳 可选）
    end_ms:   Optional[int] = None # 毫秒时间戳 可选）
    is_final: Optional[bool] = False # 是否最终结果 可选）
    uid : Optional[str] = None  # 唯一标识符（可选）

class _STTMeta(type(QObject), ABCMeta):
    """满足 QObject 和 ABC 同时存在的元类"""
    pass

# ---------- 抽象引擎 ----------
class STTEngine(QObject, metaclass=_STTMeta):
    """
    统一语音识别引擎接口。

    用法：
        eng = WhisperEngine(model='medium')
        eng.segmentReady.connect(on_piece)
        eng.speechStarted.connect(on_speech_started)
        eng.start()
        ...
        eng.feed(block)      # 由 AudioHub 推送 PCM
        ...
        eng.stop()
    """
    # Qt 信号：当生成新文本段时发射
    segmentReady = Signal(int, object) 
    #               └── channel id (int)
    
    # Qt 信号：当检测到语音开始时发射（用于 'end' 模式对齐）
    speechStarted = Signal(int)
    #                └── channel id (int)

    def __init__(self, language="auto", channel_id=0):
        super().__init__()
        self.language = language
        self.channel_id = channel_id
        self.running = False

    # -------- 生命周期 --------
    @abstractmethod
    def start(self) -> None:
        """初始化资源（模型、线程、缓冲），准备接受数据。"""
        ...

    @abstractmethod
    def stop(self) -> None:
        """释放资源；之后再调用 feed() 应安全地忽略。"""
        ...

    # -------- 数据入口 --------
    @abstractmethod
    def feed(self, channel_id: int, pcm_block) -> None:
        """
        接收声道ID和PCM数据块。
        
        Args:
            channel_id: 声道编号 (0-based)
            pcm_block: 1D numpy ndarray，采样率 = 16 kHz，float32 [-1,1]
            
        由 AudioHub 在回调线程里调用；必须 **非阻塞**（把数据放进内部队列）。
        """
        ...

    # -------- 可选：动态参数 --------
    def set_vad_threshold(self, value: float) -> None:
        """若引擎内部有 VAD，可在运行期调整门限。"""
        pass

    # -------- 工具：发射信号 --------
    def _emit(self, piece):
        self.segmentReady.emit(self.channel_id, piece)
        
    def _emit_speech_started(self):
        """发射语音开始信号"""
        self.speechStarted.emit(self.channel_id)
