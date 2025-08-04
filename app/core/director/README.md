# Director 模块文档 (简化版)

## 概述

Director 是字幕系统的核心调度器和裁决者，负责统一处理来自3个来源的字幕行切换提案，并做出即时决策。简化版去除了复杂的收集延迟机制，采用直接处理方式，提高响应速度和系统稳定性。

## 设计理念

### 问题背景
原有复杂的5源提案+收集延迟机制在实际使用中过于复杂，容易导致：
- 响应延迟增加
- 决策逻辑复杂难以调试
- 不必要的功能冗余

### 简化方案
新的Director采用**三源直处理**架构：

1. **MANUAL (人工操作)**：最高优先级，强制覆盖所有智能系统决定
2. **ALIGNER (智能对齐)**：正常优先级，带50ms去重保护
3. **SITUATION (情境感知)**：仅提供决策信息，不直接触发切换

## 核心特性

### 1. 三源提案处理
- **MANUAL**: 优先级HIGH，置信度1.0，可强制覆盖锁定状态
- **ALIGNER**: 优先级NORMAL，带时间戳的去重保护（50ms窗口）
- **SITUATION**: 优先级NORMAL，提供上下文信息辅助决策

### 2. 直接处理机制
- 取消提案收集延迟，每个提案立即处理
- 简化决策流程：接收 → 验证 → 执行
- 提高系统响应速度

### 3. 智能去重保护
- 防止Aligner在50ms内重复发送相同Cue提案
- 比较条件：target_cue.id + source + timestamp
- 基于历史记录的去重检查

### 4. 强制覆盖机制
- MANUAL提案可以覆盖任何锁定状态
- 人工操作具有最高决策权限
- 确保在紧急情况下的可控性

## API 接口

### 输入接口（槽函数）

```python
# 三种提案来源
receive_aligner_proposal(target_cue: Cue, confidence: float, reason: str)
receive_manual_proposal(target_cue: Cue, reason: str)  
receive_situation_proposal(target_cue: Cue, reason: str, metadata: Dict)

# 锁定控制
lock_director(reason: str, duration_ms: int)
unlock_director()

# 状态同步
sync_current_cue(cue: Cue)
```

### 输出接口（信号）

```python
# 核心输出
cueChangeRequested = Signal(Cue, str)  # 请求切换到指定Cue

# 状态通知
stateChanged = Signal(DirectorState)  # IDLE/PROCESSING/LOCKED
lockStateChanged = Signal(bool, str)

# 决策监控
decisionMade = Signal(str, CueProposal)
proposalRejected = Signal(CueProposal, str)
```

## 工作流程

### 1. Aligner提案处理流程
```
STT识别 → Aligner分析 → director.receive_aligner_proposal()
    ↓
检查锁定状态 → 检查置信度 → 检查去重 → 执行切换
    ↓
记录历史 → 发射信号 → 自动锁定1.5s
```

### 2. 人工操作流程  
```
UI操作 → director.receive_manual_proposal()
    ↓
强制覆盖锁定 → 直接执行切换 → 记录历史
    ↓
发射信号 → 自动锁定2s
```

### 3. 去重保护机制
```python
def _is_duplicate_proposal(self, new_proposal):
    for existing in self.proposal_history:
        if (existing.target_cue.id == new_proposal.target_cue.id and
            existing.source == new_proposal.source and  
            current_time - existing.timestamp < 50ms):
            return True  # 拒绝重复提案
```

## 配置选项

### 预设配置

```python
from app.core.director.director import DirectorPresets

# 保守配置 - 适合正式演出
conservative = DirectorPresets.get_conservative_config()
# 置信度阈值: 0.5, 去重窗口: 100ms, 解锁延迟: 8s

# 积极配置 - 适合排练调试  
aggressive = DirectorPresets.get_aggressive_config()
# 置信度阈值: 0.2, 去重窗口: 30ms, 解锁延迟: 2s

# 剧场配置 - 平衡设置
theater = DirectorPresets.get_theater_config()
# 置信度阈值: 0.4, 去重窗口: 50ms, 解锁延迟: 6s

# 应用配置
director.config.update(theater)
```

### 主要参数说明

- `min_confidence_threshold`: 最小置信度阈值，低于此值的提案被拒绝
- `dedup_window_ms`: 去重时间窗口，防止Aligner重复提案
- `auto_unlock_delay_ms`: 自动解锁延迟时间  
- `max_history_size`: 最大历史记录数量

## 集成指南

### 1. 修改现有 Aligner

```python
# 原有代码  
self.cueMatched.emit(best_match_cue)

# 修改为
director.receive_aligner_proposal(best_match_cue, confidence/100.0, "Fuzzy match")
```

### 2. 连接 SubtitlePlayer

```python
# Director -> SubtitlePlayer
director.cueChangeRequested.connect(player.go_by_cue_obj)

# SubtitlePlayer -> Director  
player.cueChanged.connect(director.sync_current_cue)
```

### 3. 人工控制界面

```python
# UI按钮处理
def on_next_button():
    next_cue = get_next_cue()
    director.receive_manual_proposal(next_cue, "Manual next")

def on_jump_button(target_cue):
    director.receive_manual_proposal(target_cue, "Manual jump")
```

### 4. SituationSense集成

```python
# 情境感知模块
def on_context_change(detected_cue, context_info):
    director.receive_situation_proposal(
        detected_cue, 
        "Context change detected",
        {"confidence": 0.9, "context": context_info}
    )
```

## 使用示例

```python
from app.core.director import Director, DirectorPresets

# 创建Director
director = Director(current_cue=initial_cue)

# 应用剧场配置
director.config.update(DirectorPresets.get_theater_config())

# 连接信号
director.cueChangeRequested.connect(player.go_by_cue_obj)
director.proposalRejected.connect(log_rejection)

# 模拟使用
director.receive_aligner_proposal(target_cue, 0.85, "High confidence")
director.receive_manual_proposal(emergency_cue, "Emergency intervention")
```

## 调试和监控

### 1. 状态查询
```python
state = director.get_current_state()
print(f"当前Cue: {state['current_cue_id']}")
print(f"锁定状态: {state['is_locked']}")
```

### 2. 历史记录
```python
history = director.get_proposal_history(limit=10) 
for proposal in history:
    print(f"{proposal.timestamp}: {proposal.source.value} -> Cue {proposal.target_cue.id}")
```

### 3. 实时监控
```python
director.decisionMade.connect(lambda t, p: print(f"决策: {t}"))
director.proposalRejected.connect(lambda p, r: print(f"拒绝: {r}"))
```

## 性能优势

相比原版复杂架构：
- **响应速度**: 去除收集延迟，提案立即处理
- **内存使用**: 简化数据结构，减少内存占用
- **调试友好**: 决策流程清晰，易于问题定位
- **稳定性**: 减少复杂逻辑，降低出错概率

## 总结

简化版Director通过三源直处理架构，在保持核心功能的同时大幅简化了系统复杂度。它特别适合：

- 对响应速度要求高的实时字幕场景
- 需要稳定可靠的正式演出环境  
- 要求调试友好的开发测试阶段

这个设计在功能性和复杂度之间取得了很好的平衡，是实用导向的优化方案。
