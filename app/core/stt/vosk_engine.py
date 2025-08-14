
'''
import queue, json, threading
from collections import deque
from typing import List

import numpy as np
from vosk import Model, KaldiRecognizer

from app.core.stt.base import STTEngine, TranscriptPiece


class VoskEngine(STTEngine):
    """
    适用于实时舞台字幕的轻量 Vosk 引擎。
    关键点：
    • 仅输出最近 K 个词（滑动窗口），避免 partial 无限增长。
    • 识别器在检测到静默时调用 Result() 以重置内部状态，但 **不** 清空窗口，保证上下文连贯。
    • O(1) 内存 + O(m) 公共前缀增量算法，CPU 负担极低。
    """

    # ----- 可调常量 -----
    WINDOW_SIZE = 8          # 保留最近 K 个词
    SKIP_DUP_TICKS = 2       # 连续多少帧无增量则跳过 _emit

    def __init__(self,
                 model_dir: str = "models/stt/vosk/vosk-model-cn-0.22",
                 lang: str = "zh",
                 channel_id: int = 0):
        super().__init__(lang, channel_id)
        self.model_dir = model_dir
        self.q = queue.Queue(maxsize=120)  # ≈ 12 s 缓冲 (0.1 s × 120)
        self.rec: KaldiRecognizer | None = None

        # 增量 & 窗口状态
        self._last_partial: str = ""
        self._tail_words: deque[str] = deque(maxlen=self.WINDOW_SIZE)
        self._skip_counter: int = 0
        self.FILLER_WORDS = {"hum"}

    # ---------- 生命周期 ----------
    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._worker_loop, daemon=True).start()

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.q.put(None)  # 哑元退出

    # ---------- 数据入口 ----------
    def feed(self, channel_id: int, pcm_block: np.ndarray):
        if not self.running or channel_id != self.channel_id:
            return
        try:
            int16_bytes = (pcm_block * 32767).astype(np.int16).tobytes()
            self.q.put_nowait(int16_bytes)
        except queue.Full:
            # 丢最旧保持实时
            try:
                self.q.get_nowait()
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

    # ---------- 核心处理 ----------
    def _process_chunk(self, chunk: bytes):
        # 1) 喂给识别器
        utter_end = self.rec.AcceptWaveform(chunk)

        # 2) 若句子结束，重置 Vosk 状态（但保留 tail_words）
        if utter_end:
            _ = self.rec.Result()  # 刷新内部缓存，内容无关
            self._last_partial = ""  # diff 基准清零

        # 3) 取新的 partial
        curr = json.loads(self.rec.PartialResult()).get("partial", "")
        if not curr:
            return

        # 4) 计算新增词并更新窗口
        delta = self._get_new_words(self._last_partial, curr)
        if delta:
            for w in delta:
                if w.lower() not in self.FILLER_WORDS:
                    self._tail_words.append(w)
                

        # 5) 限流后输出给上层（aligner）
        if delta or self._skip_counter >= self.SKIP_DUP_TICKS:
            context = " ".join(self._tail_words)
            self._emit(TranscriptPiece(text=context, confidence=0.5))
            self._skip_counter = 0
        else:
            self._skip_counter += 1

        self._last_partial = curr

    # ---------- 工具函数 ----------
    @staticmethod
    def _get_new_words(prev: str, curr: str) -> List[str]:
        """返回 curr 相对于 prev 新增的词列表（按空格分词）"""
        p, c = prev.split(), curr.split()
        i = 0
        while i < len(p) and i < len(c) and p[i] == c[i]:
            i += 1
        return c[i:]
'''



    


from __future__ import annotations

import json
import queue
import threading
from collections import deque
from typing import List, Optional

import numpy as np
from vosk import Model, KaldiRecognizer
from PySide6.QtCore import Signal

from app.core.stt.base import STTEngine, TranscriptPiece


class VoskEngine(STTEngine):
    """
    适用于实时舞台字幕的轻量 Vosk 引擎。
    关键点：
    • 仅输出最近 K 个词（滑动窗口），避免 partial 无限增长。
    • 识别器在检测到静默时调用 Result() 以重置内部状态，但 **不** 清空窗口，保证上下文连贯。
    • O(1) 内存 + O(m) 公共前缀增量算法，CPU 负担极低。
    • （可选）在运行时动态更新 grammar 约束（仅动态 HCLG 小模型有效）。
    """
    
    # 模型就绪信号
    modelReady = Signal()

    # ----- 可调常量 -----
    WINDOW_SIZE = 8          # 保留最近 K 个词
    SKIP_DUP_TICKS = 2       # 连续多少帧无增量则跳过 _emit

    def __init__(
        self,
        model_dir: str = "models/stt/vosk/vosk-model-cn-0.22",
        lang: str = "zh",
        channel_id: int = 0,
        *,
        enable_grammar: bool = False,   # 新增：允许运行时动态 grammar
        allow_unk: bool = False         # 新增：是否在 grammar 中自动包含 "[unk]"
    ):
        super().__init__(lang, channel_id)
        self.model_dir = model_dir
        self.q: queue.Queue[Optional[bytes]] = queue.Queue(maxsize=120)  # ≈ 12 s 缓冲 (0.1 s × 120)
        self.rec: KaldiRecognizer | None = None

        # 增量 & 窗口状态
        self._last_partial: str = ""
        self._tail_words: deque[str] = deque(maxlen=self.WINDOW_SIZE)
        self._skip_counter: int = 0
        self.FILLER_WORDS = {"hum"}

        # grammar 相关
        self.enable_grammar = enable_grammar
        self.allow_unk = allow_unk
        self._ctrl_q: queue.Queue = queue.Queue()     # 控制指令队列（线程安全）
        self._grammar_enabled_warned = False          # 仅用于打印一次性提示

        # 运行状态
        self.running = False

    # ---------- 生命周期 ----------
    def start(self):
        if self.running:
            return
        self.running = True
        threading.Thread(target=self._worker_loop, daemon=True).start()

    def stop(self):
        if not self.running:
            return
        self.running = False
        self.q.put(None)  # 哑元退出
        # 给控制队列也塞一个空以避免阻塞（非必须）
        try:
            self._ctrl_q.put_nowait(("__stop__", None))
        except Exception:
            pass

    # ---------- 外部接口：音频输入 ----------
    def feed(self, channel_id: int, pcm_block: np.ndarray):
        if not self.running or channel_id != self.channel_id:
            return
        try:
            int16_bytes = (pcm_block * 32767).astype(np.int16).tobytes()
            self.q.put_nowait(int16_bytes)
        except queue.Full:
            # 丢最旧保持实时
            try:
                _ = self.q.get_nowait()
                self.q.put_nowait(int16_bytes)
            except queue.Empty:
                pass

    # ---------- 外部接口：动态 grammar ----------
    def set_grammar(self, words: Optional[List[str]]):
        """
        运行时动态更新 grammar 约束（仅在 enable_grammar=True 时生效）。
        建议在短静默期调用；内部会调用一次 Result() 清空 Vosk 的搜索状态。
        """
        if not self.enable_grammar:
            if not self._grammar_enabled_warned:
                print("[VoskEngine] grammar is disabled; call ignored.")
                self._grammar_enabled_warned = True
            return

        words = list(words or [])
        if self.allow_unk and "[unk]" not in words:
            words.append("[unk]")

        try:
            self._ctrl_q.put_nowait(("set_grammar", words))
        except queue.Full:
            # 控制队列基本不会满，这里只是兜底
            print("[VoskEngine] control queue full, grammar update skipped.")

    # ---------- 线程循环 ----------
    def _worker_loop(self):
        model = Model(self.model_dir)
        self.rec = KaldiRecognizer(model, 16_000)
        print("[VoskEngine] recognizer ready")
        
        # 发送模型就绪信号
        self.modelReady.emit()

        while self.running:
            # 先处理控制指令（非阻塞）
            self._drain_ctrl_commands()

            data = self.q.get()
            if data is None:
                break

            self._process_chunk(data)

        print("[VoskEngine] worker stopped")

    # ---------- 控制指令处理 ----------
    def _drain_ctrl_commands(self):
        """
        处理控制队列中的所有待办（避免与 AcceptWaveform 竞争）。
        每次 grammar 更新后，会：
          - 调用 SetGrammar(JSON)
          - 调用 Result() 清空搜索状态
          - 重置 _last_partial（但不清空 tail 窗口）
        """
        if not self.rec:
            return

        while True:
            try:
                cmd, payload = self._ctrl_q.get_nowait()
            except queue.Empty:
                break

            if cmd == "set_grammar":
                try:
                    g = json.dumps(payload or [])
                    self.rec.SetGrammar(g)
                    # 清理当前搜索状态，避免旧假阳性污染
                    _ = self.rec.Result()
                    self._last_partial = ""
                    preview = payload[:5] if payload else []
                    print(f"[VoskEngine] Grammar updated (size={len(payload or [])}): {preview} ...")
                except Exception as e:
                    print(f"[VoskEngine] SetGrammar failed: {e}")
            elif cmd == "__stop__":
                # 无操作，纯占位
                pass

    # ---------- 核心处理 ----------
    def _process_chunk(self, chunk: bytes):
        # 1) 喂给识别器
        utter_end = self.rec.AcceptWaveform(chunk)

        # 2) 若句子结束，重置 Vosk 状态（但保留 tail_words）
        if utter_end:
            _ = self.rec.Result()  # 刷新内部缓存，内容无关
            self._last_partial = ""  # diff 基准清零

        # 3) 取新的 partial
        curr = json.loads(self.rec.PartialResult()).get("partial", "")
        if not curr:
            return

        # 4) 计算新增词并更新窗口
        delta = self._get_new_words(self._last_partial, curr)
        if delta:
            for w in delta:
                if w.lower() not in self.FILLER_WORDS:
                    self._tail_words.append(w)

        # 5) 限流后输出给上层（aligner）
        if delta or self._skip_counter >= self.SKIP_DUP_TICKS:
            context = " ".join(self._tail_words)
            self._emit(TranscriptPiece(text=context, confidence=0.5))
            self._skip_counter = 0
        else:
            self._skip_counter += 1

        self._last_partial = curr

    # ---------- 工具函数 ----------
    @staticmethod
    def _get_new_words(prev: str, curr: str) -> List[str]:
        """返回 curr 相对于 prev 新增的词列表（按空格分词）"""
        p, c = prev.split(), curr.split()
        i = 0
        while i < len(p) and i < len(c) and p[i] == c[i]:
            i += 1
        return c[i:]
