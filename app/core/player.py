from typing import List, Optional, Dict
from PySide6.QtCore import QObject, Signal, Slot
from app.models.models import Cue

class SubtitlePlayer(QObject):
    """
    字幕播放控制器
    
    职责：
    1. 管理当前播放状态（当前Cue索引）
    2. 响应Director的Cue切换请求
    3. 提供手动控制接口（next/prev/go）
    4. 通知其他组件Cue变化
    5. 管理多个字幕显示窗口
    """
    # 信号：当台词行发生变化时发射
    cueChanged = Signal(Cue)  # 发射当前Cue对象
    
    # 新增信号：播放状态变化
    playbackStatusChanged = Signal(str)  # 发射状态描述
    
    # 新增信号：多窗口相关
    windowStateChanged = Signal(int, bool)  # 窗口编号, 激活状态
    secondLanguageStateChanged = Signal(int, bool)  # 窗口编号, 第二语言激活状态

    def __init__(self, cues: List[Cue], parent: Optional[QObject] = None):
        super().__init__(parent)
        self.cues: List[Cue] = cues
        self.idx: int = -1  # 初始索引为-1，表示尚未开始
        self._is_playing: bool = False
        
        # 多窗口状态管理
        self.window_states: Dict[int, bool] = {1: True, 2: False, 3: False}  # 窗口激活状态
        self.second_lang_states: Dict[int, bool] = {1: False, 2: False, 3: False}  # 第二语言激活状态
        
        # 字幕显示窗口引用
        self.subtitle_windows: Dict[int, Optional[QObject]] = {1: None, 2: None, 3: None}
        
        print(f"[SubtitlePlayer] Initialized with {len(cues)} cues")
        print(f"[SubtitlePlayer] Window states: {self.window_states}")
        print(f"[SubtitlePlayer] Second language states: {self.second_lang_states}")

    # ---------- 属性访问 ----------
    @property
    def current_cue(self) -> Optional[Cue]:
        """获取当前Cue对象"""
        if 0 <= self.idx < len(self.cues):
            return self.cues[self.idx]
        return None
    
    @property
    def current_index(self) -> int:
        """获取当前索引"""
        return self.idx
    
    @property
    def is_playing(self) -> bool:
        """获取播放状态"""
        return self._is_playing
    
    @property
    def total_cues(self) -> int:
        """获取总Cue数量"""
        return len(self.cues)

    # ---------- Director集成接口 ----------
    @Slot(Cue, str)
    def switch_to_cue(self, target_cue: Cue, reason: str = ""):
        """
        响应Director的Cue切换请求
        
        Args:
            target_cue: 目标Cue对象
            reason: 切换原因（用于日志）
        """
        if not target_cue:
            print("[SubtitlePlayer] Warning: Received None as target_cue")
            return
            
        # 查找目标Cue的索引
        target_idx = self._find_cue_index(target_cue)
        if target_idx is not None:
            old_idx = self.idx
            self.idx = target_idx
            
            print(f"[SubtitlePlayer] Switched to Cue {target_cue.id} (index {target_idx}) - {reason}")
            
            # 发射信号通知变化
            self.cueChanged.emit(target_cue)
            self.playbackStatusChanged.emit(f"Switched to Cue {target_cue.id}: {reason}")
        else:
            print(f"[SubtitlePlayer] Warning: Target Cue {target_cue.id} not found in cues list")
    
    @Slot(Cue)
    def go_by_cue_obj(self, cue: Cue):
        """
        通过Cue对象跳转（兼容接口）
        
        Args:
            cue: 目标Cue对象
        """
        self.switch_to_cue(cue, "Manual/External request")
    
    def _find_cue_index(self, target_cue: Cue) -> Optional[int]:
        """在Cue列表中查找指定Cue的索引"""
        for i, cue in enumerate(self.cues):
            if cue.id == target_cue.id:
                return i
        return None

    # ---------- 手动控制接口 ----------
    def next(self):
        """切换到下一个Cue"""
        self.go(self.idx + 1, "Manual next")

    def prev(self):
        """切换到上一个Cue"""
        self.go(self.idx - 1, "Manual previous")

    def go(self, i: int, reason: str = "Manual navigation"):
        """
        跳转到指定索引的Cue
        
        Args:
            i: 目标索引
            reason: 跳转原因
        """
        if not self.cues:
            print("[SubtitlePlayer] Warning: No cues available")
            return
        
        new_idx = max(0, min(i, len(self.cues) - 1))
        
        # 只有在索引真正改变时才发射信号
        if new_idx != self.idx:
            old_idx = self.idx
            self.idx = new_idx
            current_cue = self.cues[self.idx]
            
            print(f"[SubtitlePlayer] Manual navigation: {old_idx} -> {new_idx} (Cue {current_cue.id}) - {reason}")
            
            self.cueChanged.emit(current_cue)
            self.playbackStatusChanged.emit(f"Manual navigation to Cue {current_cue.id}")

    # ---------- 状态管理 ----------
    def start_playback(self):
        """开始播放"""
        if not self._is_playing:
            self._is_playing = True
            self.playbackStatusChanged.emit("Playback started")
            print("[SubtitlePlayer] Playback started")
    
    def stop_playback(self):
        """停止播放"""
        if self._is_playing:
            self._is_playing = False
            self.playbackStatusChanged.emit("Playback stopped")
            print("[SubtitlePlayer] Playback stopped")
    
    def reset(self):
        """重置到初始状态"""
        self.idx = -1
        self._is_playing = False
        self.playbackStatusChanged.emit("Reset to initial state")
        print("[SubtitlePlayer] Reset to initial state")

    # ---------- 信息获取 ----------
    def get_status(self) -> dict:
        """获取当前播放状态信息"""
        current_cue = self.current_cue
        return {
            "current_index": self.idx,
            "current_cue_id": current_cue.id if current_cue else None,
            "current_cue_line": current_cue.line if current_cue else None,
            "is_playing": self._is_playing,
            "total_cues": len(self.cues),
            "progress_percentage": (self.idx / len(self.cues) * 100) if self.cues else 0,
            "window_states": self.window_states.copy(),
            "second_lang_states": self.second_lang_states.copy()
        }

    # ---------- 多窗口管理 ----------
    def set_window_active(self, window_id: int, active: bool):
        """设置窗口激活状态"""
        if window_id in self.window_states:
            old_state = self.window_states[window_id]
            self.window_states[window_id] = active
            
            if old_state != active:
                print(f"[SubtitlePlayer] Window {window_id} {'activated' if active else 'deactivated'}")
                self.windowStateChanged.emit(window_id, active)
    
    def set_second_language_active(self, window_id: int, active: bool):
        """设置第二语言激活状态"""
        if window_id in self.second_lang_states:
            old_state = self.second_lang_states[window_id]
            self.second_lang_states[window_id] = active
            
            if old_state != active:
                print(f"[SubtitlePlayer] Window {window_id} second language {'activated' if active else 'deactivated'}")
                self.secondLanguageStateChanged.emit(window_id, active)
    
    def get_window_active(self, window_id: int) -> bool:
        """获取窗口激活状态"""
        return self.window_states.get(window_id, False)
    
    def get_second_language_active(self, window_id: int) -> bool:
        """获取第二语言激活状态"""
        return self.second_lang_states.get(window_id, False)
    
    def register_subtitle_window(self, window_id: int, window_obj):
        """注册字幕显示窗口"""
        if window_id in self.subtitle_windows:
            self.subtitle_windows[window_id] = window_obj
            print(f"[SubtitlePlayer] Registered subtitle window {window_id}")
    
    def unregister_subtitle_window(self, window_id: int):
        """注销字幕显示窗口"""
        if window_id in self.subtitle_windows:
            self.subtitle_windows[window_id] = None
            print(f"[SubtitlePlayer] Unregistered subtitle window {window_id}")
    
    def get_active_windows(self) -> List[int]:
        """获取所有激活的窗口ID列表"""
        return [window_id for window_id, active in self.window_states.items() if active]
