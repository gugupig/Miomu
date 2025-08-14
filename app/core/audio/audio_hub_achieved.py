# This is achieved code for audio hub 

# ==============================================================================
# 最简单的音频输入处理类
# ==============================================================================
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


# ==============================================================================
# 加入了简单的降噪和自动增益控制（AGC）
# ==============================================================================

import queue, threading
import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal

class AudioHub(QObject):
    """
    统一管控多通道麦克风输入。
    - blockReady 发出单通道 PCM float32 ndarray（shape = (frames,)）
    - 可选音频降噪（简单噪声门）和自动增益控制（AGC）
    """
    blockReady = Signal(int, np.ndarray)  # channel, processed block

    def __init__(
        self,
        samplerate=16_000,
        frames_per_block=1024,
        channels=1,
        device=None,
        silence_thresh=0.01,
        debug=False,
        # 预处理开关及参数
        enable_denoise=False,
        noise_floor=0.02,
        enable_agc=False,
        target_rms=0.1,
        max_gain=10.0,
    ):
        super().__init__()
        self.samplerate = samplerate
        self.frames = frames_per_block
        self.channels = channels
        self.device = device
        self.silence_thresh = silence_thresh
        self.debug = debug

        # 预处理开关与参数
        self.enable_denoise = enable_denoise
        self.noise_floor = noise_floor
        self.enable_agc = enable_agc
        self.target_rms = target_rms
        self.max_gain = max_gain

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

    def _callback(self, indata, frames, time, status):
        """
        indata shape: (frames, channels) float32 [-1,1]
        仅做轻量拆分→queue，避免阻塞回调线程。
        """
        if status:
            print(f"[AudioHub] ⚠️ {status}")
        for ch in range(self.channels):
            try:
                self.queues[ch].put_nowait(indata[:, ch].copy())
            except queue.Full:
                _ = self.queues[ch].get_nowait()
                self.queues[ch].put_nowait(indata[:, ch].copy())

    def _preprocess(self, block: np.ndarray) -> np.ndarray:
        """
        对音频块执行可选的降噪（噪声门）和 AGC 增益控制
        """
        # 简单噪声门：低于噪声底的样本置零
        if self.enable_denoise:
            mask = np.abs(block) < self.noise_floor
            block = block.copy()
            block[mask] = 0.0

        # 自动增益控制
        if self.enable_agc:
            rms = np.sqrt((block**2).mean())
            if rms > 1e-4:
                gain = self.target_rms / rms
                gain = min(gain, self.max_gain)
                block = block * gain
                block = np.clip(block, -1.0, 1.0)
        return block

    def _emit_loop(self, ch: int):
        q = self.queues[ch]
        while self._running:
            block = q.get()
            # 应用预处理
            processed = self._preprocess(block)
            if self.debug:
                import time
                if not hasattr(self, '_last_print_time') or time.time() - self._last_print_time > 1:
                    print(f"[AudioHub] ch-{ch} processed block, max_vol={np.max(np.abs(processed)):.4f}")
                    self._last_print_time = time.time()
            # 静音过滤
            if np.sqrt((processed**2).mean()) < self.silence_thresh:
                continue
            # 发射处理后音频块
            self.blockReady.emit(ch, processed)

    def start(self):
        if self._running:
            return
        self._running = True
        self.stream.start()
        for ch in range(self.channels):
            threading.Thread(target=self._emit_loop, args=(ch,), daemon=True).start()
        print(f"[AudioHub] Started, {self.channels} ch @ {self.samplerate} Hz")

    def stop(self):
        self._running = False
        self.stream.stop()
        print("[AudioHub] Stopped")

    # 可动态更新预处理配置
    def set_preprocessing(
        self,
        enable_denoise: bool = None,
        noise_floor: float = None,
        enable_agc: bool = None,
        target_rms: float = None,
        max_gain: float = None,
    ):
        if enable_denoise is not None:
            self.enable_denoise = enable_denoise
        if noise_floor is not None:
            self.noise_floor = noise_floor
        if enable_agc is not None:
            self.enable_agc = enable_agc
        if target_rms is not None:
            self.target_rms = target_rms
        if max_gain is not None:
            self.max_gain = max_gain
        print(f"[AudioHub] Preprocessing config updated: denoise={self.enable_denoise}, "
              f"noise_floor={self.noise_floor}, agc={self.enable_agc}, "
              f"target_rms={self.target_rms}, max_gain={self.max_gain}")

