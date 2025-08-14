from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple
from collections import deque

from PySide6.QtCore import QObject, Signal, Slot, QMutex, QMutexLocker
from rapidfuzz.distance import Levenshtein

# -----------------------------------------
# 数据结构（保持与原接口一致）
# -----------------------------------------

@dataclass
class MatchProposal:
    target_cue: Any
    confidence_score: float
    strategy_source: str  # "SPRTHead"
    matched_words: List[str]
    matched_phonemes: List[str]

    @classmethod
    def create_empty_proposal(cls) -> "MatchProposal":
        return cls(
            target_cue=type("EmptyCue", (), {"id": -1, "character": None, "line": ""})(),
            confidence_score=0.0,
            strategy_source="None",
            matched_words=[],
            matched_phonemes=[],
        )

@dataclass
class TargetEntry:
    head_tok: List[str]
    head_phonemes: List[str]
    head_bigrams: List[Tuple[str, str]]
    # NEW: 整句 n-gram（用于锚点救援）
    line_ngrams_tok: List[Tuple[str, ...]]
    line_ngrams_ph: List[Tuple[str, ...]]
    line_ngram_index: Dict[Tuple[str, ...], int]  # 位置索引，用于 head-bias

# -----------------------------------------
# 实用函数
# -----------------------------------------

_TOKEN_SPLIT_RE = re.compile(r"[^\w\s\u00C0-\u017F\u0100-\u024F\u1E00-\u1EFF'-]")

STOPWORDS = {
    "le","la","les","du","de","des","un","une","et","a","à","au","aux","en","y",
    "ou","pour","par","sur","dans","que","qui","quoi","ou","où","je","tu","il","elle",
    "nous","vous","ils","elles","me","te","se","ne","pas","mais","donc","or","ni","car",
    "l","d","j","qu","ce","cet","cette","ces","mon","ma","mes","ton","ta","tes","son","sa","ses"
}
FILLERS = {"hum", "euh", "uh", "mmm"}

def _norm_tokenize(text: str) -> List[str]:
    cleaned = _TOKEN_SPLIT_RE.sub(" ", text.lower())
    toks = [t for t in cleaned.split() if t]
    return toks

def _bigrams(tokens: List[str]) -> List[Tuple[str, str]]:
    return list(zip(tokens, tokens[1:])) if len(tokens) >= 2 else []

def _ngrams(tokens: List[str], n: int) -> List[Tuple[str, ...]]:
    if n <= 1 or len(tokens) < n:
        return []
    return [tuple(tokens[i:i+n]) for i in range(0, len(tokens) - n + 1)]

def _clip(x: float, lo: float = 0.05, hi: float = 0.95) -> float:
    return max(lo, min(hi, x))

def _canon(s: str) -> str:
    # 规范形：去掉黏连符号，统一小写
    return re.sub(r"[’'\-]", "", s.lower())

def _split_clitic(word: str) -> List[str]:
    # NEW: 法语缩合粗拆分：n'avez -> [n, avez]; c'est -> [c, est]; qu'est-ce -> [qu, est, ce]
    w = word.replace("’", "'")
    parts = [p for p in re.split(r"'", w) if p]
    out: List[str] = []
    for p in parts:
        out.extend(_norm_tokenize(p))  # 再过一次规范化，去标点
    return out or (_norm_tokenize(word) or [word.lower()])

# -----------------------------------------
# SPRT 对齐器（只用 head + line-ngram 锚点）
# -----------------------------------------

class Aligner(QObject):
    """
    SPRT 驱动的对齐器（只判定“是否进入下一句”，主要使用每行 head_* 特征；
    新增：利用整句 line_ngram 做锚点救援，容错漏词。）
    """

    standby = Signal()
    suggestionReady = Signal(object)
    currentCueIndexChanged = Signal(int)

    def __init__(self, cues: List[Any], g2p_converter: Any, parent: Optional[QObject] = None, debug: bool = False):
        super().__init__(parent)
        self.cues = cues
        self.g2p = g2p_converter
        self.debug = debug

        # 配置（可按需调参）
        self.config: Dict[str, Any] = {
            # ASR 窗口与 head 对齐
            "ASR_MIN_WORDS": 1,
            "HEAD_MAX_WORDS": 5,

            # SPRT 阈值（对数似然）与连续确认
            "SPRT_A_ON": 2.2,
            "SPRT_B_OFF": -3.0,
            "CONFIRM_FRAMES": 2,
            "LLR_DECAY": 0.90,

            # 判定门槛
            "ON_PROB_MIN": 0.55,
            "PHON_EQ_THR": 0.85,

            # 特征权重
            "W_PREFIX": 0.35,
            "W_BIGRAM": 0.25,
            "W_RARE":   0.20,
            "W_PHON":   0.20,

            # 🔁 重复句头簇（快通道）
            "REPEAT_CLUSTER_ENABLE": True,
            "REPEAT_CLUSTER_PREFIX_N": 2,
            "REPEAT_CLUSTER_LOOKAHEAD": 2,
            "SPRT_A_ON_REPEAT": 2.0,
            "CONFIRM_FRAMES_REPEAT": 1,

            # ✅ 首词投票滑窗（仅在重复簇内启用）
            "FIRSTWORD_WINDOW_ENABLE": True,
            "FIRSTWORD_WINDOW_W": 8,
            "FIRSTWORD_WINDOW_K": 3,
            "FIRSTWORD_WINDOW_MIN_LLR": 1.2,

            # NEW: line-ngram 锚点
            "LINE_NGRAM_N": 3,        # 对齐所用的 n
            "W_ANCHOR": 0.30,         # 锚点权重加入 S
            "ANCHOR_HEAD_BIAS": 0.5,  # 越靠前权重越高（尾部至少乘以 1-0.5=0.5）
        }

        # 状态
        self.current_cue_index: int = -1
        self._mutex = QMutex()
        self._entry: Optional[TargetEntry] = None
        self._next_index: Optional[int] = None

        # SPRT 累计状态
        self._llr: float = 0.0
        self._consec_on: int = 0
        self._last_prob: float = 0.5

        # 重复句头簇状态 & 首词滑窗
        self._in_repeat_cluster: bool = False
        self._firstword_hits: Optional[deque] = deque(maxlen=self.config["FIRSTWORD_WINDOW_W"]) \
            if self.config["FIRSTWORD_WINDOW_ENABLE"] else None

        # 全剧 IDF
        self._idf: Dict[str, float] = self._build_idf()

        self._refresh_target()
        if self.debug:
            print(f"[Aligner/SPRT] Init done. IDF size={len(self._idf)} next={self._next_index} repeat={self._in_repeat_cluster}")

    # -------------------- 外部接口 --------------------

    @Slot(int)
    def update_current_cue_index(self, index: int):
        with QMutexLocker(self._mutex):
            if index != self.current_cue_index:
                self.current_cue_index = index
                self._reset_sprt()
                self._refresh_target()
                if self.debug:
                    print(f"[Aligner/SPRT] current_cue_index -> {index}; next={self._next_index} repeat={self._in_repeat_cluster}")
                self.currentCueIndexChanged.emit(index)
            else:
                self._refresh_target()
                if self.debug:
                    print(f"[Aligner/SPRT] current index unchanged; refreshed next={self._next_index} repeat={self._in_repeat_cluster}")

    @Slot(list)
    def analyze(self, asr_word_list: List[str]):
        """接收最近窗口的 ASR 词序列，进行一次 SPRT 更新。"""
        pending_proposal = None
        pending_index_change = None
        
        with QMutexLocker(self._mutex):
            if self._entry is None or self._next_index is None:
                return

            # ===(0) 预处理：生成规范化 ASR 序列（用于锚点匹配）===
            n = int(self.config.get("LINE_NGRAM_N", 3))
            W_norm: List[str] = []
            for w in asr_word_list:
                if not w or w.lower() in FILLERS:
                    continue
                # 缩合拆分 + 规范化
                for p in _split_clitic(w.lower()):
                    W_norm.append(p)
            W_norm = [t for t in W_norm if t]  # already normalized

            # ===(1) 取目标 head 与 line-ngram===
            H_tok = self._entry.head_tok
            H_pho = self._entry.head_phonemes
            H_bi  = self._entry.head_bigrams
            L_tri = self._entry.line_ngrams_tok
            L_tri_ph = self._entry.line_ngrams_ph
            L_idx = self._entry.line_ngram_index

            m = min(self.config["HEAD_MAX_WORDS"], len(H_tok))
            Hm_tok = H_tok[:m]
            Hm_pho = H_pho[:m] if H_pho else []
            Hm_bi  = [b for b in H_bi if b[0] in set(Hm_tok)]  # 简单裁剪

            # ===(2) 基于 head 的保留（老逻辑）===
            W_raw = [w.lower() for w in asr_word_list if w]
            W_raw = [w for w in W_raw if w not in FILLERS]

            if W_raw:
                try:
                    W_raw_pho = self._words_to_phonemes(W_raw)
                except Exception:
                    W_raw_pho = ["" for _ in W_raw]
            else:
                W_raw_pho = []

            Hm_tok_pho = Hm_pho if Hm_pho else []
            PH_THR = self.config.get("PHON_EQ_THR", 0.85)
            Hm_canon = [_canon(t) for t in Hm_tok]

            W: List[str] = []
            for w, w_ph in zip(W_raw, W_raw_pho):
                wc = _canon(w)
                keep = (w in Hm_tok)
                if not keep:
                    keep = any(h in wc or wc in h for h in Hm_canon)
                if not keep and Hm_tok_pho and w_ph:
                    keep = any(Levenshtein.normalized_similarity(w_ph, hp) >= PH_THR for hp in Hm_tok_pho)
                if keep:
                    W.append(w)

            # ===(2b) 锚点救援：若 head 过滤后证据过弱，用 line_ngram 命中来回填===
            anchor_hit = False
            anchor_bias = 0.0
            anchor_words: List[str] = []
            if n >= 2 and W_norm:
                W_ng = _ngrams(W_norm, n)
                if L_tri:
                    # 用规范形做字典匹配
                    canon_target = {tuple(_canon(t) for t in tri): idx for (tri, idx) in L_idx.items()}
                    for tri in W_ng:
                        key = tuple(_canon(t) for t in tri)
                        if key in canon_target:
                            anchor_hit = True
                            anchor_words = list(tri)
                            # 位置越靠前，bias 越大
                            pos = canon_target[key]
                            total = max(1, len(L_tri) - 1)
                            head_bias = 1.0 - (pos / total) * self.config["ANCHOR_HEAD_BIAS"]
                            anchor_bias = max(0.5, head_bias)  # 最低 0.5（行尾也有分）
                            break

                # 若词面锚点没中，尝试音素锚点
                if not anchor_hit and L_tri_ph:
                    try:
                        W_ph = self._words_to_phonemes(W_norm)
                    except Exception:
                        W_ph = []
                    W_ng_ph = list(zip(*[W_ph[i:] for i in range(n)])) if len(W_ph) >= n else []
                    if W_ng_ph:
                        # 逐个 n-gram 做音素相似匹配
                        thr = self.config.get("PHON_EQ_THR", 0.85)
                        for i, tri_ph in enumerate(W_ng_ph):
                            for j, tgt_ph in enumerate(L_tri_ph):
                                ok = True
                                for a, b in zip(tri_ph, tgt_ph):
                                    if Levenshtein.normalized_similarity(a, b) < thr:
                                        ok = False
                                        break
                                if ok:
                                    anchor_hit = True
                                    anchor_words = list(W_norm[i:i+n])
                                    total = max(1, len(L_tri_ph) - 1)
                                    head_bias = 1.0 - (j / total) * self.config["ANCHOR_HEAD_BIAS"]
                                    anchor_bias = max(0.5, head_bias)
                                    break
                            if anchor_hit:
                                break

            # 当 head 过滤为空/单一非首词时，用锚点回填
            if not W or (len(W) == 1 and not any(_canon(W[0]) == _canon(Hm_tok[0]) for _ in [0] if Hm_tok)):
                if anchor_hit and anchor_words:
                    if self.debug:
                        print(f"[Aligner/SPRT] anchor rescue: {anchor_words} (bias={anchor_bias:.2f})")
                    W = anchor_words[:]  # 用锚点片段喂入特征
                else:
                    # 仍然无证据，跳过
                    if not W:
                        if self.debug:
                            print("[Aligner/SPRT] no head-overlap; skip update")
                            print(f"[Aligner/SPRT] target head={Hm_tok} bigrams={Hm_bi} idx={self._next_index}")
                        if self._firstword_hits is not None:
                            self._firstword_hits.append(0)
                        return
                    if len(W) == 1:
                        if self.debug:
                            print("[Aligner/SPRT] single non-head token; skip update", W)
                            print(f"[Aligner/SPRT] target head={Hm_tok} bigrams={Hm_bi} idx={self._next_index}")
                        if self._firstword_hits is not None:
                            self._firstword_hits.append(0)
                        return

            # ===(3) 特征===
            if self.debug:
                print(f"[Aligner/SPRT] target head={Hm_tok} bigrams={Hm_bi} idx={self._next_index}")
            feats = self._features(W, Hm_tok, Hm_pho, Hm_bi)

            # 合成分数 + 锚点加成
            S = (self.config["W_PREFIX"] * feats["prefix_tok"] +
                 self.config["W_BIGRAM"] * feats["bigram_hit"] +
                 self.config["W_RARE"]   * feats["rare_norm"] +
                 self.config["W_PHON"]   * feats["phon_prefix"])
            if anchor_hit:
                S += self.config["W_ANCHOR"] * anchor_bias
            p_t = _clip(S)
            self._last_prob = p_t

            # SPRT 更新（带衰减）
            self._llr = self._llr * self.config["LLR_DECAY"] + math.log(p_t) - math.log(1 - p_t)

            if self.debug:
                dbg = f"[Aligner/SPRT] W={W} | feats={feats} | "
                if anchor_hit:
                    dbg += f"anchor=1 bias={anchor_bias:.2f} | "
                dbg += f"S={S:.3f} p={p_t:.3f} llr={self._llr:.2f}"
                print(dbg)

            # 连续确认
            on_prob = self.config.get("ON_PROB_MIN", 0.60)
            if p_t >= on_prob:
                self._consec_on += 1
            else:
                self._consec_on = 0

            # 记录首词滑窗
            first_match = False
            if Hm_tok:
                try:
                    W_sel_pho = self._words_to_phonemes(W)
                except Exception:
                    W_sel_pho = ["" for _ in W]
                first_tok = Hm_tok[0]
                first_pho = Hm_pho[0] if Hm_pho else ""
                first_match = any((_canon(w) == _canon(first_tok)) for w in W)
                if (not first_match) and first_pho:
                    PH_THR = self.config.get("PHON_EQ_THR", 0.85)
                    first_match = any(Levenshtein.normalized_similarity(p, first_pho) >= PH_THR for p in W_sel_pho if p)
            if self._firstword_hits is not None:
                self._firstword_hits.append(1 if first_match else 0)

            # ===(4) 判决===
            if self._in_repeat_cluster:
                thr_on = self.config["SPRT_A_ON_REPEAT"]
                needed_frames = self.config["CONFIRM_FRAMES_REPEAT"]
            else:
                thr_on = self.config["SPRT_A_ON"]
                needed_frames = 1 if len(Hm_tok) <= 1 else self.config["CONFIRM_FRAMES"]

            if self._llr >= thr_on and self._consec_on >= needed_frames:
                pending_proposal = self._make_proposal(W, Hm_pho)
                if self.debug:
                    print(f"[Aligner/SPRT] SWITCH -> cue {self._next_index} (p={p_t:.2f}, llr={self._llr:.2f}) [sprt]")
                self.current_cue_index = self._next_index
                pending_index_change = self.current_cue_index
                self._reset_sprt()
                self._refresh_target()
            elif self._in_repeat_cluster and self._firstword_hits is not None:
                K = self.config["FIRSTWORD_WINDOW_K"]
                min_llr = self.config["FIRSTWORD_WINDOW_MIN_LLR"]
                hits = sum(self._firstword_hits)
                if hits >= K and self._llr >= min_llr:
                    pending_proposal = self._make_proposal(W, Hm_pho)
                    if self.debug:
                        print(f"[Aligner/SPRT] SWITCH -> cue {self._next_index} via firstword-window "
                              f"(hits={hits}/{len(self._firstword_hits)}, llr={self._llr:.2f})")
                    self.current_cue_index = self._next_index
                    pending_index_change = self.current_cue_index
                    self._reset_sprt()
                    self._refresh_target()
            elif self._llr <= self.config["SPRT_B_OFF"]:
                if self.debug:
                    print(f"[Aligner/SPRT] strong reject, reset (llr={self._llr:.2f})")
                self._reset_sprt()
        
        # 锁外发射信号
        if pending_proposal is not None:
            if self.debug:
                print(f"[Aligner/SPRT] 🔓 Emitting suggestionReady signal outside lock")
            self.suggestionReady.emit(pending_proposal)
        
        if pending_index_change is not None:
            if self.debug:
                print(f"[Aligner/SPRT] 🔓 Emitting currentCueIndexChanged({pending_index_change}) signal outside lock")
            self.currentCueIndexChanged.emit(pending_index_change)

    # -------------------- 内部实现 --------------------

    def _reset_sprt(self):
        self._llr = 0.0
        self._consec_on = 0
        self._last_prob = 0.5
        if self._firstword_hits is not None:
            self._firstword_hits.clear()

    def _refresh_target(self):
        """基于 current_cue_index 刷新下一句 head 条目，并从 line_ngram 提取可配置长度的 n-gram。"""
        idx = self.current_cue_index + 1
        if idx < len(self.cues):
            cue = self.cues[idx]

            # head
            head_tok = cue.head_tok if getattr(cue, 'head_tok', None) else _norm_tokenize(getattr(cue, 'pure_line', cue.line))[:5]
            head_pho = cue.head_phonemes if getattr(cue, 'head_phonemes', None) else []
            head_bi  = _bigrams(head_tok)  # CHG: 不再依赖 head_ngram，现算

            # line n-gram（NEW）
            n = int(self.config.get("LINE_NGRAM_N", 3))

            # 先尝试从 JSON 读取 line_ngram（可能已经是 n-gram 列表，也可能是整句 token）
            raw_ln = getattr(cue, 'line_ngram', None)
            line_tokens: List[str]
            if isinstance(raw_ln, list):
                if raw_ln and all(isinstance(x, (list, tuple)) for x in raw_ln):
                    # 已经是 n-gram 列表（取与 n 相同长度的）
                    ln_tok = [tuple(t[:n]) for t in raw_ln if isinstance(t, (list, tuple)) and len(t) >= n]
                    line_tokens = []  # 无法恢复整句，后续仅用 n-gram
                elif raw_ln and all(isinstance(x, str) for x in raw_ln):
                    # 是整句 token 列表
                    line_tokens = [x.lower() for x in raw_ln]
                    ln_tok = _ngrams(line_tokens, n)
                else:
                    # 空/未知，退化到从 pure_line 解析
                    line_tokens = _norm_tokenize(getattr(cue, 'pure_line', cue.line))
                    ln_tok = _ngrams(line_tokens, n)
            else:
                # 没有 line_ngram 字段：从整句解析
                line_tokens = _norm_tokenize(getattr(cue, 'pure_line', cue.line))
                ln_tok = _ngrams(line_tokens, n)

            # 音素 n-gram（若可）
            try:
                if line_tokens:
                    ph_all = self._words_to_phonemes(line_tokens)
                    ln_ph = list(zip(*[ph_all[i:] for i in range(n)])) if len(ph_all) >= n else []
                else:
                    # 若只有 n-gram 列表但无整句 tokens，则无法重算音素，保持空
                    ln_ph = []
            except Exception:
                ln_ph = []

            # 建立位置索引（靠前的 trigram 给予更大 bias）
            idx_map: Dict[Tuple[str, ...], int] = {}
            for i, tri in enumerate(ln_tok):
                key = tuple(_canon(t) for t in tri)
                if key not in idx_map:
                    idx_map[key] = i

            self._entry = TargetEntry(
                head_tok=head_tok,
                head_phonemes=head_pho,
                head_bigrams=head_bi,
                line_ngrams_tok=ln_tok,
                line_ngrams_ph=ln_ph,
                line_ngram_index=idx_map,
            )
            self._next_index = idx

            # 检测重复句头簇（沿用旧逻辑）
            self._in_repeat_cluster = False
            if self.config["REPEAT_CLUSTER_ENABLE"]:
                n_pref = min(self.config["REPEAT_CLUSTER_PREFIX_N"], len(head_tok))
                sig = tuple(_canon(t) for t in head_tok[:n_pref]) if n_pref > 0 else ()
                look = self.config["REPEAT_CLUSTER_LOOKAHEAD"]
                same_cnt = 0
                for j in range(1, look + 1):
                    k = idx + j
                    if k >= len(self.cues):
                        break
                    c = self.cues[k]
                    tok_k = c.head_tok if getattr(c, 'head_tok', None) else _norm_tokenize(getattr(c, 'pure_line', c.line))[:5]
                    sig_k = tuple(_canon(t) for t in tok_k[:n_pref]) if n_pref > 0 else ()
                    if sig and sig_k == sig:
                        same_cnt += 1
                self._in_repeat_cluster = (sig != () and same_cnt >= 1)

            if self.debug:
                print(f"[Aligner/SPRT] _refresh_target -> next={self._next_index}, head={head_tok}, "
                      f"line_ngram_n={n}, line_tris={len(ln_tok)}, repeat_cluster={self._in_repeat_cluster}")
        else:
            self._entry = None
            self._next_index = None
            self._in_repeat_cluster = False

    def _features(self, W: List[str], H_tok: List[str], H_pho: List[str], H_bi: List[Tuple[str, str]]) -> Dict[str, float]:
        # 1) 词序前缀
        k = len(W)
        if k == 0:
            prefix_tok = 0.0
        else:
            k_eff = min(k, len(H_tok))
            Wk = W[:k_eff]
            if H_pho:
                try:
                    W_pho_pos = self._words_to_phonemes(Wk)
                except Exception:
                    W_pho_pos = ["" for _ in Wk]
            else:
                W_pho_pos = ["" for _ in Wk]
            thr = self.config.get("PHON_EQ_THR", 0.85)
            match_cnt = 0
            for i in range(k_eff):
                tok_ok = (Wk[i] == H_tok[i]) or (_canon(Wk[i]) == _canon(H_tok[i]))
                pho_ok = False
                if H_pho and W_pho_pos[i] and H_pho[i]:
                    pho_ok = Levenshtein.normalized_similarity(W_pho_pos[i], H_pho[i]) >= thr
                if tok_ok or pho_ok:
                    match_cnt += 1
            prefix_tok = match_cnt / max(1, k_eff)

        # 2) bigram 命中（词面 OR 音素）
        W_bi_tok = set(_bigrams(W))
        tok_hit = bool(W_bi_tok and any(b in W_bi_tok for b in H_bi))

        pho_hit = 0.0
        if H_pho:
            try:
                W_pho_all = self._words_to_phonemes(W)
            except Exception:
                W_pho_all = []
            if len(W_pho_all) >= 2 and len(H_pho) >= 2:
                W_bi_ph = list(zip(W_pho_all, W_pho_all[1:]))
                H_bi_ph = list(zip(H_pho, H_pho[1:]))
                thr = self.config.get("PHON_EQ_THR", 0.85)
                for a1, a2 in W_bi_ph:
                    for b1, b2 in H_bi_ph:
                        if (Levenshtein.normalized_similarity(a1, b1) >= thr and
                            Levenshtein.normalized_similarity(a2, b2) >= thr):
                            pho_hit = 1.0
                            break
                    if pho_hit:
                        break
        bigram_hit = 1.0 if (tok_hit or pho_hit) else 0.0

        # 3) 罕见词命中（基于 IDF）
        rare_head = sorted(H_tok, key=lambda t: self._idf.get(t, 1.0), reverse=True)[:2]
        rare_hits = sum(1 for w in W if w in rare_head)
        rare_norm = rare_hits / 2.0

        # 4) 音素前缀相似（若无 phonemes，置 0.5 中性）
        if H_pho:
            try:
                W_pho = self._words_to_phonemes(W)
                k_eff2 = min(len(W_pho), len(H_pho))
                phon_prefix = Levenshtein.normalized_similarity(
                    " ".join(W_pho[:k_eff2]), " ".join(H_pho[:k_eff2])
                ) if k_eff2 > 0 else 0.0
            except Exception:
                phon_prefix = 0.5
        else:
            phon_prefix = 0.5

        return {
            "prefix_tok": float(prefix_tok),
            "bigram_hit": float(bigram_hit),
            "rare_norm": float(rare_norm),
            "phon_prefix": float(phon_prefix),
        }

    def _make_proposal(self, W: List[str], Hm_pho: List[str]) -> MatchProposal:
        try:
            W_pho = self._words_to_phonemes(W)
        except Exception:
            W_pho = [""] * len(W)

        target_cue = self.cues[self._next_index] if self._next_index is not None else None
        conf = self._p_from_llr(self._llr)
        return MatchProposal(
            target_cue=target_cue,
            confidence_score=conf,
            strategy_source="SPRTHead",
            matched_words=W,
            matched_phonemes=W_pho,
        )

    def _p_from_llr(self, llr: float) -> float:
        return 1.0 / (1.0 + math.exp(-llr))

    def _words_to_phonemes(self, words: List[str]) -> List[str]:
        if hasattr(self.g2p, "batch_convert"):
            return self.g2p.batch_convert(words)
        else:
            return [getattr(self.g2p, "convert", lambda x: x)(w) for w in words]

    # -------------------- IDF --------------------

    def _build_idf(self) -> Dict[str, float]:
        df: Dict[str, int] = {}
        N = max(1, len(self.cues))
        for cue in self.cues:
            text = getattr(cue, 'pure_line', '') or cue.line
            toks = set(_norm_tokenize(text))
            for t in toks:
                df[t] = df.get(t, 0) + 1
        return {t: math.log((N + 1) / (c + 1)) + 1.0 for t, c in df.items()}





