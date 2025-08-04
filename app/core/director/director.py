"""
Director模块 - 字幕显示总调度/裁决者

Director类作为整个字幕系统的核心调度器，统一处理来自多个来源的行号提案：
- Aligner的智能对齐建议
- 人工操作指令
- SituationSense的上下文事件处理

它负责决策逻辑，协调冲突，并最终控制SubtitlePlayer的显示状态。
"""

from typing import Optional, Dict, Any, List, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import inspect
from PySide6.QtCore import QObject, Signal, Slot, QTimer

from app.models.models import Cue


class ProposalSource(Enum):
    """提案来源枚举"""
    MANUAL = "manual"           # 人工操作 (最高优先级，强制覆盖)
    ALIGNER = "aligner"         # 智能对齐器 (正常优先级)


class ProposalPriority(Enum):
    """提案优先级枚举"""
    NORMAL = 1          # ALIGNER
    HIGH = 2            # MANUAL (强制优先级)


@dataclass
class SituationEvent:
    """SituationSense上下文事件数据结构"""
    event_type: str                     # 事件类型标识
    event_data: Dict[str, Any]          # 事件数据
    timestamp: datetime                 # 事件时间戳
    priority: int = 0                   # 事件优先级 (数字越大优先级越高)
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ContextHandler:
    """上下文事件处理器基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
    
    def handle(self, event: SituationEvent, director: 'Director') -> bool:
        """
        处理上下文事件
        
        Args:
            event: 上下文事件对象
            director: Director实例引用
            
        Returns:
            bool: 是否成功处理事件
        """
        raise NotImplementedError("Subclasses must implement handle method")
    
    def can_handle(self, event_type: str) -> bool:
        """检查是否能处理指定类型的事件"""
        return True  # 默认处理所有事件，子类可重写
    
    def enable(self):
        """启用处理器"""
        self.enabled = True
    
    def disable(self):
        """禁用处理器"""
        self.enabled = False


@dataclass
class CueProposal:
    """Cue切换提案数据结构"""
    target_cue: Cue                     # 目标Cue对象
    source: ProposalSource              # 提案来源
    priority: ProposalPriority          # 优先级
    confidence: float                   # 置信度 (0.0-1.0)
    reason: str                         # 提案原因描述
    timestamp: datetime                 # 提案时间戳
    metadata: Optional[Dict[str, Any]] = None     # 额外元数据
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DirectorState(Enum):
    """Director状态枚举"""
    IDLE = "idle"                       # 空闲状态
    PROCESSING = "processing"           # 处理提案中
    LOCKED = "locked"                   # 锁定状态（禁止切换）


class Director(QObject):
    """
    字幕显示总调度/裁决者 (增强版)
    
    功能职责：
    1. 接收来自2个来源的Cue切换提案：MANUAL(强制优先级)、ALIGNER(正常优先级)
    2. 接收并处理来自SituationSense的上下文事件，通过可插拔的handler策略处理
    3. 对每个提案直接进行决策和处理，无收集延迟
    4. MANUAL提案强制覆盖智能系统的所有决定
    5. 防止Aligner在50ms内重复发送相同Cue的提案
    6. 管理锁定状态和自动解锁
    7. 支持上下文事件影响决策过程（配置修改、状态控制、提案过滤等）
    8. 提供决策日志和状态监控
    """
    
    # === 输出信号 ===
    # 通知SubtitlePlayer切换到指定Cue
    cueChangeRequested = Signal(Cue, str)  # (target_cue, reason)
    
    # 状态变化通知
    stateChanged = Signal(DirectorState)
    
    # 决策事件通知（用于调试和监控）
    decisionMade = Signal(str, CueProposal)  # (decision_type, chosen_proposal)
    
    # 冲突解决通知
    conflictResolved = Signal(List[CueProposal], CueProposal)  # (conflicting_proposals, chosen_proposal)
    
    # 提案被拒绝通知
    proposalRejected = Signal(CueProposal, str)  # (rejected_proposal, reason)
    
    # 锁定状态变化
    lockStateChanged = Signal(bool, str)  # (is_locked, reason)
    
    # 上下文事件处理通知
    contextEventProcessed = Signal(str, SituationEvent, bool)  # (handler_name, event, success)
    
    # 配置变化通知
    configurationChanged = Signal(str, object, object)  # (key, old_value, new_value)
    
    # === 输入槽 ===
    # 接收各种来源的Cue切换提案和上下文事件
    
    def __init__(self, current_cue: Optional[Cue] = None, parent: Optional[QObject] = None):
        super().__init__(parent)
        
        # === 核心状态 ===
        self.current_cue: Optional[Cue] = current_cue
        self.state: DirectorState = DirectorState.IDLE
        self.is_locked: bool = False
        self.lock_reason: str = ""
        
        # === 提案管理 ===
        self.pending_proposals: List[CueProposal] = []
        self.proposal_history: List[CueProposal] = []
        self.max_history_size: int = 100
        
        # === 上下文事件处理 ===
        self.context_handlers: Dict[str, List[ContextHandler]] = {}  # event_type -> handlers
        self.global_handlers: List[ContextHandler] = []  # 处理所有事件的全局处理器
        self.event_history: List[SituationEvent] = []
        self.max_event_history_size: int = 50
        
        # === 决策配置 ===
        self.config = {
            # 最小置信度阈值
            "min_confidence_threshold": 0.3,
            
            # 相同来源的提案去重时间窗口（毫秒）- 防止Aligner在50ms内重复发同一Cue
            "dedup_window_ms": 50,
            
            # 自动解锁延迟（毫秒）
            "auto_unlock_delay_ms": 5000,
            
            # 最大历史记录大小
            "max_history_size": 100,
        }
        
        # === 定时器 ===
        # 自动解锁定时器
        self.unlock_timer = QTimer(self)
        self.unlock_timer.setSingleShot(True)
        self.unlock_timer.setInterval(self.config["auto_unlock_delay_ms"])
        self.unlock_timer.timeout.connect(self._auto_unlock)
        
        print(f"[Director] Initialized with current_cue: {current_cue.id if current_cue else 'None'}")
    
    # === 公共API - 接收提案 ===
    
    @Slot(Cue, float, str)
    def receive_aligner_proposal(self, target_cue: Cue, confidence: float, reason: str = ""):
        """接收来自Aligner的Cue切换提案"""
        proposal = CueProposal(
            target_cue=target_cue,
            source=ProposalSource.ALIGNER,
            priority=ProposalPriority.NORMAL,
            confidence=confidence,
            reason=reason or "Aligner suggestion",
            timestamp=datetime.now(),
            metadata={"aligner_score": confidence}
        )
        self._process_proposal(proposal)
    
    @Slot(Cue, str)
    def receive_manual_proposal(self, target_cue: Cue, reason: str = ""):
        """接收来自人工操作的Cue切换提案（最高优先级，强制覆盖）"""
        proposal = CueProposal(
            target_cue=target_cue,
            source=ProposalSource.MANUAL,
            priority=ProposalPriority.HIGH,
            confidence=1.0,  # 人工操作具有最高置信度
            reason=reason or "Manual operation",
            timestamp=datetime.now(),
            metadata={"operator_action": True}
        )
        self._process_proposal(proposal)
    
    # === 上下文事件处理 ===
    
    @Slot(str, dict)
    def receive_context_event(self, event_type: str, event_data: Dict[str, Any]):
        """接收来自SituationSense的上下文事件"""
        event = SituationEvent(
            event_type=event_type,
            event_data=event_data,
            timestamp=datetime.now(),
            priority=event_data.get('priority', 0),
            metadata=event_data.get('metadata', {})
        )
        self._process_context_event(event)
    
    def register_context_handler(self, event_type: str, handler: Union[ContextHandler, Callable[[SituationEvent, 'Director'], bool]]):
        """
        注册上下文事件处理器
        
        Args:
            event_type: 事件类型，为"*"时表示全局处理器
            handler: 处理器实例或处理函数
        """
        # 如果传入的是函数，包装为ContextHandler
        if callable(handler) and not isinstance(handler, ContextHandler):
            handler_name = getattr(handler, '__name__', f'handler_{id(handler)}')
            
            class FunctionHandler(ContextHandler):
                def __init__(self, func, name):
                    super().__init__(name)
                    self.func = func
                
                def handle(self, event: SituationEvent, director: 'Director') -> bool:
                    try:
                        # 检查函数签名
                        sig = inspect.signature(self.func)
                        params = list(sig.parameters.keys())
                        
                        if len(params) == 2:
                            return self.func(event, director)
                        elif len(params) == 1:
                            return self.func(event)
                        else:
                            return self.func()
                    except Exception as e:
                        print(f"[Director] Error in handler {self.name}: {e}")
                        return False
            
            handler = FunctionHandler(handler, handler_name)
        
        if event_type == "*":
            # 全局处理器
            self.global_handlers.append(handler)
            print(f"[Director] Registered global context handler: {handler.name}")
        else:
            # 特定事件类型的处理器
            if event_type not in self.context_handlers:
                self.context_handlers[event_type] = []
            self.context_handlers[event_type].append(handler)
            print(f"[Director] Registered context handler for '{event_type}': {handler.name}")
    
    def unregister_context_handler(self, event_type: str, handler_name: str) -> bool:
        """
        注销上下文事件处理器
        
        Args:
            event_type: 事件类型，为"*"时表示全局处理器
            handler_name: 处理器名称
            
        Returns:
            bool: 是否成功注销
        """
        if event_type == "*":
            # 从全局处理器中移除
            for i, handler in enumerate(self.global_handlers):
                if handler.name == handler_name:
                    del self.global_handlers[i]
                    print(f"[Director] Unregistered global context handler: {handler_name}")
                    return True
        else:
            # 从特定事件处理器中移除
            if event_type in self.context_handlers:
                handlers = self.context_handlers[event_type]
                for i, handler in enumerate(handlers):
                    if handler.name == handler_name:
                        del handlers[i]
                        if not handlers:  # 如果列表为空，删除该事件类型
                            del self.context_handlers[event_type]
                        print(f"[Director] Unregistered context handler for '{event_type}': {handler_name}")
                        return True
        
        print(f"[Director] Handler '{handler_name}' not found for event type '{event_type}'")
        return False
    
    def get_registered_handlers(self) -> Dict[str, List[str]]:
        """获取已注册的处理器列表"""
        result = {}
        
        # 全局处理器
        if self.global_handlers:
            result["*"] = [h.name for h in self.global_handlers]
        
        # 特定事件处理器
        for event_type, handlers in self.context_handlers.items():
            result[event_type] = [h.name for h in handlers]
        
        return result
    
    # === 锁定控制 ===
    
    @Slot(str, int)
    def lock_director(self, reason: str, duration_ms: int = 0):
        """
        锁定Director，禁止Cue切换
        
        Args:
            reason: 锁定原因
            duration_ms: 锁定持续时间（毫秒），0表示手动解锁
        """
        if self.is_locked:
            print(f"[Director] Already locked: {self.lock_reason}")
            return
            
        self.is_locked = True
        self.lock_reason = reason
        self.lockStateChanged.emit(True, reason)
        
        if duration_ms > 0:
            self.unlock_timer.setInterval(duration_ms)
            self.unlock_timer.start()
            
        print(f"[Director] Locked: {reason} (duration: {duration_ms}ms)")
    
    @Slot()
    def unlock_director(self):
        """解锁Director"""
        if not self.is_locked:
            return
            
        self.is_locked = False
        old_reason = self.lock_reason
        self.lock_reason = ""
        self.unlock_timer.stop()
        self.lockStateChanged.emit(False, f"Unlocked from: {old_reason}")
        
        print(f"[Director] Unlocked from: {old_reason}")
    
    # === 状态管理 ===
    
    def get_current_state(self) -> Dict[str, Any]:
        """获取当前Director状态信息"""
        return {
            "current_cue_id": self.current_cue.id if self.current_cue else None,
            "state": self.state.value,
            "is_locked": self.is_locked,
            "lock_reason": self.lock_reason,
            "pending_proposals_count": len(self.pending_proposals),
            "unlock_timer_active": self.unlock_timer.isActive(),
        }
    
    @Slot(Cue)
    def sync_current_cue(self, cue: Cue):
        """同步当前Cue状态（通常由SubtitlePlayer调用）"""
        if self.current_cue != cue:
            old_cue = self.current_cue
            self.current_cue = cue
            print(f"[Director] Current cue synced: {old_cue.id if old_cue else 'None'} -> {cue.id}")
    
    # === 内部实现 ===
    
    def _process_context_event(self, event: SituationEvent):
        """处理上下文事件"""
        print(f"[Director] Processing context event: {event.event_type}")
        
        # 记录事件到历史
        self.event_history.append(event)
        if len(self.event_history) > self.max_event_history_size:
            self.event_history = self.event_history[-self.max_event_history_size:]
        
        # 收集所有匹配的处理器
        handlers_to_run = []
        
        # 添加全局处理器
        handlers_to_run.extend(self.global_handlers)
        
        # 添加特定事件类型的处理器
        if event.event_type in self.context_handlers:
            handlers_to_run.extend(self.context_handlers[event.event_type])
        
        # 按优先级排序处理器（如果处理器有优先级属性）
        handlers_to_run.sort(key=lambda h: getattr(h, 'priority', 0), reverse=True)
        
        # 执行处理器
        for handler in handlers_to_run:
            if not handler.enabled:
                continue
                
            try:
                success = handler.handle(event, self)
                self.contextEventProcessed.emit(handler.name, event, success)
                
                if success:
                    print(f"[Director] Context handler '{handler.name}' processed event '{event.event_type}' successfully")
                else:
                    print(f"[Director] Context handler '{handler.name}' failed to process event '{event.event_type}'")
                    
            except Exception as e:
                print(f"[Director] Error in context handler '{handler.name}': {e}")
                self.contextEventProcessed.emit(handler.name, event, False)
    
    def _process_proposal(self, proposal: CueProposal):
        """直接处理单个提案"""
        # 检查是否被锁定（人工提案可以强制覆盖）
        if self.is_locked and proposal.source != ProposalSource.MANUAL:
            self.proposalRejected.emit(proposal, f"Director is locked: {self.lock_reason}")
            return
        
        # 检查置信度阈值
        if proposal.confidence < self.config["min_confidence_threshold"]:
            self.proposalRejected.emit(proposal, f"Confidence too low: {proposal.confidence}")
            return
        
        # 检查是否是重复提案（仅对Aligner）
        if proposal.source == ProposalSource.ALIGNER and self._is_duplicate_proposal(proposal):
            self.proposalRejected.emit(proposal, "Duplicate proposal within time window")
            return
        
        print(f"[Director] Processing proposal: {proposal.source.value} -> Cue {proposal.target_cue.id} "
              f"(confidence: {proposal.confidence}, priority: {proposal.priority.value})")
        
        # 记录到历史
        self.proposal_history.append(proposal)
        if len(self.proposal_history) > self.max_history_size:
            self.proposal_history = self.proposal_history[-self.max_history_size:]
        
        # 直接执行决策
        self._execute_decision(proposal)
    
    def _is_duplicate_proposal(self, new_proposal: CueProposal) -> bool:
        """检查是否是重复提案 - 比较 target_cue.id + source + timestamp"""
        current_time = datetime.now()
        dedup_window = timedelta(milliseconds=self.config["dedup_window_ms"])
        
        # 检查历史记录中是否有重复提案（在去重窗口内）
        for existing in self.proposal_history:
            if (existing.target_cue.id == new_proposal.target_cue.id and
                existing.source == new_proposal.source and
                current_time - existing.timestamp < dedup_window):
                return True
        return False
    
    def _execute_decision(self, proposal: CueProposal):
        """直接执行单个提案的决策"""
        # 检查是否需要切换
        if (not self.current_cue or 
            proposal.target_cue.id != self.current_cue.id):
            
            # 执行切换
            self._execute_cue_change(proposal)
            self.decisionMade.emit("direct", proposal)
        else:
            print(f"[Director] No change needed: already at Cue {proposal.target_cue.id}")
    
    def _cleanup_old_proposals(self):
        """清理旧的低优先级提案"""
        # 按优先级和时间排序，移除最不重要的提案
        self.pending_proposals.sort(key=lambda p: (p.priority.value, p.timestamp), reverse=True)
        while len(self.pending_proposals) >= self.config["max_concurrent_proposals"]:
            removed = self.pending_proposals.pop()
            self.proposalRejected.emit(removed, "Queue full, removed low priority proposal")
    
    def _process_proposals(self):
        """处理所有待处理的提案"""
        if not self.pending_proposals:
            return
        
        self.state = DirectorState.PROCESSING
        self.stateChanged.emit(self.state)
        
        try:
            # 选择最佳提案
            chosen_proposal = self._select_best_proposal()
            
            if chosen_proposal:
                # 检查是否需要切换
                if (not self.current_cue or 
                    chosen_proposal.target_cue.id != self.current_cue.id):
                    
                    # 执行切换
                    self._execute_cue_change(chosen_proposal)
                else:
                    print(f"[Director] No change needed: already at Cue {chosen_proposal.target_cue.id}")
            
            # 记录所有提案到历史
            self.proposal_history.extend(self.pending_proposals)
            if len(self.proposal_history) > self.max_history_size:
                self.proposal_history = self.proposal_history[-self.max_history_size:]
            
            # 清空待处理提案
            self.pending_proposals.clear()
            
        finally:
            self.state = DirectorState.IDLE
            self.stateChanged.emit(self.state)
    
    def _select_best_proposal(self) -> Optional[CueProposal]:
        """从待处理提案中选择最佳提案"""
        if not self.pending_proposals:
            return None
        
        # 检查冲突提案
        if len(self.pending_proposals) > 1:
            chosen = self._resolve_conflicts()
            if chosen:
                return chosen
        
        # 单个提案或冲突解决后的结果
        if self.pending_proposals:
            chosen = self.pending_proposals[0]
            self.decisionMade.emit("single", chosen)
            return chosen
        
        return None
    
    def _resolve_conflicts(self) -> Optional[CueProposal]:
        """解决冲突提案"""
        # 按优先级分组
        priority_groups = {}
        for proposal in self.pending_proposals:
            priority = proposal.priority.value
            if priority not in priority_groups:
                priority_groups[priority] = []
            priority_groups[priority].append(proposal)
        
        # 选择最高优先级组
        highest_priority = max(priority_groups.keys())
        candidates = priority_groups[highest_priority]
        
        if len(candidates) == 1:
            chosen = candidates[0]
        else:
            # 在同优先级内按置信度选择
            chosen = max(candidates, key=lambda p: p.confidence)
        
        # 发射冲突解决信号
        conflicting = [p for p in self.pending_proposals if p != chosen]
        if conflicting:
            self.conflictResolved.emit(conflicting, chosen)
        
        self.decisionMade.emit("conflict_resolved", chosen)
        return chosen
    
    def _execute_cue_change(self, proposal: CueProposal):
        """执行Cue切换"""
        old_cue = self.current_cue
        self.current_cue = proposal.target_cue
        
        # 发射切换请求信号
        reason = f"{proposal.source.value}: {proposal.reason}"
        self.cueChangeRequested.emit(proposal.target_cue, reason)
        
        print(f"[Director] Cue change executed: {old_cue.id if old_cue else 'None'} -> "
              f"{proposal.target_cue.id} ({reason})")
        
        # 根据提案类型设置临时锁定
        if proposal.source == ProposalSource.ALIGNER:
            # Aligner提案后短暂锁定，避免频繁跳转
            self.lock_director("Post-aligner stabilization", 1500)
        elif proposal.source == ProposalSource.MANUAL:
            # 人工操作后稍长锁定，给操作者确认时间
            self.lock_director("Post-manual confirmation", 2000)
    
    def _auto_unlock(self):
        """自动解锁"""
        self.unlock_director()
    
    def update_config(self, key: str, value: Any):
        """动态更新配置参数"""
        if key in self.config:
            old_value = self.config[key]
            self.config[key] = value
            self.configurationChanged.emit(key, old_value, value)
            print(f"[Director] Config updated: {key} = {old_value} -> {value}")
            
            # 处理特殊配置更新
            if key == "auto_unlock_delay_ms":
                self.unlock_timer.setInterval(value)
        else:
            print(f"[Director] Warning: Unknown config key '{key}'")
    
    def get_config(self, key: str, default=None):
        """获取配置参数"""
        return self.config.get(key, default)
    
    def get_event_history(self, limit: int = 20) -> List[SituationEvent]:
        """获取上下文事件历史记录"""
        return self.event_history[-limit:]
    
    def clear_event_history(self):
        """清空上下文事件历史"""
        self.event_history.clear()
        print("[Director] Context event history cleared")
    
    # === 调试和监控接口 ===
    
    def get_proposal_history(self, limit: int = 20) -> List[CueProposal]:
        """获取提案历史记录"""
        return self.proposal_history[-limit:]
    
    def get_pending_proposals(self) -> List[CueProposal]:
        """获取当前待处理提案"""
        return self.pending_proposals.copy()
    
    def clear_proposal_history(self):
        """清空提案历史"""
        self.proposal_history.clear()
        print("[Director] Proposal history cleared")


# === 预定义上下文事件处理器 ===

class LockingHandler(ContextHandler):
    """锁定控制处理器 - 响应锁定/解锁事件"""
    
    def __init__(self):
        super().__init__("locking_handler")
    
    def handle(self, event: SituationEvent, director: 'Director') -> bool:
        if event.event_type == "lock_request":
            reason = event.event_data.get('reason', 'Context event lock')
            duration = event.event_data.get('duration_ms', 0)
            director.lock_director(reason, duration)
            return True
        elif event.event_type == "unlock_request":
            director.unlock_director()
            return True
        return False
    
    def can_handle(self, event_type: str) -> bool:
        return event_type in ["lock_request", "unlock_request"]


class ConfigurationHandler(ContextHandler):
    """配置修改处理器 - 动态调整配置参数"""
    
    def __init__(self):
        super().__init__("configuration_handler")
    
    def handle(self, event: SituationEvent, director: 'Director') -> bool:
        if event.event_type == "config_change":
            config_updates = event.event_data.get('config_updates', {})
            for key, value in config_updates.items():
                director.update_config(key, value)
            return True
        elif event.event_type == "confidence_adjustment":
            # 调整置信度阈值
            new_threshold = event.event_data.get('threshold', 0.3)
            director.update_config('min_confidence_threshold', new_threshold)
            return True
        return False
    
    def can_handle(self, event_type: str) -> bool:
        return event_type in ["config_change", "confidence_adjustment"]


class ProposalFilterHandler(ContextHandler):
    """提案过滤处理器 - 临时屏蔽某些提案来源"""
    
    def __init__(self):
        super().__init__("proposal_filter_handler")
        self.blocked_sources = set()
        self.original_process_proposal = None
    
    def handle(self, event: SituationEvent, director: 'Director') -> bool:
        if event.event_type == "block_source":
            source = event.event_data.get('source')
            if source:
                self.blocked_sources.add(source)
                self._patch_director(director)
                return True
        elif event.event_type == "unblock_source":
            source = event.event_data.get('source')
            if source and source in self.blocked_sources:
                self.blocked_sources.remove(source)
                if not self.blocked_sources:
                    self._unpatch_director(director)
                return True
        elif event.event_type == "clear_blocks":
            self.blocked_sources.clear()
            self._unpatch_director(director)
            return True
        return False
    
    def _patch_director(self, director: 'Director'):
        """替换Director的提案处理方法以添加过滤"""
        if self.original_process_proposal is None:
            self.original_process_proposal = director._process_proposal
            
            def filtered_process_proposal(proposal):
                if proposal.source.value not in self.blocked_sources:
                    if self.original_process_proposal:
                        return self.original_process_proposal(proposal)
                else:
                    director.proposalRejected.emit(proposal, f"Source {proposal.source.value} is temporarily blocked")
            
            director._process_proposal = filtered_process_proposal
    
    def _unpatch_director(self, director: 'Director'):
        """恢复Director的原始提案处理方法"""
        if self.original_process_proposal is not None:
            director._process_proposal = self.original_process_proposal
            self.original_process_proposal = None
    
    def can_handle(self, event_type: str) -> bool:
        return event_type in ["block_source", "unblock_source", "clear_blocks"]


# === 工厂函数和便利接口 ===

def create_director(current_cue: Optional[Cue] = None) -> Director:
    """创建Director实例的工厂函数"""
    return Director(current_cue=current_cue)


# === 预定义配置 ===

class DirectorPresets:
    """Director预设配置"""
    
    @staticmethod
    def get_conservative_config() -> Dict[str, Any]:
        """保守配置 - 较高的置信度要求，较长的锁定时间"""
        return {
            "min_confidence_threshold": 0.5,
            "dedup_window_ms": 100,
            "auto_unlock_delay_ms": 8000,
            "max_history_size": 50,
        }
    
    @staticmethod
    def get_aggressive_config() -> Dict[str, Any]:
        """积极配置 - 较低的置信度要求，较短的锁定时间"""
        return {
            "min_confidence_threshold": 0.2,
            "dedup_window_ms": 30,
            "auto_unlock_delay_ms": 2000,
            "max_history_size": 200,
        }
    
    @staticmethod
    def get_theater_config() -> Dict[str, Any]:
        """剧场配置 - 针对复杂剧场环境优化"""
        return {
            "min_confidence_threshold": 0.4,
            "dedup_window_ms": 50,
            "auto_unlock_delay_ms": 6000,
            "max_history_size": 100,
        }
