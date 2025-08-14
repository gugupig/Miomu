# TODO :解耦AudioHub与降噪器
import os
import queue
import threading
import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal
import ctypes
from ctypes import c_void_p, c_float, POINTER

# Try importing noisereduce
try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
except ImportError:
    NOISEREDUCE_AVAILABLE = False

class RNNoiseCT:
    """
    Simple RNNoise binding via ctypes.
    """
    FRAME_SIZE = 480  # 30ms @ 16kHz

    def __init__(self, lib_path: str):
        if not os.path.isfile(lib_path):
            raise FileNotFoundError(f"RNNoise 库文件不存在: {lib_path}")
        self.lib = ctypes.cdll.LoadLibrary(lib_path)
        # Setup function signatures
        self.lib.rnnoise_create.restype = c_void_p
        self.lib.rnnoise_destroy.argtypes = [c_void_p]
        self.lib.rnnoise_process_frame.argtypes = [c_void_p, POINTER(c_float), POINTER(c_float)]
        self.state = self.lib.rnnoise_create()

    def filter(self, pcm_block: np.ndarray) -> np.ndarray:
        data = pcm_block.astype(np.float32)
        length = len(data)
        out = np.zeros_like(data)
        for i in range(0, length, self.FRAME_SIZE):
            chunk = data[i:i + self.FRAME_SIZE]
            if chunk.shape[0] < self.FRAME_SIZE:
                padded = np.zeros(self.FRAME_SIZE, dtype=np.float32)
                padded[:chunk.shape[0]] = chunk
                chunk = padded
            in_arr = (c_float * self.FRAME_SIZE)(*chunk)
            out_arr = (c_float * self.FRAME_SIZE)()
            self.lib.rnnoise_process_frame(self.state, in_arr, out_arr)
            processed = np.ctypeslib.as_array(out_arr)
            out[i:i + chunk.shape[0]] = processed[:chunk.shape[0]]
        return out

    def __del__(self):
        try:
            self.lib.rnnoise_destroy(self.state)
        except Exception:
            pass

class AudioHub(QObject):
    """
    管理多通道麦克风输入。
    - blockReady 发出单通道 PCM float32 ndarray
    - 可选预处理：降噪（noisereduce 或 RNNoise）与 AGC
    """
    blockReady = Signal(int, np.ndarray)

    def __init__(
        self,
        samplerate=16_000,
        frames_per_block=1024,
        channels=1,
        device=None,
        silence_thresh=0.01,
        debug=False,
        # 预处理
        enable_denoise=False,
        denoise_method='noisereduce',  # 'noisereduce' or 'rnnoise'
        rnnoise_lib_path: str = None,
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
        self.debug = False

        # 预处理配置
        self.enable_denoise = enable_denoise
        self.denoise_method = denoise_method
        self.enable_agc = enable_agc
        self.target_rms = target_rms
        self.max_gain = max_gain

        # 初始化降噪器
        self.denoiser = None
        if self.enable_denoise:
            if self.denoise_method == 'noisereduce':
                if NOISEREDUCE_AVAILABLE:
                    print("[AudioHub] 使用 noisereduce 降噪")
                else:
                    print("[AudioHub] WARNING: noisereduce 未安装，降噪关闭")
                    self.enable_denoise = False
            elif self.denoise_method == 'rnnoise':
                if not rnnoise_lib_path:
                    raise ValueError("使用 rnnoise 时必须提供 rnnoise_lib_path")
                try:
                    self.denoiser = RNNoiseCT(rnnoise_lib_path)
                    print("[AudioHub] 使用 RNNoise 降噪")
                except Exception as e:
                    print(f"[AudioHub] 初始化 RNNoiseCT 失败：{e}")
                    self.enable_denoise = False
            else:
                raise ValueError(f"未知的降噪方法: {self.denoise_method}")

        # 队列与流
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
        if status:
            print(f"[AudioHub] ⚠️ {status}")
        for ch in range(self.channels):
            try:
                self.queues[ch].put_nowait(indata[:, ch].copy())
            except queue.Full:
                _ = self.queues[ch].get_nowait()
                self.queues[ch].put_nowait(indata[:, ch].copy())

    def _preprocess(self, block: np.ndarray) -> np.ndarray:
        # 降噪
        if self.enable_denoise:
            try:
                if self.denoise_method == 'noisereduce':
                    block = nr.reduce_noise(y=block, sr=self.samplerate, stationary=False)
                elif self.denoise_method == 'rnnoise' and self.denoiser:
                    block = self.denoiser.filter(block)
            except Exception as e:
                if self.debug:
                    print(f"[AudioHub] 降噪出错：{e}")
        # AGC
        if self.enable_agc:
            rms = np.sqrt(np.mean(block**2))
            if rms > 1e-5:
                gain = self.target_rms / rms
                gain = min(gain, self.max_gain)
                block = np.clip(block * gain, -1.0, 1.0)
        return block

    def _emit_loop(self, ch: int):
        q = self.queues[ch]
        while self._running:
            block = q.get()
            if block is None:
                break
            # 静音过滤
            if np.sqrt(np.mean(block**2)) < self.silence_thresh:
                continue
            processed = self._preprocess(block)
            if self.debug:
                import time
                if not hasattr(self, '_last_print_time') or time.time() - self._last_print_time > 1:
                    print(f"[AudioHub] ch-{ch} processed max_vol={np.max(np.abs(processed)):.4f}")
                    self._last_print_time = time.time()
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
        if not self._running:
            return
        self._running = False
        for q in self.queues:
            try: q.put_nowait(None)
            except queue.Full: pass
        self.stream.stop()
        self.stream.close()
        print("[AudioHub] Stopped")

    def set_preprocessing(self, **kwargs):
        # 支持动态更新参数和降噪方法
        for k, v in kwargs.items():
            if hasattr(self, k): setattr(self, k, v)
        print(f"[AudioHub] 预处理更新：denoise={self.enable_denoise}, method={self.denoise_method}, agc={self.enable_agc}")




