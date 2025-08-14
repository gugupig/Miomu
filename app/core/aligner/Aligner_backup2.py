from __future__ import annotations

import re
from typing import Optional, List, Tuple, Dict, Any
from dataclasses import dataclass
from PySide6.QtCore import QObject, Signal, Slot, QMutex, QMutexLocker
from rapidfuzz import fuzz

from app.core.g2p.base import G2PConverter
from app.models.models import Cue


@dataclass
class MatchProposal:
    """匹配提案数据结构"""
    target_cue: Cue
    confidence_score: float
    strategy_source: str  # "BridgeNext", "BridgeSubsequent", "FallbackHead"
    matched_words: List[str]
    matched_phonemes: List[str]
    
    @classmethod
    def create_empty_proposal(cls) -> 'MatchProposal':
        """创建空提案，表示没有找到匹配"""
        from app.models.models import Cue
        
        # 创建一个特殊的空Cue对象
        empty_cue = Cue(
            id=-1,  # 特殊ID表示空提案
            character=None,
            line=""
        )
        
        return cls(
            target_cue=empty_cue,
            confidence_score=0.0,
            strategy_source="None",
            matched_words=[],
            matched_phonemes=[]
        )


@dataclass
class TargetEntry:
    """目标台词条目数据结构"""
    head_tok: List[str]
    head_phonemes: List[str]
    bridge_tok: List[str]
    bridge_phonemes: List[str]


class Aligner(QObject):
    """
    重构后的智能对齐器模块 (v4.0)
    专注于分析和建议，不再直接控制播放器
    向Director报告匹配提案
    
    Args:
        cues: 台词列表
        g2p_converter: 音素转换器
        parent: Qt父对象
        debug: 是否启用调试模式
        force_use_layer: 强制使用指定层级，-1表示使用所有层，1-3分别表示只使用对应层级
    """
    
    # 信号定义
    standby = Signal()  # 待机信号
    suggestionReady = Signal(object)  # 发送MatchProposal对象
    currentCueIndexChanged = Signal(int)  # 通知Director当前Cue索引已更新

    def __init__(self, cues: 'List[Cue]', g2p_converter: 'G2PConverter', parent: 'Optional[QObject]' = None, debug: bool = False, force_use_layer: int = -1):
        super().__init__(parent)
        
        self.cues = cues
        self.g2p_converter = g2p_converter
        self.debug = debug  # 是否启用调试模式
        self.force_use_layer = force_use_layer  # 强制使用指定层，-1表示使用所有层
        # 配置参数
        self.config = {
            "BRIDGE_HIGH_THRESHOLD": 85,  # Bridge匹配高阈值
            "HEAD_FALLBACK_THRESHOLD": 70,  # Head后备匹配阈值
            "ASR_BRIDGE_WORDS_COUNT": 3,  # 从ASR截取用于Bridge匹配的词数
            "ASR_HEAD_WORDS_COUNT": 5,  # 从ASR截取用于Head匹配的词数
            "TARGETS_COUNT": 0,  # 目标台词数量
            "TEXT_WEIGHT": 0.4,
            "PHONEME_WEIGHT": 0.6,
            
        }
        
        # 内部状态
        self.alignment_entry: Dict[str, Any] = {}
        self.current_cue_index: int = 0
        
        # 线程安全锁
        self.alignment_mutex = QMutex()
        
        # 构建初始战术地图
        self._update_alignment_entry()
        if self.debug:
            print(f"[Aligner] Initialized with initial alignment_entry: {len(self.alignment_entry)} entries")
        
        if self.force_use_layer != -1:
            print(f"[Aligner] Initialized in analysis mode - reports to Director (Force Layer: {self.force_use_layer})")
        else:
            print("[Aligner] Initialized in analysis mode - reports to Director")

    @Slot(int)
    def update_current_cue_index(self, index: int):
        """接收来自Director的当前台词索引更新"""
        if index != self.current_cue_index:
            self.current_cue_index = index
            self._update_alignment_entry()
            self.currentCueIndexChanged.emit(index)  # 确认收到更新
            if self.debug:
                print(f"[Aligner] Updated current cue index to {index}")
        else:
            # 即使索引相同，也强制更新一次战术地图（适用于初始同步）
            self._update_alignment_entry()
            if self.debug:
                print(f"[Aligner] Refreshed alignment entry for current index {index}")

    def _update_alignment_entry(self):
        """更新内部战术地图（线程安全版本）"""
        if self.debug:
            print(f"[Aligner] Updating alignment entry for current_cue_index: {self.current_cue_index}")
        
        # 构建新的alignment_entry，避免在更新过程中暴露不一致状态
        new_alignment_entry = {
            'current_cue_index': self.current_cue_index
        }
        
        # 计算next_cue_index
        next_index = self.current_cue_index + 1
        if next_index < len(self.cues):
            new_alignment_entry['next_cue_index'] = {
                'entry': self._build_target_entry(next_index),
                'cue_index': next_index
            }
            if self.debug:
                print(f"[Aligner] Added next_cue_index: {next_index}")
        
        # 计算后续的target_cue_index (最多5个)
        for i in range(self.config["TARGETS_COUNT"]):
            target_index = self.current_cue_index + 2 + i  # 从next+1开始
            if target_index < len(self.cues):
                new_alignment_entry[f'target_cue_index_{i+1}'] = {
                    'entry': self._build_target_entry(target_index),
                    'cue_index': target_index
                }
                if self.debug:
                    print(f"[Aligner] Added target_cue_index_{i+1}: {target_index}")
        
        # 原子性替换：使用锁确保读写操作不会冲突
        with QMutexLocker(self.alignment_mutex):
            self.alignment_entry = new_alignment_entry
            
        if self.debug:
            print(f"[Aligner] Alignment entry updated with {len(new_alignment_entry)} entries")

    def _build_target_entry(self, cue_index: int) -> TargetEntry:
        """构建目标台词条目"""
        cue = self.cues[cue_index]
        
        # 使用预处理好的head_tok和head_phonemes
        head_tok = getattr(cue, 'head_tok', [])
        head_phonemes = getattr(cue, 'head_phonemes', [])
        
        # 如果没有预处理数据，则动态提取
        if not head_tok:
            head_tok = self._extract_head_tokens(cue.line, self.config["ASR_HEAD_WORDS_COUNT"])
            head_phonemes = self.g2p_converter.batch_convert(head_tok)
        
        # 动态构建bridge_tok和bridge_phonemes
        bridge_tok, bridge_phonemes = self._build_bridge_tokens(cue_index)
        
        return TargetEntry(
            head_tok=head_tok,
            head_phonemes=head_phonemes,
            bridge_tok=bridge_tok,
            bridge_phonemes=bridge_phonemes
        )

    def _build_bridge_tokens(self, cue_index: int) -> Tuple[List[str], List[str]]:
        """构建bridge词语和音素"""
        bridge_tok = []
        bridge_phonemes = []
        
        # 如果是第一个cue，只使用当前cue的完整head
        if cue_index == 0:
            current_cue = self.cues[cue_index]
            head_tok = getattr(current_cue, 'head_tok', [])
            if not head_tok:
                head_tok = self._extract_head_tokens(current_cue.line, self.config["ASR_HEAD_WORDS_COUNT"])
            bridge_tok = head_tok  # 使用完整的head_tok，不截取
            bridge_phonemes = self.g2p_converter.batch_convert(bridge_tok)
        else:
            # 使用前一个cue的完整tail + 当前cue的完整head
            prev_cue = self.cues[cue_index - 1]
            current_cue = self.cues[cue_index]
            
            # 获取前一个cue的完整tail
            prev_tail = getattr(prev_cue, 'tail_tok', [])
            if not prev_tail:
                prev_tail = self._extract_tail_tokens(prev_cue.line, 2)
            
            # 获取当前cue的完整head
            current_head = getattr(current_cue, 'head_tok', [])
            if not current_head:
                current_head = self._extract_head_tokens(current_cue.line, 2)
            
            # 直接拼接bridge，不截取
            bridge_tok = prev_tail + current_head
            bridge_phonemes = self.g2p_converter.batch_convert(bridge_tok)
        
        return bridge_tok, bridge_phonemes

    def _extract_head_tokens(self, line: str, count: int) -> List[str]:
        """提取台词头部词语"""
        import re
        # 保留重音字符、连字符等多语言字符，只移除标点符号
        # 保留: 字母、数字、空格、重音符、连字符、撇号
        cleaned_line = re.sub(r'[^\w\s\u00C0-\u017F\u0100-\u024F\u1E00-\u1EFF\'-]', ' ', line)
        tokens = [token.strip() for token in cleaned_line.split() if token.strip()]
        return tokens[:count]

    def _extract_tail_tokens(self, line: str, count: int) -> List[str]:
        """提取台词尾部词语"""
        import re
        # 保留重音字符、连字符等多语言字符，只移除标点符号
        # 保留: 字母、数字、空格、重音符、连字符、撇号
        cleaned_line = re.sub(r'[^\w\s\u00C0-\u017F\u0100-\u024F\u1E00-\u1EFF\'-]', ' ', line)
        tokens = [token.strip() for token in cleaned_line.split() if token.strip()]
        return tokens[-count:] if len(tokens) >= count else tokens

    @Slot(list)
    def analyze(self, asr_word_list: List[str]):
        """
        分析ASR词语列表并生成匹配提案
        
        Args:
            asr_word_list: 来自ASR的词语列表
        """
        if not asr_word_list:
            self.suggestionReady.emit(MatchProposal.create_empty_proposal())
            return

        
        
        # 智能预处理：处理ASR词语列表长度不足的情况
        asr_len = len(asr_word_list)
        
        # 如果ASR词语数量不足，使用全部词语
        bridge_count = min(self.config["ASR_BRIDGE_WORDS_COUNT"], asr_len)
        head_count = min(self.config["ASR_HEAD_WORDS_COUNT"], asr_len)
        
        # 当词语数量极少时，调整匹配策略
        if asr_len < 2:
            print(f"[Aligner] Warning: Very few ASR words ({asr_len}), using all available words")
            asr_bridge_words = asr_word_list.copy()
            asr_head_words = asr_word_list.copy()
        else:
            # 正常情况：从末尾取指定数量的词语
            asr_bridge_words = asr_word_list[-bridge_count:] if bridge_count > 0 else []
            asr_head_words = asr_word_list[-head_count:] if head_count > 0 else []
        
        # 获取所有唯一词语，保持顺序
        all_unique_words = list(dict.fromkeys(asr_bridge_words + asr_head_words))
        
        # 防止空词语列表导致的问题
        if not all_unique_words:
            print("[Aligner] Warning: No valid words extracted from ASR, emitting empty proposal")
            self.suggestionReady.emit(MatchProposal.create_empty_proposal())
            return
        
        # 一次性转换所有唯一词语
        try:
            all_phonemes = self.g2p_converter.batch_convert(all_unique_words)
        except Exception as e:
            print(f"[Aligner] Error in phoneme conversion: {e}, using fallback")
            # 如果音素转换失败，使用空音素列表作为后备
            all_phonemes = [""] * len(all_unique_words)
        
        # 创建词语到音素的映射
        word_to_phoneme = dict(zip(all_unique_words, all_phonemes))
        
        # 构建各层所需的音素数据
        asr_bridge_phonemes = [word_to_phoneme[word] for word in asr_bridge_words]
        asr_head_phonemes = [word_to_phoneme[word] for word in asr_head_words]
        
        # 动态调整匹配阈值：当ASR词语数量不足时降低阈值
        adjusted_thresholds = self._calculate_adjusted_thresholds(asr_len)
        
        # 如果指定了force_use_layer，只使用指定的层
        if self.force_use_layer == 1:
            # 只使用第一层：Next Cue Bridge匹配
            proposal = self._layer_1_next_bridge(asr_bridge_words, asr_bridge_phonemes, adjusted_thresholds)
            if self.debug:
                print(f"[Aligner] Force using Layer 1 only")
            if proposal:
                print(f"[Aligner] Forced Layer 1 match found: {proposal.strategy_source}")
                self.suggestionReady.emit(proposal)
            else:
                print("[Aligner] Forced Layer 1 found no match")
                self.suggestionReady.emit(MatchProposal.create_empty_proposal())
            return
            
        elif self.force_use_layer == 2:
            # 只使用第二层：Subsequent Cues Bridge匹配
            proposal = self._layer_2_subsequent_bridge(asr_bridge_words, asr_bridge_phonemes, adjusted_thresholds)
            if self.debug:
                print(f"[Aligner] Force using Layer 2 only")
            if proposal:
                print(f"[Aligner] Forced Layer 2 match found: {proposal.strategy_source}")
                self.suggestionReady.emit(proposal)
            else:
                print("[Aligner] Forced Layer 2 found no match")
                self.suggestionReady.emit(MatchProposal.create_empty_proposal())
            return
            
        elif self.force_use_layer == 3:
            # 只使用第三层：Fallback Head搜索
            proposal = self._layer_3_fallback_head(asr_head_words, asr_head_phonemes, adjusted_thresholds)
            if self.debug:
                print(f"[Aligner] Force using Layer 3 only")
            if proposal:
                print(f"[Aligner] Forced Layer 3 match found: {proposal.strategy_source}")
                self.suggestionReady.emit(proposal)
            else:
                print("[Aligner] Forced Layer 3 found no match")
                self.suggestionReady.emit(MatchProposal.create_empty_proposal())
            return

        # 如果force_use_layer为-1或其他值，使用所有层（默认行为）
        # 第一层：Next Cue Bridge匹配
        proposal = self._layer_1_next_bridge(asr_bridge_words, asr_bridge_phonemes, adjusted_thresholds)
        if self.debug:
            print(f"[Aligner] Layer 1 analysis: "
                  f"ASR Bridge Words: {asr_bridge_words}, "
                  f"ASR Bridge Phonemes: {asr_bridge_phonemes}, "
                  f"Adjusted Thresholds: {adjusted_thresholds}")
        if proposal:
            print(f"[Aligner] Layer 1 match found: {proposal.strategy_source}")
            self.suggestionReady.emit(proposal)
            return

        # 第二层：Subsequent Cues Bridge匹配
        proposal = self._layer_2_subsequent_bridge(asr_bridge_words, asr_bridge_phonemes, adjusted_thresholds)
        if proposal:
            print(f"[Aligner] Layer 2 match found: {proposal.strategy_source}")
            self.suggestionReady.emit(proposal)
            return

        # 第三层：Fallback Head搜索
        proposal = self._layer_3_fallback_head(asr_head_words, asr_head_phonemes, adjusted_thresholds)
        if proposal:
            print(f"[Aligner] Layer 3 match found: {proposal.strategy_source}")
            self.suggestionReady.emit(proposal)
            return

        # 所有层都失败
        print("[Aligner] No match found in any layer")
        self.suggestionReady.emit(MatchProposal.create_empty_proposal())

    def _calculate_adjusted_thresholds(self, asr_word_count: int) -> Dict[str, float]:
        """
        根据ASR词语数量动态调整匹配阈值
        
        Args:
            asr_word_count: ASR词语总数
            
        Returns:
            调整后的阈值字典
        """
        # 基础阈值
        base_bridge_threshold = self.config["BRIDGE_HIGH_THRESHOLD"]
        base_head_threshold = self.config["HEAD_FALLBACK_THRESHOLD"]
        
        # 根据词语数量计算调整因子
        if asr_word_count >= self.config["ASR_BRIDGE_WORDS_COUNT"]:
            # 词语充足，使用标准阈值
            bridge_adjustment = 1.0
        elif asr_word_count >= 2:
            # 词语较少，适度降低阈值（降低5-15%）
            bridge_adjustment = 0.95 - (self.config["ASR_BRIDGE_WORDS_COUNT"] - asr_word_count) * 0.05
        else:
            # 词语极少（1个词），大幅降低阈值（降低20%）
            bridge_adjustment = 0.8
        
        # Head阈值的调整更保守一些
        head_adjustment = max(bridge_adjustment, 0.9)
        
        adjusted_thresholds = {
            "bridge": max(base_bridge_threshold * bridge_adjustment, 50.0),  # 最低不低于50
            "head": max(base_head_threshold * head_adjustment, 50.0)  # 最低不低于50
        }
        
        if bridge_adjustment < 1.0:
            print(f"[Aligner] Adjusted thresholds for {asr_word_count} words: "
                  f"bridge={adjusted_thresholds['bridge']:.1f}, head={adjusted_thresholds['head']:.1f}")
        
        return adjusted_thresholds

    def _layer_1_next_bridge(self, asr_bridge_words: List[str], asr_bridge_phonemes: List[str], 
                            adjusted_thresholds: Dict[str, float]) -> Optional[MatchProposal]:
        """第一层：Next Cue Bridge匹配（线程安全版本）"""
        # 检查输入有效性
        if not asr_bridge_words or not asr_bridge_phonemes:
            print("[Aligner] Layer 1: Empty ASR bridge data, skipping")
            return None
            
        # 安全地获取alignment_entry数据
        if self.debug:
            print("[Aligner] Layer 1: Alignment entry data:", self.alignment_entry)
        with QMutexLocker(self.alignment_mutex):
            if 'next_cue_index' not in self.alignment_entry:
                return None
                
            next_data = self.alignment_entry['next_cue_index'].copy()  # 创建副本避免引用
        
        next_entry = next_data['entry']
        next_cue_index = next_data['cue_index']
        
        # 检查目标数据有效性
        if not next_entry.bridge_tok or not next_entry.bridge_phonemes:
            print("[Aligner] Layer 1: Empty target bridge data, skipping")
            return None
        
        score = self._calculate_dual_score(
            asr_bridge_words, asr_bridge_phonemes,
            next_entry.bridge_tok, next_entry.bridge_phonemes
        )

        bridge_threshold = adjusted_thresholds["bridge"]
        if score >= bridge_threshold:
            return MatchProposal(
                target_cue=self.cues[next_cue_index],
                confidence_score=score,
                strategy_source="BridgeNext",
                matched_words=asr_bridge_words,
                matched_phonemes=asr_bridge_phonemes
            )

        return None

    def _layer_2_subsequent_bridge(self, asr_bridge_words: List[str], asr_bridge_phonemes: List[str],
                                  adjusted_thresholds: Dict[str, float]) -> Optional[MatchProposal]:
        """第二层：Subsequent Cues Bridge匹配（线程安全版本）"""
        # 检查输入有效性
        if not asr_bridge_words or not asr_bridge_phonemes:
            print("[Aligner] Layer 2: Empty ASR bridge data, skipping")
            return None
            
        best_score = 0
        best_cue_index = None

        # 安全地获取所有target_cue数据
        targets_to_check = []
        with QMutexLocker(self.alignment_mutex):
            for i in range(1, self.config["TARGETS_COUNT"]):
                key = f'target_cue_index_{i}'
                if key in self.alignment_entry:
                    targets_to_check.append(self.alignment_entry[key].copy())  # 创建副本

        # 在锁外进行计算密集型操作
        for target_data in targets_to_check:
            entry = target_data['entry']
            cue_index = target_data['cue_index']
            
            # 检查目标数据有效性
            if not entry.bridge_tok or not entry.bridge_phonemes:
                continue
            
            score = self._calculate_dual_score(
                asr_bridge_words, asr_bridge_phonemes,
                entry.bridge_tok, entry.bridge_phonemes
            )

            if score > best_score:
                best_score = score
                best_cue_index = cue_index  # 直接使用存储的索引

        bridge_threshold = adjusted_thresholds["bridge"]
        if best_score >= bridge_threshold and best_cue_index is not None:
            return MatchProposal(
                target_cue=self.cues[best_cue_index],
                confidence_score=best_score,
                strategy_source="BridgeSubsequent",
                matched_words=asr_bridge_words,
                matched_phonemes=asr_bridge_phonemes
            )

        return None

    def _layer_3_fallback_head(self, asr_head_words: List[str], asr_head_phonemes: List[str],
                              adjusted_thresholds: Dict[str, float]) -> Optional[MatchProposal]:
        """第三层：Fallback Head搜索（线程安全版本）"""
        # 检查输入有效性
        if not asr_head_words or not asr_head_phonemes:
            print("[Aligner] Layer 3: Empty ASR head data, skipping")
            return None
            
        best_score = 0
        best_cue_index = None

        # 安全地获取所有需要检查的entries数据
        entries_to_check = []
        with QMutexLocker(self.alignment_mutex):
            # 检查next_cue
            if 'next_cue_index' in self.alignment_entry:
                next_data = self.alignment_entry['next_cue_index'].copy()
                entries_to_check.append((next_data['cue_index'], next_data['entry']))

            # 检查所有target_cue
            for i in range(1, self.config["TARGETS_COUNT"]):
                key = f'target_cue_index_{i}'
                if key in self.alignment_entry:
                    target_data = self.alignment_entry[key].copy()
                    entries_to_check.append((target_data['cue_index'], target_data['entry']))

        # 在锁外进行计算密集型操作
        for cue_index, entry in entries_to_check:
            # 检查目标数据有效性
            if not entry.head_tok or not entry.head_phonemes:
                continue
                
            score = self._calculate_dual_score(
                asr_head_words, asr_head_phonemes,
                entry.head_tok, entry.head_phonemes
            )

            if score > best_score:
                best_score = score
                best_cue_index = cue_index  # 直接使用存储的索引

        head_threshold = adjusted_thresholds["head"]
        if best_score >= head_threshold and best_cue_index is not None:
            return MatchProposal(
                target_cue=self.cues[best_cue_index],
                confidence_score=best_score,
                strategy_source="FallbackHead",
                matched_words=asr_head_words,
                matched_phonemes=asr_head_phonemes
            )

        return None

    def _calculate_dual_score(self, words1: List[str], phonemes1: List[str], 
                             words2: List[str], phonemes2: List[str]) -> float:
        """计算双轨（词+音素）模糊匹配分数"""
        if not words1 or not words2:
            return 0.0

        # 将列表转换为字符串进行匹配
        text1 = ' '.join(words1)
        text2 = ' '.join(words2)
        phoneme1 = ' '.join(phonemes1)
        phoneme2 = ' '.join(phonemes2)

        # 使用partial_ratio作为主要算法，token_sort_ratio作为后备
        text_partial = fuzz.partial_ratio(text1, text2)
        text_token_sort = fuzz.token_sort_ratio(text1, text2)
        text_score = max(text_partial, text_token_sort)  # 取较高分数
        
        phoneme_partial = fuzz.partial_ratio(phoneme1, phoneme2)
        phoneme_token_sort = fuzz.token_sort_ratio(phoneme1, phoneme2)
        phoneme_score = max(phoneme_partial, phoneme_token_sort)  # 取较高分数

        final_score = (self.config["TEXT_WEIGHT"] * text_score +
                      self.config["PHONEME_WEIGHT"] * phoneme_score)

        return final_score