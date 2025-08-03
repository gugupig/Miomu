import threading, queue, time, numpy as np
from pathlib import Path
from faster_whisper import WhisperModel

from app.core.stt.base import STTEngine, TranscriptPiece

class WhisperEngine(STTEngine):
    """
    基于 faster-whisper 的流式 STT：
    - 从 AudioHub 持续 feed PCM float32 [-1,1] @16 kHz
    - 内部 0.8 s 窗 + 50% 重叠推理
    - 使用 vad_filter=True 自动 VAD，低噪声下延迟 ≈ 300-500 ms（GPU）
    """
    def __init__(self,
                 model_size   : str  = "medium",
                 device       : str  = "cuda",      # "cpu" / "cuda" / "auto"
                 compute_type : str  = "int8",      # float16 / int8
                 language     : str  = "zh",
                 channel_id   : int  = 0):
        super().__init__(language, channel_id)
        self.model_size   = model_size
        self.device       = device
        self.compute_type = compute_type

        # 缓冲与线程
        self.block_q      = queue.Queue(maxsize=200)   # 约 16 s
        self.buf          = np.empty((0,), dtype=np.float32)

        # 前缀累积避免重复打印
        self.prev_text    = ""
        
        # 语音状态检测（用于发射 speechStarted 信号）
        self.was_speech_active = False

        # 初始化模型（懒加载到工作线程更安全）
        self._model       = None

    # ---------- 生命周期 ----------
    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._worker_loop,
                         name="WhisperEngineWorker",
                         daemon=True).start()

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.block_q.put(None)
        # 重置语音状态
        self.was_speech_active = False

    # ---------- 数据入口 ----------
    def feed(self, channel_id: int, pcm_block: np.ndarray):
        """
        接收声道ID和PCM数据块
        
        Args:
            channel_id: 声道编号 (0-based)  
            pcm_block: float32 ndarray, 单声道 16 kHz
        """
        if not self.running:
            return
        try:
            # 目前只处理指定声道（通常是channel 0）
            if channel_id == self.channel_id:
                self.block_q.put_nowait(pcm_block.copy())
        except queue.Full:
            # 丢掉最旧块保持实时
            try:
                self.block_q.get_nowait()
                self.block_q.put_nowait(pcm_block.copy())
            except queue.Empty:
                pass

    # ---------- 后台线程 ----------
    def _worker_loop(self):
        # 惰性加载模型，避免阻塞主线程
        self._model = WhisperModel(self.model_size,
                                   device=self.device,
                                   compute_type=self.compute_type)

        WINDOW_SEC = 0.8
        HOP_SEC    = WINDOW_SEC / 2
        SAMPLE_RATE = 16_000
        WIN_SAMPLES = int(WINDOW_SEC * SAMPLE_RATE)
        HOP_SAMPLES = int(HOP_SEC   * SAMPLE_RATE)

        while self.running:
            block = self.block_q.get()
            if block is None:
                break
            # 追加到环形缓冲
            self.buf = np.concatenate([self.buf, block])
            # 如果缓冲超过一窗口，切出推理段
            while len(self.buf) >= WIN_SAMPLES:
                chunk = self.buf[:WIN_SAMPLES].copy()
                self._process_chunk(chunk)
                # 回退一半实现重叠
                self.buf = self.buf[HOP_SAMPLES:]

        print("[WhisperEngine] worker stopped")

    # ---------- 推理 + 发射 ----------
    def _process_chunk(self, samples: np.ndarray):
        """
        samples: float32 [-1,1], len = WIN_SAMPLES
        使用 vad_filter=True → 在纯静音窗口直接返回空列表。
        """
        segments, _ = self._model.transcribe(
            samples,
            language=self.language,
            beam_size=1,
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=300)
        )
        new_text = ""
        has_speech = False
        
        for seg in segments:
            # segment.text 自带空格/标点
            new_text += seg.text.strip() + " "
            has_speech = True

        new_text = new_text.strip()
        
        # 检测语音开始：从无语音状态转为有语音状态
        if has_speech and not self.was_speech_active:
            self.was_speech_active = True
            self._emit_speech_started()
        elif not has_speech:
            self.was_speech_active = False
        
        if not new_text:
            return

        # 仅当文本真正变化时发射
        if new_text != self.prev_text:
            self.prev_text = new_text
            self._emit(TranscriptPiece(text=new_text, confidence=0.7))
