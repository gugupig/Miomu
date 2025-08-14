"""
字幕窗口管理器

负责管理多个字幕显示窗口的创建、显示、隐藏和销毁
"""

from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QApplication
from app.core.player import SubtitlePlayer
from app.views.enhanced_subtitle_window import EnhancedSubtitleWindow


class SubtitleWindowManager(QObject):
    """字幕窗口管理器"""
    
    # 信号
    windowCreated = Signal(int)  # 窗口创建信号
    windowDestroyed = Signal(int)  # 窗口销毁信号
    windowShown = Signal(int)  # 窗口显示信号
    windowHidden = Signal(int)  # 窗口隐藏信号
    
    def __init__(self, player: SubtitlePlayer, parent=None):
        super().__init__(parent)
        
        self.player = player
        self.windows: Dict[int, Optional[EnhancedSubtitleWindow]] = {}
        
        # 默认窗口位置配置
        self.default_positions = {
            1: (100, 100),   # 窗口1位置
            2: (950, 100),   # 窗口2位置
            3: (525, 550),   # 窗口3位置
        }
        
        self.setup_connections()
        print("[SubtitleWindowManager] Initialized")
    
    def setup_connections(self):
        """设置信号连接"""
        # 连接播放器的窗口状态变化信号
        self.player.windowStateChanged.connect(self.on_window_state_changed)
    
    @Slot(int, bool)
    def on_window_state_changed(self, window_id: int, active: bool):
        """响应窗口状态变化"""
        if active:
            self.show_window(window_id)
        else:
            self.hide_window(window_id)
    
    def create_window(self, window_id: int) -> bool:
        """创建字幕窗口"""
        if window_id in self.windows and self.windows[window_id] is not None:
            print(f"[SubtitleWindowManager] Window {window_id} already exists")
            return False
        
        try:
            # 创建新窗口
            window = EnhancedSubtitleWindow(window_id, self.player)
            
            # 设置窗口位置
            if window_id in self.default_positions:
                x, y = self.default_positions[window_id]
                window.set_window_position(x, y)
            
            # 连接窗口关闭信号
            window.windowClosed.connect(self.on_window_closed)
            
            # 存储窗口引用
            self.windows[window_id] = window
            
            print(f"[SubtitleWindowManager] Created window {window_id}")
            self.windowCreated.emit(window_id)
            return True
            
        except Exception as e:
            print(f"[SubtitleWindowManager] Failed to create window {window_id}: {e}")
            return False
    
    def destroy_window(self, window_id: int) -> bool:
        """销毁字幕窗口"""
        if window_id not in self.windows or self.windows[window_id] is None:
            print(f"[SubtitleWindowManager] Window {window_id} does not exist")
            return False
        
        try:
            window = self.windows[window_id]
            if window is not None:
                window.close()
                window.deleteLater()
                self.windows[window_id] = None
            
            print(f"[SubtitleWindowManager] Destroyed window {window_id}")
            self.windowDestroyed.emit(window_id)
            return True
            
        except Exception as e:
            print(f"[SubtitleWindowManager] Failed to destroy window {window_id}: {e}")
            return False
    
    def show_window(self, window_id: int) -> bool:
        """显示字幕窗口"""
        # 如果窗口不存在，先创建
        if window_id not in self.windows or self.windows[window_id] is None:
            if not self.create_window(window_id):
                return False
        
        try:
            window = self.windows[window_id]
            if window is not None:
                window.show_window()
                
                print(f"[SubtitleWindowManager] Shown window {window_id}")
                self.windowShown.emit(window_id)
                return True
            else:
                return False
            
        except Exception as e:
            print(f"[SubtitleWindowManager] Failed to show window {window_id}: {e}")
            return False
    
    def hide_window(self, window_id: int) -> bool:
        """隐藏字幕窗口"""
        if window_id not in self.windows or self.windows[window_id] is None:
            print(f"[SubtitleWindowManager] Window {window_id} does not exist")
            return False
        
        try:
            window = self.windows[window_id]
            if window is not None:
                window.hide_window()
                
                print(f"[SubtitleWindowManager] Hidden window {window_id}")
                self.windowHidden.emit(window_id)
                return True
            else:
                return False
            
        except Exception as e:
            print(f"[SubtitleWindowManager] Failed to hide window {window_id}: {e}")
            return False
    
    def show_all_windows(self):
        """显示所有激活的窗口"""
        active_windows = self.player.get_active_windows()
        for window_id in active_windows:
            self.show_window(window_id)
        
        print(f"[SubtitleWindowManager] Shown all active windows: {active_windows}")
    
    def hide_all_windows(self):
        """隐藏所有窗口"""
        for window_id, window in self.windows.items():
            if window is not None and window.isVisible():
                self.hide_window(window_id)
        
        print("[SubtitleWindowManager] Hidden all windows")
    
    def destroy_all_windows(self):
        """销毁所有窗口"""
        window_ids = list(self.windows.keys())
        for window_id in window_ids:
            if self.windows[window_id] is not None:
                self.destroy_window(window_id)
        
        print("[SubtitleWindowManager] Destroyed all windows")
    
    @Slot(int)
    def on_window_closed(self, window_id: int):
        """处理窗口关闭事件"""
        if window_id in self.windows:
            self.windows[window_id] = None
            
            # 更新播放器中的窗口状态
            self.player.set_window_active(window_id, False)
            
            print(f"[SubtitleWindowManager] Window {window_id} was closed")
            self.windowDestroyed.emit(window_id)
    
    def get_window(self, window_id: int) -> Optional[EnhancedSubtitleWindow]:
        """获取指定窗口实例"""
        return self.windows.get(window_id)
    
    def is_window_visible(self, window_id: int) -> bool:
        """检查窗口是否可见"""
        window = self.windows.get(window_id)
        return window is not None and window.isVisible()
    
    def get_all_window_info(self) -> Dict[int, dict]:
        """获取所有窗口的信息"""
        info = {}
        for window_id, window in self.windows.items():
            if window is not None:
                info[window_id] = window.get_window_info()
            else:
                info[window_id] = {
                    "window_id": window_id,
                    "exists": False
                }
        return info
    
    def set_window_position(self, window_id: int, x: int, y: int) -> bool:
        """设置窗口位置"""
        window = self.windows.get(window_id)
        if window is not None:
            window.set_window_position(x, y)
            # 更新默认位置
            self.default_positions[window_id] = (x, y)
            return True
        return False
    
    def toggle_window_fullscreen(self, window_id: int) -> bool:
        """切换窗口全屏状态"""
        window = self.windows.get(window_id)
        if window is not None:
            window.toggle_fullscreen()
            return True
        return False
    
    def get_active_window_count(self) -> int:
        """获取激活窗口数量"""
        return len([w for w in self.windows.values() if w is not None and w.isVisible()])
    
    def update_default_position(self, window_id: int, x: int, y: int):
        """更新默认窗口位置"""
        self.default_positions[window_id] = (x, y)
        print(f"[SubtitleWindowManager] Updated default position for window {window_id}: ({x}, {y})")
