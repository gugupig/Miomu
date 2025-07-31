# STT引擎多声道接口改进

## 问题描述

原来的STT引擎`feed`方法签名为：
```python
def feed(self, pcm_block) -> None:
```

这导致了以下问题：
1. **丢失声道信息**：无法知道音频数据来自哪个声道
2. **需要lambda包装**：连接AudioHub信号时需要写成 `lambda ch, blk: stt_engine.feed(blk)`
3. **难以扩展**：未来支持多声道时需要大量修改

## 解决方案

### 新的统一接口

将所有STT引擎的`feed`方法签名统一为：
```python
def feed(self, channel_id: int, pcm_block) -> None:
    """
    接收声道ID和PCM数据块
    
    Args:
        channel_id: 声道编号 (0-based)
        pcm_block: 1D numpy ndarray，采样率 = 16 kHz，float32 [-1,1]
    """
```

### 直接信号连接

现在可以直接连接AudioHub和STT引擎：
```python
# 旧方式：需要lambda包装，丢失声道信息
audio_hub.blockReady.connect(lambda ch, blk: stt_engine.feed(blk))

# 新方式：直接连接，保留声道信息
audio_hub.blockReady.connect(stt_engine.feed)
```

## 实现细节

### 修改的文件

1. **`app/core/stt/base.py`**：更新抽象基类的feed方法签名
2. **`app/core/stt/whisper_engine.py`**：实现新接口，支持声道过滤
3. **`app/core/stt/vosk_engine.py`**：实现新接口，支持声道过滤  
4. **`app/views/main_console.py`**：使用新的直接连接方式

### 声道过滤逻辑

每个STT引擎现在可以指定要处理的声道：
```python
class WhisperEngine(STTEngine):
    def __init__(self, channel_id=0, ...):
        super().__init__(channel_id=channel_id)
        
    def feed(self, channel_id: int, pcm_block):
        # 只处理指定声道的数据
        if channel_id == self.channel_id:
            self.block_q.put_nowait(pcm_block.copy())
```

## 优势总结

### 1. 代码简洁性
- 消除了lambda包装函数
- 直接连接更清晰易读

### 2. 多声道扩展性
```python
# 未来可以轻松实现多声道场景
stt_actor1 = WhisperEngine(channel_id=0)  # 演员1麦克风
stt_actor2 = WhisperEngine(channel_id=1)  # 演员2麦克风
stt_ambient = WhisperEngine(channel_id=2) # 环境音麦克风

# 所有引擎都连接到同一个AudioHub
audio_hub.blockReady.connect(stt_actor1.feed)
audio_hub.blockReady.connect(stt_actor2.feed)
audio_hub.blockReady.connect(stt_ambient.feed)
```

### 3. 解耦设计
- AudioHub不需要知道有多少个STT引擎
- 每个STT引擎独立决定处理哪个声道
- 添加新引擎无需修改现有代码

### 4. 类型安全
- 明确的参数类型定义
- 更好的IDE支持和错误检查

## 向后兼容性

这是一个破坏性变更，需要更新所有STT引擎的实现。但变更是局部的，只影响：
- STT引擎实现类
- 信号连接代码

核心的AudioHub和业务逻辑无需修改。

## 测试验证

创建了`test_stt_interface.py`来验证新接口的正确性：
- 测试多声道数据分发
- 验证声道过滤逻辑
- 展示直接连接的优势

运行测试确认所有功能正常工作。
