import re
from typing import Optional, List, Tuple
from PySide6.QtCore import QObject, Signal, Slot, QTimer
from rapidfuzz import fuzz

from app.core.g2p.base import G2PConverter
from app.models.models import Cue, TranscriptPiece
from app.core.player import SubtitlePlayer
from app.core.stt.base import STTEngine

class Aligner(QObject):
    """
    智能对齐器模块 (v3.2 - Viterbi接口预留)
    - 在'beginning'模式下增加了三层置信度判断逻辑。
    - 预留了_run_viterbi_confirmation接口供未来实现。
    """
    cueMatched = Signal(Cue)
    alignmentUncertain = Signal(bool)

    def __init__(self, player: SubtitlePlayer, stt_engine: STTEngine, cues: list[Cue], 
                 g2p_converter: G2PConverter, 
                 trigger_on: str = 'beginning', 
                 parent: QObject = None):
        super().__init__(parent)
        
        self.player = player
        self.stt_engine = stt_engine
        self.cues = cues
        self.g2p_converter = g2p_converter
        
        # --- 可配置的超参数 ---
        self.config = {
            "trigger_on": trigger_on,
            "WINDOW_SIZE": 10,
            # 'beginning' 模式参数
            "BEGIN_HIGH_CONF_THRESHOLD": 85,  # 高置信度阈值，直接采纳
            "BEGIN_VITERBI_THRESHOLD": 70,    # Viterbi触发阈值 (70-85分之间为不确定区间)
            "BEGIN_UNLOCK_ADVANTAGE": 15,
            "BEGIN_LOCK_DURATION_MS": 1500,
            # 'end' 模式参数
            "END_OF_LINE_WORD_COUNT": 4, "END_OF_LINE_THRESHOLD": 85, "DRAMATIC_PAUSE_TIMEOUT_MS": 3000,
            # 通用参数
            "UNCERTAINTY_TIMEOUT_MS": 8000,
            "TEXT_WEIGHT": 0.4, "PHONEME_WEIGHT": 0.6
        }

        # --- 内部状态机和定时器 (保持不变) ---
        self.current_index: int = 0
        self.pending_cue: Optional[Cue] = None
        
        self.lock_timer = QTimer(self)
        self.lock_timer.setSingleShot(True)
        self.lock_timer.setInterval(self.config["BEGIN_LOCK_DURATION_MS"])
        
        self.dramatic_pause_timer = QTimer(self)
        self.dramatic_pause_timer.setSingleShot(True)
        self.dramatic_pause_timer.setInterval(self.config["DRAMATIC_PAUSE_TIMEOUT_MS"])

        self.uncertainty_timer = QTimer(self)
        self.uncertainty_timer.setSingleShot(True)
        self.uncertainty_timer.setInterval(self.config["UNCERTAINTY_TIMEOUT_MS"])

        print(f"[Aligner] Initialized with trigger mode: '{self.config['trigger_on']}'")
        self._connect_signals()
        self.uncertainty_timer.start()

    def _connect_signals(self):
        self.stt_engine.segmentReady.connect(self.on_stt_result)
        self.stt_engine.speechStarted.connect(self.on_speech_started)
        self.player.cueChanged.connect(self.on_player_cue_changed)
        self.dramatic_pause_timer.timeout.connect(self._on_dramatic_pause_timeout)
        self.uncertainty_timer.timeout.connect(self._on_uncertainty_timeout)

    # ---------- 'beginning' 模式核心逻辑 (已修改) ----------
    def _align_by_beginning(self, piece: TranscriptPiece):
        if self.lock_timer.isActive() or not piece.text:
            return

        self.uncertainty_timer.start()
        
        # 在滑动窗口内寻找最佳匹配
        search_window = self._get_search_window()
        best_match_cue, best_score = self._find_best_match_in_window(piece, search_window)
        
        if best_match_cue is None:
            return

        # 获取当前行的匹配度作为基准
        current_cue = self.cues[self.current_index]
        _, current_score = self._calculate_scores(piece, current_cue)

        # --- 三层置信度决策 ---
        # 1. 高置信度：立即跳转
        if (best_score > self.config["BEGIN_HIGH_CONF_THRESHOLD"] and 
            best_score > current_score + self.config["BEGIN_UNLOCK_ADVANTAGE"]):
            
            self._trigger_jump(best_match_cue, best_score, "Fuzzy Match (High Confidence)")
        
        # 2. 中等置信度：调用Viterbi进行确认 (当前为空接口)
        elif (best_score > self.config["BEGIN_VITERBI_THRESHOLD"] and
              best_score > current_score + self.config["BEGIN_UNLOCK_ADVANTAGE"]):
            
            viterbi_confirmed_cue = self._run_viterbi_confirmation(piece, search_window)
            if viterbi_confirmed_cue:
                self._trigger_jump(viterbi_confirmed_cue, 0, "Viterbi Confirmation")

        # 3. 低置信度：忽略，等待更清晰的语音输入
        else:
            self.alignmentUncertain.emit(True)
            
    # --- Viterbi接口 ---
    def _run_viterbi_confirmation(self, piece: TranscriptPiece, candidates: List[Cue]) -> Optional[Cue]:
        """
        【Viterbi接口占位符】
        当模糊匹配分数处于中等“不确定”区间时，此方法被调用。
        未来将在此实现WFST图的构建和Viterbi搜索。
        
        :param piece: 当前的ASR识别结果。
        :param candidates: 滑动窗口内的候选Cue列表。
        :return: 如果Viterbi确认了一个匹配，则返回对应的Cue对象，否则返回None。
        """
        print(f"[Aligner] Fuzzy match score is ambiguous. Calling Viterbi hook (currently empty)...")
        # --- 未来在此处填充您的WFST和Viterbi逻辑 ---
        # 1. 动态为 'candidates' 构建一个局部的WFST图。
        # 2. 将 piece.text 转换为音素序列。
        # 3. 在图上运行Viterbi算法，找到最佳路径对应的Cue。
        # 4. 如果找到，则 return best_cue_from_viterbi
        return None

    # ---------- 辅助方法和未修改的逻辑 ----------

    def _trigger_jump(self, cue: Cue, score: float, method: str):
        """统一处理跳转逻辑"""
        print(f"[Aligner] Matched ({method}): Jump to Cue {cue.id} with score {score:.2f}.")
        self.cueMatched.emit(cue)
        self.lock_timer.start()
        self.uncertainty_timer.stop()
        self.alignmentUncertain.emit(False)
        
    def _get_search_window(self) -> List[Cue]:
        """获取用于搜索的滑动窗口"""
        start_index = self.current_index + 1
        end_index = start_index + self.config["WINDOW_SIZE"]
        return self.cues[start_index:end_index]
        
    def _find_best_match_in_window(self, piece: TranscriptPiece, search_window: List[Cue]) -> Tuple[Optional[Cue], float]:
        best_score = 0
        best_match_cue = None
        for cue in search_window:
            _, final_score = self._calculate_scores(piece, cue)
            if final_score > best_score:
                best_score = final_score
                best_match_cue = cue
        return best_match_cue, best_score

    # ... 其他所有方法 (_align_by_end, on_player_cue_changed, on_speech_started,
    # _calculate_scores, _is_end_of_line等) 保持不变 ...
    @Slot(Cue)
    def on_player_cue_changed(self, cue: Cue):
        new_index = cue.id - 1
        if new_index == self.current_index: return
        self.current_index = new_index
        self.lock_timer.stop()
        if self.pending_cue:
            self.pending_cue = None
            self.dramatic_pause_timer.stop()
        self.uncertainty_timer.stop()
        self.alignmentUncertain.emit(False)
        print(f"[Aligner] State synced to Cue {cue.id}.")

    @Slot(int, TranscriptPiece)
    def on_stt_result(self, channel_id: int, piece: TranscriptPiece):
        if self.config["trigger_on"] == 'beginning':
            self._align_by_beginning(piece)
        elif self.config["trigger_on"] == 'end':
            self._align_by_end(piece)
            
    @Slot(int)
    def on_speech_started(self, channel_id: int):
        if self.config["trigger_on"] == 'end' and self.pending_cue:
            print(f"[Aligner] Fired (end mode): New speech detected. Emitting Cue {self.pending_cue.id}.")
            self.cueMatched.emit(self.pending_cue)
            self.pending_cue = None
            self.dramatic_pause_timer.stop()
            
    def _align_by_end(self, piece: TranscriptPiece):
        if self.pending_cue or not piece.text: return
        self.uncertainty_timer.start()
        current_cue = self.cues[self.current_index]
        if self._is_end_of_line(piece, current_cue):
            next_cue_index = self._find_next_valid_cue_index(self.current_index)
            if next_cue_index is not None:
                self.pending_cue = self.cues[next_cue_index]
                self.dramatic_pause_timer.start()
                self.uncertainty_timer.stop()
                self.alignmentUncertain.emit(False)
                print(f"[Aligner] Armed (end mode): End of Cue {current_cue.id} detected. Pending Cue {self.pending_cue.id}.")
                
    def _on_dramatic_pause_timeout(self):
        if self.pending_cue:
            print(f"[Aligner] Pending state timed out (end mode): Dramatic pause detected.")
            self.pending_cue = None
            self.alignmentUncertain.emit(True)
            self.uncertainty_timer.start()

    def _on_uncertainty_timeout(self):
        print("[Aligner] ⚠️ Alert: System is uncertain. Requesting operator attention.")
        self.alignmentUncertain.emit(True)

    def _calculate_scores(self, piece: TranscriptPiece, cue: Cue) -> Tuple[str, float]:
        asr_phonemes = self.g2p_converter.convert(piece.text)
        text_score = fuzz.partial_ratio(piece.text, cue.line)
        phoneme_score = fuzz.partial_ratio(asr_phonemes, cue.phonemes)
        final_score = (self.config["TEXT_WEIGHT"] * text_score +
                       self.config["PHONEME_WEIGHT"] * phoneme_score)
        return asr_phonemes, final_score

    def _is_end_of_line(self, piece: TranscriptPiece, current_cue: Cue) -> bool:
        k = self.config["END_OF_LINE_WORD_COUNT"]
        words = re.split(r'(\s+)', current_cue.line)
        words = [w for w in words if w.strip()]
        if not words: return False
        
        if len(words) < k:
            end_of_line_text = current_cue.line
            end_of_line_phonemes = current_cue.phonemes
        else:
            end_of_line_text = "".join(words[-k:])
            end_of_line_phonemes = self.g2p_converter.convert(end_of_line_text)

        _, final_score = self._calculate_scores(piece, Cue(0, "", end_of_line_text, end_of_line_phonemes))
        return final_score > self.config["END_OF_LINE_THRESHOLD"]

    def _find_next_valid_cue_index(self, start_index: int) -> Optional[int]:
        next_index = start_index + 1
        if next_index < len(self.cues): return next_index
        return None