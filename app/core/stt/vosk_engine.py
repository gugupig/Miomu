
'''
import queue, json, threading, numpy as np
from vosk import Model, KaldiRecognizer
from app.core.stt.base import STTEngine, TranscriptPiece 

class VoskEngine(STTEngine):
    def __init__(self, model_dir="models/stt/vosk/vosk-model-cn-0.22", lang = 'zh', channel_id=0, debug=False):
        super().__init__(lang, channel_id)
        self.model = Model(model_dir)
        self.rec   = KaldiRecognizer(self.model, 16_000)
        self.q     = queue.Queue(maxsize=200)
        self.debug = debug
        self.buf = bytearray()          # 临时 PCM 缓冲
        self.partial = ""

    def start(self):
        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.running = False

    def feed(self, channel_id: int, pcm_block: np.ndarray):
        """
        channel_id: 声道编号 (0-based)
        pcm_block: float32 ndarray [-1, 1]  *单通道*
        """
        # 注意：Kaldi 接收 16-bit PCM，小数需要转换
        pcm_int16 = (pcm_block * 32767).astype("int16").tobytes()
        self.buf += pcm_int16

        if len(self.buf) >= 32000:      # ≈ 0.6 s @16 kHz * 2 bytes
            chunk = bytes(self.buf)     # ← 转成 bytes!
            self._process(chunk)
            # 回退一半实现 50 % 重叠
            self.buf = self.buf[len(self.buf)//2:]
        

    def _loop(self):
        while self.running:
            data = self.q.get()
            if self.rec.AcceptWaveform(data):
                res = json.loads(self.rec.Result())
                if txt := res.get("text"):
                    piece = TranscriptPiece(text=txt, confidence=0.85)
                    self._emit(piece)                 # ← 只传 dataclass
            else:
                part = json.loads(self.rec.PartialResult()).get("partial")
                if part:
                    piece = TranscriptPiece(text=part, confidence=0.5)
                    self._emit(piece)
    def _process(self, chunk: bytes):
        if self.rec.AcceptWaveform(chunk):
            res = json.loads(self.rec.Result())
            if txt := res.get("text"):
                piece = TranscriptPiece(
                    text      = self.partial + txt,
                    confidence=0.90
                )
                self.partial = ""
                self._emit(piece)
        else:
            part = json.loads(self.rec.PartialResult()).get("partial", "")
            if part:
                self.partial += part
                self._emit(TranscriptPiece(self.partial, 0.50))

'''
import queue, json, threading
import numpy as np
from vosk import Model, KaldiRecognizer

from app.core.stt.base   import STTEngine, TranscriptPiece

class VoskEngine(STTEngine):
    """
    Vosk 实时识别引擎 (单通道).
    - 每次 feed 一个 PCM block (float32 [-1,1])
    - 后台线程从队列取块并调用 KaldiRecognizer
    """
    def __init__(self,
                 model_dir="models/stt/vosk/vosk-model-cn-0.22",
                 lang="zh",
                 channel_id=0):
        super().__init__(lang, channel_id)
        self.model_dir = model_dir
        self.q        = queue.Queue(maxsize=120)      # 约 12 秒缓冲 (0.1s × 120)
        self.rec      = None

        # 用于 partial 去重
        self.prev_part    = ""


    # ---------- 生命周期 ----------
    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._worker_loop,
                         daemon=True).start()

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.q.put(None)                 # 哑元让线程安全退出

    # ---------- 数据入口 ----------
    def feed(self, channel_id: int, pcm_block: np.ndarray):
        """
        接收声道ID和PCM数据块
        
        Args:
            channel_id: 声道编号 (0-based)
            pcm_block: float32 ndarray, 单通道, 16-kHz
        """
        if not self.running:
            return
        try:
            # 目前只处理指定声道（通常是channel 0）
            if channel_id == self.channel_id:
                int16_bytes = (pcm_block * 32767).astype(np.int16).tobytes()
                self.q.put_nowait(int16_bytes)
        except queue.Full:
            # 丢弃最旧帧以保持实时性
            try:
                self.q.get_nowait()
                int16_bytes = (pcm_block * 32767).astype(np.int16).tobytes()
                self.q.put_nowait(int16_bytes)
            except queue.Empty:
                pass

    # ---------- 线程循环 ----------
    def _worker_loop(self):
        model = Model(self.model_dir)
        self.rec = KaldiRecognizer(model, 16_000)
        print("[VoskEngine] recognizer ready")

        while self.running:
            data = self.q.get()
            if data is None:
                break
            self._process_chunk(data)

        print("[VoskEngine] worker stopped")

    # ---------- 核心推理 ----------
    def _process_chunk(self, chunk: bytes):
        self.rec.AcceptWaveform(chunk)

        part = json.loads(self.rec.PartialResult()).get("partial", "")
        if not part:
            return                          # 识别器还没什么可说

        # --- 粗暴去抖逻辑 ---
        if len(part) < len(self.prev_part): # 进入新句，重置
            self.prev_part = ""

        if part != self.prev_part:          # 只有变化才发
            self.prev_part = part
            self._emit(TranscriptPiece(text=part, confidence=0.5))


    ''' # 直接把 latest partial 发出去，不做任何处理，不过会导致信号发送频率非常高
    def _process_chunk(self, chunk: bytes):
        # 喂入解码器；仍然调用 AcceptWaveform 触发内部解码
        self.rec.AcceptWaveform(chunk)

        # 只关心 partial
        part = json.loads(self.rec.PartialResult()).get("partial", "")
        if not part:
            return

        # 直接把 latest partial 发出去
        self._emit(TranscriptPiece(
            text       = part,
            confidence = 0.5,     # 你可用固定值或自己估算
        ))
    '''


