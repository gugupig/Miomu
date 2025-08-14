"""
Director和SubtitlePlayer模块集成工具

提供便捷的函数来正确连接Director和SubtitlePlayer模块，确保双向通信正常工作。
"""

from typing import Optional
from PySide6.QtCore import QObject

from app.core.director.director import Director
from app.core.player import SubtitlePlayer
from app.models.models import Cue


def connect_director_player(director: Director, player: SubtitlePlayer) -> None:
    """
    连接Director和SubtitlePlayer模块，建立双向通信
    
    Args:
        director: Director实例
        player: SubtitlePlayer实例
    """
    print("[Integration] Connecting Director and SubtitlePlayer...")
    
    # 1. Director -> SubtitlePlayer: Cue切换请求
    director.cueChangeRequested.connect(player.switch_to_cue)
    
    # 2. SubtitlePlayer -> Director: Cue变化通知（用于状态同步）
    player.cueChanged.connect(director.sync_current_cue)
    
    print("[Integration] ✅ Director-SubtitlePlayer integration completed")
    print(f"[Integration] - Director can request cue changes to SubtitlePlayer")
    print(f"[Integration] - SubtitlePlayer notifies Director of cue changes")


def verify_director_player_integration(director: Director, player: SubtitlePlayer) -> bool:
    """
    验证Director和SubtitlePlayer的集成是否正确
    
    Returns:
        bool: 集成是否正确
    """
    issues = []
    
    # 检查基本组件
    if not director:
        issues.append("Director instance is None")
    
    if not player:
        issues.append("SubtitlePlayer instance is None")
    
    # 检查数据一致性
    if player.current_cue and director.current_cue:
        if player.current_cue.id != director.current_cue.id:
            issues.append(f"State mismatch: Player at Cue {player.current_cue.id}, Director at Cue {director.current_cue.id}")
    
    # 检查基本属性
    if not hasattr(director, 'cueChangeRequested'):
        issues.append("Director missing cueChangeRequested signal")
    
    if not hasattr(player, 'switch_to_cue'):
        issues.append("SubtitlePlayer missing switch_to_cue method")
    
    if issues:
        print("[Integration] ❌ Integration issues found:")
        for issue in issues:
            print(f"[Integration]   - {issue}")
        return False
    else:
        print("[Integration] ✅ Director-SubtitlePlayer integration verified successfully")
        return True


def test_director_player_integration(director: Director, player: SubtitlePlayer) -> bool:
    """
    测试Director和SubtitlePlayer的集成功能
    
    Returns:
        bool: 测试是否通过
    """
    print("[Integration] Testing Director-SubtitlePlayer integration...")
    
    try:
        # 记录初始状态
        initial_player_idx = player.current_index
        initial_director_cue = director.current_cue
        
        print(f"[Integration] Initial state - Player: {initial_player_idx}, Director: {initial_director_cue.id if initial_director_cue else None}")
        
        # 测试手动Player操作是否同步到Director
        if player.total_cues > 1:
            print("[Integration] Testing manual player navigation...")
            player.next()
            
            # Director应该收到同步通知
            if director.current_cue and player.current_cue:
                if director.current_cue.id == player.current_cue.id:
                    print("[Integration] ✅ Manual player navigation syncs to Director")
                else:
                    print(f"[Integration] ❌ Sync failed: Player {player.current_cue.id} != Director {director.current_cue.id}")
                    return False
        
        print("[Integration] ✅ All integration tests passed")
        return True
        
    except Exception as e:
        print(f"[Integration] ❌ Integration test failed: {e}")
        return False


class DirectorPlayerMonitor(QObject):
    """Director-SubtitlePlayer集成监控器"""
    
    def __init__(self, director: Director, player: SubtitlePlayer):
        super().__init__()
        self.director = director
        self.player = player
        self.cue_changes = 0
        self.director_requests = 0
        self.sync_events = 0
        
        # 连接监控信号
        self._setup_monitoring()
    
    def _setup_monitoring(self):
        """设置监控信号连接"""
        # 监控Director的决策和请求
        self.director.cueChangeRequested.connect(self._on_director_cue_request)
        self.director.decisionMade.connect(self._on_director_decision)
        
        # 监控SubtitlePlayer的变化
        self.player.cueChanged.connect(self._on_player_cue_changed)
        self.player.playbackStatusChanged.connect(self._on_player_status_changed)
    
    def _on_director_cue_request(self, cue: Cue, reason: str):
        """Director请求Cue切换时的回调"""
        self.director_requests += 1
        print(f"[Monitor] Director request #{self.director_requests}: Cue {cue.id} ({reason})")
    
    def _on_director_decision(self, decision_type: str, proposal):
        """Director做出决策时的回调"""
        target_id = proposal.target_cue.id if hasattr(proposal, 'target_cue') else "unknown"
        print(f"[Monitor] Director decision: {decision_type} -> Cue {target_id}")
    
    def _on_player_cue_changed(self, cue: Cue):
        """SubtitlePlayer Cue变化时的回调"""
        self.cue_changes += 1
        print(f"[Monitor] Player change #{self.cue_changes}: now at Cue {cue.id}")
    
    def _on_player_status_changed(self, status: str):
        """SubtitlePlayer状态变化时的回调"""
        print(f"[Monitor] Player status: {status}")
    
    def get_stats(self) -> dict:
        """获取监控统计"""
        return {
            "total_cue_changes": self.cue_changes,
            "director_requests": self.director_requests,
            "sync_events": self.sync_events,
            "current_player_cue": self.player.current_cue.id if self.player.current_cue else None,
            "current_director_cue": self.director.current_cue.id if self.director.current_cue else None,
            "state_synced": (
                self.player.current_cue and self.director.current_cue and 
                self.player.current_cue.id == self.director.current_cue.id
            )
        }
    
    def reset_stats(self):
        """重置统计数据"""
        self.cue_changes = 0
        self.director_requests = 0
        self.sync_events = 0
        print("[Monitor] Statistics reset")


def create_integrated_system(cues: list, parent: Optional[QObject] = None):
    """
    创建一个完整的集成系统，包含Director和SubtitlePlayer
    
    Args:
        cues: Cue列表
        parent: 父QObject
        
    Returns:
        tuple: (director, player, monitor)
    """
    print("[Integration] Creating integrated Director-SubtitlePlayer system...")
    
    # 创建实例
    director = Director(current_cue=cues[0] if cues else None, parent=parent)
    player = SubtitlePlayer(cues, parent=parent)
    
    # 建立连接
    connect_director_player(director, player)
    
    # 创建监控器
    monitor = DirectorPlayerMonitor(director, player)
    
    # 验证集成
    if verify_director_player_integration(director, player):
        print("[Integration] ✅ Integrated system created successfully")
    else:
        print("[Integration] ⚠️ Integrated system created with warnings")
    
    return director, player, monitor


# 便捷的配置预设
class IntegrationPresets:
    """Director-SubtitlePlayer集成预设配置"""
    
    @staticmethod
    def setup_theater_mode(director: Director, player: SubtitlePlayer):
        """剧场模式配置 - 稳定的播放体验"""
        director.update_config("min_confidence_threshold", 0.4)
        director.update_config("auto_unlock_delay_ms", 6000)
        print("[Integration] Theater mode configured")
    
    @staticmethod
    def setup_demo_mode(director: Director, player: SubtitlePlayer):
        """演示模式配置 - 快速响应"""
        director.update_config("min_confidence_threshold", 0.3)
        director.update_config("auto_unlock_delay_ms", 2000)
        print("[Integration] Demo mode configured")
    
    @staticmethod
    def setup_debug_mode(director: Director, player: SubtitlePlayer):
        """调试模式配置 - 详细日志"""
        director.update_config("max_history_size", 200)
        print("[Integration] Debug mode configured")
