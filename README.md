# Miomu

智能剧本对齐系统，支持实时语音识别和自动台词对齐。

## 功能特性

- **双模式界面**: 编辑模式和剧场模式分页设计
- **多线程架构**: 
  - `LoadScriptThread`: 后台加载和G2P预处理，避免UI冻结
  - `EngineWorkerThread`: 后台音频处理和STT识别
- **多声道支持**: STT引擎支持多声道输入，便于未来扩展
- **实时对齐**: 基于Fuzzy匹配和Viterbi算法的智能对齐
- **模块化设计**: 支持多种STT引擎（Whisper、Vosk）和G2P转换器

## 主要组件

### 用户界面
- `MainConsoleWindow`: 主控制台，包含编辑模式和剧场模式
- `SubtitleWindow`: 全屏字幕显示窗口
- `DebugLogWindow`: 调试日志窗口

### 核心模块
- `AudioHub`: 多通道音频采集
- `STTEngine`: 语音识别引擎（支持多声道接口）
- `Aligner`: 智能对齐器
- `SubtitlePlayer`: 剧本播放控制器
- `ScriptData`: 剧本数据管理

### 最新改进

#### 多声道STT接口统一
STT引擎的`feed`方法现在使用统一签名：
```python
def feed(self, channel_id: int, pcm_block: np.ndarray) -> None:
    """接收声道ID和PCM数据块"""
```

这样可以直接连接AudioHub信号：
```python
# 旧方式：需要lambda包装
audio_hub.blockReady.connect(lambda ch, blk: stt_engine.feed(blk))

# 新方式：直接连接，支持多声道
audio_hub.blockReady.connect(stt_engine.feed)
```

#### 非阻塞剧本加载
- 使用`LoadScriptThread`在后台执行G2P预处理
- 实时进度反馈，UI保持响应
- 支持大型剧本文件的流畅加载

## 使用方法

1. 运行主程序：
```bash
python main.py
```

2. 在编辑模式中加载剧本文件（JSON格式）
3. 切换到剧场模式开始对齐
4. 可选显示字幕窗口进行实时字幕显示

## 依赖项

- PySide6: GUI框架
- numpy: 数值计算
- sounddevice: 音频采集
- rapidfuzz: 文本匹配
- faster-whisper: Whisper STT引擎（可选）
- vosk: Vosk STT引擎（可选）
- phonemizer: G2P转换（可选，有fallback）