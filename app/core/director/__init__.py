"""
Director module - 字幕显示总调度/裁决者

提供统一的字幕行切换决策和控制机制
增强版：支持SituationSense上下文事件处理系统
"""

from .director import (
    Director,
    CueProposal,
    SituationEvent,
    ContextHandler,
    ProposalSource,
    ProposalPriority,
    DirectorState,
    DirectorPresets
)

__all__ = [
    'Director',
    'CueProposal',
    'SituationEvent',
    'ContextHandler',
    'ProposalSource',
    'ProposalPriority',
    'DirectorState',
    'DirectorPresets'
]
