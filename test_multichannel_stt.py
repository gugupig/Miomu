#!/usr/bin/env python3
"""
测试新的多通道STT接口设计
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from unittest.mock import Mock

# 导入我们的模块
from app.core.stt.base import STTEngine, TranscriptPiece
from app.core.audio.audio_hub import AudioHub

class MockSTTEngine(STTEngine):
    """用于测试的模拟STT引擎"""
    
    def __init__(self, channel_id=0):
        super().__init__(channel_id=channel_id)
        self.received_data = []
        
    def start(self):
        self.running = True
        print(f"MockSTTEngine for channel {self.channel_id} started")
        
    def stop(self):
        self.running = False
        print(f"MockSTTEngine for channel {self.channel_id} stopped")
        
    def feed(self, channel_id: int, pcm_block):
        """新的统一接口"""
        print(f"STTEngine received data from channel {channel_id}, block shape: {pcm_block.shape}")
        if channel_id == self.channel_id:
            self.received_data.append((channel_id, pcm_block.copy()))
            # 模拟识别结果
            if len(self.received_data) % 5 == 0:  # 每5个块发射一次结果
                piece = TranscriptPiece(
                    text=f"测试文本 channel={channel_id} count={len(self.received_data)}",
                    confidence=0.8
                )
                self._emit(piece)


def test_multichannel_connection():
    """测试多通道连接"""
    print("=== 测试多通道STT接口 ===")
    
    # 创建多个STT引擎，每个处理不同声道
    stt_engine_ch0 = MockSTTEngine(channel_id=0)
    stt_engine_ch1 = MockSTTEngine(channel_id=1)
    
    # 设置结果处理器
    def on_result_ch0(channel_id, piece):
        print(f"[Channel 0] 识别结果: {piece.text}")
        
    def on_result_ch1(channel_id, piece):
        print(f"[Channel 1] 识别结果: {piece.text}")
    
    stt_engine_ch0.segmentReady.connect(on_result_ch0)
    stt_engine_ch1.segmentReady.connect(on_result_ch1)
    
    # 启动引擎
    stt_engine_ch0.start()
    stt_engine_ch1.start()
    
    # 模拟AudioHub发送数据到多个引擎
    print("\n--- 模拟多声道数据传输 ---")
    
    # 这展示了新接口的优势：可以直接连接
    for i in range(10):
        # 模拟来自不同声道的数据
        channel_0_data = np.random.randn(1600).astype(np.float32) * 0.1
        channel_1_data = np.random.randn(1600).astype(np.float32) * 0.1
        
        # 新的统一接口：直接调用，无需lambda包装
        stt_engine_ch0.feed(0, channel_0_data)  # 只处理channel 0
        stt_engine_ch0.feed(1, channel_1_data)  # 会被忽略
        
        stt_engine_ch1.feed(0, channel_0_data)  # 会被忽略  
        stt_engine_ch1.feed(1, channel_1_data)  # 只处理channel 1
    
    print(f"\nSTT Engine Channel 0 处理了 {len(stt_engine_ch0.received_data)} 个数据块")
    print(f"STT Engine Channel 1 处理了 {len(stt_engine_ch1.received_data)} 个数据块")
    
    # 停止引擎
    stt_engine_ch0.stop()
    stt_engine_ch1.stop()
    
    print("\n=== 测试完成 ===")


def test_direct_connection():
    """测试直接连接的优势"""
    print("\n=== 测试直接信号连接 ===")
    
    # 创建模拟的AudioHub信号
    from PySide6.QtCore import QObject, Signal
    
    class MockAudioHub(QObject):
        blockReady = Signal(int, np.ndarray)
        
        def emit_data(self, channel, data):
            self.blockReady.emit(channel, data)
    
    # 创建对象
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    
    audio_hub = MockAudioHub()
    stt_engine = MockSTTEngine(channel_id=0)
    
    # 新的连接方式：直接连接，不需要lambda
    audio_hub.blockReady.connect(stt_engine.feed)
    
    # 设置结果处理
    def on_result(channel_id, piece):
        print(f"直接连接结果: {piece.text}")
    
    stt_engine.segmentReady.connect(on_result)
    stt_engine.start()
    
    # 发送测试数据
    for i in range(6):
        test_data = np.random.randn(1600).astype(np.float32) * 0.1
        audio_hub.emit_data(0, test_data)  # 发送到channel 0
        audio_hub.emit_data(1, test_data)  # 发送到channel 1 (会被忽略)
    
    stt_engine.stop()
    print("直接连接测试完成")


if __name__ == "__main__":
    # 运行测试
    test_multichannel_connection()
    
    # 需要Qt应用来测试信号连接
    try:
        test_direct_connection()
    except ImportError:
        print("跳过Qt信号连接测试 (PySide6 未安装)")
