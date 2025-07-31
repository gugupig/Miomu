#!/usr/bin/env python3
"""
简化的多声道STT接口测试（无GUI依赖）
"""
import numpy as np
from typing import Optional
from dataclasses import dataclass

@dataclass
class TranscriptPiece:
    """模拟TranscriptPiece"""
    text: str
    confidence: float


class MockSTTEngine:
    """模拟STT引擎，演示新的多声道接口"""
    
    def __init__(self, channel_id=0):
        self.channel_id = channel_id
        self.running = False
        self.received_data = []
        
    def start(self):
        self.running = True
        print(f"MockSTTEngine for channel {self.channel_id} started")
        
    def stop(self):
        self.running = False
        print(f"MockSTTEngine for channel {self.channel_id} stopped")
        
    def feed(self, channel_id: int, pcm_block: np.ndarray):
        """新的统一接口 - 支持多声道"""
        if not self.running:
            return
            
        print(f"STTEngine(ch={self.channel_id}) received data from channel {channel_id}, shape: {pcm_block.shape}")
        
        # 只处理指定声道的数据
        if channel_id == self.channel_id:
            self.received_data.append((channel_id, pcm_block.copy()))
            # 模拟识别结果
            if len(self.received_data) % 3 == 0:
                result_text = f"识别文本 ch={channel_id} count={len(self.received_data)}"
                print(f"  -> 识别结果: {result_text}")


def test_interface_design():
    """测试新接口设计的优势"""
    print("=== 测试多声道STT接口设计 ===\n")
    
    # 创建多个STT引擎，每个处理不同声道
    engines = {
        0: MockSTTEngine(channel_id=0),
        1: MockSTTEngine(channel_id=1), 
        2: MockSTTEngine(channel_id=2)
    }
    
    # 启动所有引擎
    for engine in engines.values():
        engine.start()
    
    print("--- 模拟AudioHub多声道数据分发 ---")
    
    # 模拟AudioHub发送多声道数据
    for frame_idx in range(8):
        print(f"\nFrame {frame_idx + 1}:")
        
        # 为每个声道生成不同的测试数据
        for channel_id in range(3):
            # 生成该声道的音频数据
            test_data = np.random.randn(800).astype(np.float32) * 0.1
            test_data[0] = channel_id  # 用第一个样本标记声道
            
            # 新接口的优势：所有引擎都可以接收所有声道的数据
            # 但每个引擎只处理自己关心的声道
            for engine in engines.values():
                engine.feed(channel_id, test_data)
    
    print("\n--- 统计结果 ---")
    for ch_id, engine in engines.items():
        print(f"STT Engine Channel {ch_id}: 处理了 {len(engine.received_data)} 个数据块")
    
    # 停止所有引擎
    for engine in engines.values():
        engine.stop()
    
    print("\n=== 接口设计优势展示 ===")
    print("1. 统一接口：所有STT引擎使用相同的 feed(channel_id, pcm_block) 签名")
    print("2. 直接连接：可以直接连接 audio_hub.blockReady.connect(stt_engine.feed)")
    print("3. 多声道支持：每个引擎可以选择处理哪个声道")
    print("4. 未来扩展：容易添加新的声道处理逻辑")
    print("5. 解耦设计：AudioHub 不需要知道有多少个STT引擎")


def demonstrate_old_vs_new():
    """展示旧接口 vs 新接口的区别"""
    print("\n=== 旧接口 vs 新接口对比 ===\n")
    
    print("旧接口设计:")
    print("  def feed(self, pcm_block): ...")
    print("  # 连接方式：")
    print("  audio_hub.blockReady.connect(lambda ch, blk: stt_engine.feed(blk))")
    print("  # 问题：丢失了声道信息，未来难以扩展")
    
    print("\n新接口设计:")
    print("  def feed(self, channel_id: int, pcm_block): ...")
    print("  # 连接方式：")
    print("  audio_hub.blockReady.connect(stt_engine.feed)")
    print("  # 优势：保留声道信息，支持直接连接，便于多声道扩展")
    
    print("\n未来多声道场景示例:")
    print("  # 可以轻松实现：")
    print("  stt_actor1 = STTEngine(channel_id=0)  # 演员1的麦克风")
    print("  stt_actor2 = STTEngine(channel_id=1)  # 演员2的麦克风") 
    print("  stt_ambient = STTEngine(channel_id=2) # 环境音麦克风")
    print("  # 所有引擎都可以直接连接到同一个AudioHub")


if __name__ == "__main__":
    test_interface_design()
    demonstrate_old_vs_new()
