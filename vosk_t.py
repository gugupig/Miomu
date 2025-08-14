# ==============================================================================
#           Vosk Advanced Strategy Tester (words & grammar)
# ==============================================================================
# 这个脚本用于测试Vosk引擎的高级功能：
# 1. set_words(True): 获取每个单词的详细时间戳和置信度。
# 2. set_grammar(...): 将识别限制在一个预定义的词汇表中。

import sys
import queue
import json
import threading
import numpy as np
import logging
from PySide6.QtCore import QObject, Signal, Slot, QCoreApplication

from app.core.audio.audio_hub import AudioHub
from app.core.stt.base import TranscriptPiece
from vosk import Model, KaldiRecognizer

# --- 1. 定义Vosk高级测试引擎 ---

class VoskTester(QObject):
    """
    一个专门用于测试不同Vosk策略的独立引擎。
    增加了对 set_words 和 set_grammar 的支持。
    """
    resultReady = Signal(str, bool)
    errorOccurred = Signal(str)

    def __init__(self, model_path: str, config: dict, parent=None):
        super().__init__(parent)
        self.model_path = model_path
        self.config = config
        
        self.q = queue.Queue(maxsize=150)
        self.rec = None
        self.running = False
        self.worker_thread = None
        
        print(f"[VoskTester] Initialized with config: {self.config}")

    def start(self):
        if self.running: return
        self.running = True
        self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self.worker_thread.start()

    def stop(self):
        if not self.running: return
        self.running = False
        self.q.put(None)
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        print("[VoskTester] Stopped.")

    @Slot(int, np.ndarray)
    def feed(self, channel_id: int, pcm_block: np.ndarray):
        if not self.running: return
        try:
            int16_bytes = (pcm_block * 32767).astype(np.int16).tobytes()
            self.q.put_nowait(int16_bytes)
        except queue.Full:
            pass

    def _worker_loop(self):
        try:
            model = Model(self.model_path)
            self.rec = KaldiRecognizer(model, 16_000)
            
            # --- 核心修改：根据配置应用高级设置 ---
            if self.config.get("use_word_details", False):
                self.rec.SetWords(True)
                print("[VoskTester] Word details enabled.")
            if self.config.get("use_word_details_partial", False):
                self.rec.SetPartialWords(True)
                print("[VoskTester] Partial word details enabled.")
                
            if self.config.get("grammar", None):
                grammar_json = json.dumps(self.config["grammar"])
                self.rec.SetGrammar(grammar_json)
                print(f"[VoskTester] Grammar constrained to: {self.config['grammar'][:5]}...")
                
            print("[VoskTester] Recognizer ready.")

        except Exception as e:
            self.errorOccurred.emit(f"Failed to load Vosk model: {e}")
            return

        last_partial_text = ""
        
        while self.running:
            try:
                timeout = self.config.get("pause_detection_timeout", 0.8)
                data = self.q.get(timeout=timeout)

                if data is None: break

                self.rec.AcceptWaveform(data)

                if self.config.get("emit_partial_results", True):
                    partial_result = json.loads(self.rec.PartialResult())
                    if partial_text := partial_result.get("partial"):
                        if partial_text != last_partial_text:
                            self.resultReady.emit(partial_text, False)
                            last_partial_text = partial_text

            except queue.Empty:
                if not self.rec: continue

                final_result_str = self.rec.Result()
                final_result = json.loads(final_result_str)
                
                # --- 核心修改：解析不同格式的最终结果 ---
                output_text = ""
                # 如果开启了word_details，结果在'result'键中
                if self.config.get("use_word_details", False) and 'result' in final_result:
                    words = final_result['result']
                    full_text = " ".join([w['word'] for w in words])
                    # 我们可以格式化输出，展示每个词的详细信息
                    word_details = [f"{w['word']}({w['conf']:.2f}|{w['start']:.1f}s)" for w in words]
                    output_text = f"{full_text} -> Details: [{' '.join(word_details)}]"
                # 否则，结果在'text'键中
                elif 'text' in final_result:
                    output_text = final_result['text']

                if output_text:
                    if self.config.get("emit_final_results", True):
                         self.resultReady.emit(output_text, True)
                    last_partial_text = ""

        print("[VoskTester] Worker loop finished.")

# --- 2. 定义新的测试配置 ---

# 策略D: 词语细节模式
# 优点: 可以看到每个单词的置信度和时间戳，非常适合分析和调试。
# 缺点: 只在最终结果中提供，不影响部分识别。
CONFIG_WORD_DETAIL = {
    "name": "Word Detail",
    "pause_detection_timeout": 0.8,
    "emit_partial_results": True,
    "emit_final_results": True,
    "use_word_details": True,  # <-- 开启此功能
    "use_word_details_partial": True  # <--- 开启部分识别的词语细节
}

# 策略E: 语法约束模式 (最强大的“纠偏”工具)
# 优点: 强制识别结果落在给定的词汇表中，极大减少奇怪的识别错误。
# 缺点: 如果演员说了词汇表之外的词，会被强制识别成发音最接近的词，可能导致错误。
CONFIG_GRAMMAR_CONSTRAINED = {
    "name": "Grammar Constrained",
    "pause_detection_timeout": 0.8,
    "emit_partial_results": True,
    "emit_final_results": True,
    "grammar": [ # <--- 提供一个法语词汇表示例
        "bonjour", "monde", "le", "la", "un", "une", "salut", "ça", "va",
        "je", "tu", "il", "elle", "nous", "vous", "ils", "elles", "suis",
        "es", "est", "sommes", "êtes", "sont", "parle", "français", "oui",
        "non", "merci", "au", "revoir", "madame", "monsieur"
    ]
}

# (之前的配置也保留，方便对比)
CONFIG_BALANCED = {
    "name": "Balanced",
    "pause_detection_timeout": 0.8,
    "emit_partial_results": True,
    "emit_final_results": True
}

# --- 3. 设置模型和音频源参数 ---

# 🔴 重要: 请将此路径修改为您下载的Vosk法语模型文件夹的路径
MODEL_PATH_FR = "F:/Miomu/Miomu/app/models/stt/vosk/vosk-model-fr-0.22"

AUDIO_HUB_CONFIG = {
    "channels": 1,
    "samplerate": 16000,
    "frames_per_block": 1600,
    "silence_thresh": 0.00,
    "enable_agc": False,
    'enable_denoise': True,
}

# --- 4. 选择并应用配置 ---

# 🟢 在这里选择您想测试的配置
ACTIVE_CONFIG = CONFIG_WORD_DETAIL
#ACTIVE_CONFIG = CONFIG_GRAMMAR_CONSTRAINED
#ACTIVE_CONFIG = CONFIG_BALANCED


# --- 5. 主执行逻辑 ---

import os
if not os.path.isdir(MODEL_PATH_FR):
    print(f"❌ 错误: Vosk模型路径 '{MODEL_PATH_FR}' 不存在或不是一个文件夹。")
else:
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv)

    print("--- Vosk Advanced Strategy Test ---")
    print(f"📈 当前测试配置: {ACTIVE_CONFIG['name']}")
    
    hub = AudioHub(**AUDIO_HUB_CONFIG)

    tester = VoskTester(model_path=MODEL_PATH_FR, config=ACTIVE_CONFIG)

    @Slot(str, bool)
    def on_result(text, is_final):
        prefix = "✅ Final:" if is_final else "✍️ Partial:"
        print(f"{prefix} {text}")

    @Slot(str)
    def on_error(error_message):
        print(f"🔥 错误: {error_message}")

    hub.blockReady.connect(tester.feed)
    tester.resultReady.connect(on_result)
    tester.errorOccurred.connect(on_error)

    tester.start()
    hub.start()

    print("\n🚀 系统已启动，请开始播放法语录音...")
    print("   (在Jupyter中点击'Interrupt the kernel'按钮来停止测试)\n")

    try:
        app.exec()
    finally:
        print("\n⏹️ 正在停止引擎...")
        hub.stop()
        tester.stop()
        print("✅ 测试结束。")