import queue, threading
import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal

class AudioHub(QObject):
    """
    统一管控多通道麦克风输入。
    - blockReady 发出单通道 PCM float32 ndarray（shape = (frames,)）
    """
    blockReady = Signal(int, np.ndarray)       # channel, block

    def __init__(self, samplerate=16_000, frames_per_block=1024,
                 channels=1, device=None, silence_thresh=0.01,debug=False):
        super().__init__()
        self.samplerate = samplerate
        self.frames     = frames_per_block
        self.channels   = channels
        self.device     = device
        self.silence_thresh = silence_thresh  # 静音阈值
        self.debug = debug  # 是否打印调试信息

        # 一个队列对应一路通道
        self.queues = [queue.Queue(maxsize=100) for _ in range(channels)]
        self.stream = sd.InputStream(
            samplerate=samplerate,
            blocksize=frames_per_block,
            channels=channels,
            dtype='float32',
            device=device,
            callback=self._callback
        )
        self._running = False

    # ---------- sounddevice 回调 ----------
    def _callback(self, indata, frames, time, status):
        """
        indata shape: (frames, channels) float32 [-1,1]
        仅做轻量拆分→queue，避免阻塞回调线程。
        """
        if status:
            print(f"[AudioHub] ⚠️ {status}")
        # 按列拆分，即各个 channel
        for ch in range(self.channels):
            try:
                # 复制，避免与 sounddevice 缓冲共享内存
                self.queues[ch].put_nowait(indata[:, ch].copy())
            except queue.Full:
                # 下游来不及消费就丢弃最旧的一帧，保持低延迟
                _ = self.queues[ch].get_nowait()
                self.queues[ch].put_nowait(indata[:, ch].copy())

    # ---------- 后台消费线程 ----------
    def _emit_loop(self, ch: int):
        q = self.queues[ch]
        while self._running:
            block = q.get()
            if self.debug:
                # 打印调试信息
                import time
                if not hasattr(self, '_last_print_time') or time.time() - self._last_print_time > 1:
                    print(f"[AudioHub] 正在发射 ch-{ch} 的音频数据, shape={block.shape}, max_vol={np.max(np.abs(block)):.4f}")
                    self._last_print_time = time.time()
            if np.sqrt((block**2).mean()) < self.silence_thresh:
                continue
            self.blockReady.emit(ch, block)

    # ---------- 公共控制 ----------
    def start(self):
        if self._running:
            return
        self._running = True
        self.stream.start()
        # 每通道一个消费线程
        for ch in range(self.channels):
            threading.Thread(target=self._emit_loop, args=(ch,),
                             daemon=True).start()
        print(f"[AudioHub] Started, {self.channels} ch @ {self.samplerate} Hz")

    def stop(self):
        self._running = False
        self.stream.stop()
        print("[AudioHub] Stopped")
