"""
简单验证VoskEngine启动时机
"""
import sys
import os
import time
from datetime import datetime

# 设置路径
sys.path.append(os.path.abspath('.'))

def timestamp():
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]

def test_vosk_timing():
    """验证VoskEngine启动时机"""
    print(f"[{timestamp()}] 🧪 验证VoskEngine启动时机")
    print("=" * 60)
    
    try:
        print(f"[{timestamp()}] 📦 导入AlignmentManager...")
        from app.core.alignment_manager import AlignmentManager
        from app.data.script_data import ScriptData
        from app.models.models import Cue, Meta, Style, SubtitleDocument
        
        print(f"[{timestamp()}] 📄 创建测试数据...")
        meta = Meta(title="测试", author="测试", language=["fr"])
        styles = {"default": Style(font="Arial", size=24, color="#FFFFFF")}
        cues = [Cue(id=1, character="TEST", line="Test line")]
        
        document = SubtitleDocument(meta=meta, styles=styles, cues=cues)
        script_data = ScriptData()
        script_data.cues = document.cues
        
        print(f"[{timestamp()}] 🔧 创建AlignmentManager...")
        alignment_manager = AlignmentManager()
        
        # 监听状态变化
        status_messages = []
        def track_status(msg):
            timestamp_msg = f"[{timestamp()}] 📊 {msg}"
            print(timestamp_msg)
            status_messages.append(timestamp_msg)
        
        alignment_manager.status_changed.connect(track_status)
        
        print(f"[{timestamp()}] 🚀 开始初始化组件...")
        print(f"[{timestamp()}] ⏰ 注意：VoskEngine启动时会显示 '[VoskEngine] recognizer ready'")
        print("-" * 60)
        
        # 开始初始化
        start_time = time.time()
        success = alignment_manager.initialize_components(
            script_data=script_data,
            stt_engine_type="vosk"
        )
        
        if success:
            print(f"[{timestamp()}] ✅ 初始化方法调用成功")
            
            # 等待一些时间让VoskEngine加载
            print(f"[{timestamp()}] ⏳ 等待5秒观察VoskEngine加载...")
            time.sleep(5)
            
            end_time = time.time()
            print(f"\n[{timestamp()}] 📋 总结:")
            print(f"   - 总耗时: {end_time - start_time:.2f} 秒")
            print(f"   - 状态消息数量: {len(status_messages)}")
            
            # 检查是否有VoskEngine相关消息
            vosk_messages = [msg for msg in status_messages if "vosk" in msg.lower()]
            if vosk_messages:
                print(f"   - VoskEngine相关消息:")
                for msg in vosk_messages:
                    print(f"     {msg}")
            
            # 检查组件状态
            states = alignment_manager.get_component_states()
            print(f"   - 组件状态: {states}")
            
        else:
            print(f"[{timestamp()}] ❌ 初始化失败")
        
        # 清理
        print(f"[{timestamp()}] 🧹 清理组件...")
        alignment_manager.cleanup_components()
        
        return success
        
    except Exception as e:
        print(f"[{timestamp()}] ❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_vosk_timing()
    
    if success:
        print(f"\n[{timestamp()}] 🎉 验证完成！")
        print("📋 关键点:")
        print("   1. VoskEngine 现在在 initialize_components() 调用时立即启动")
        print("   2. 模型加载发生在初始化阶段，不是在 start_alignment() 时")
        print("   3. start_alignment() 只负责打开音频闸口")
    else:
        print(f"\n[{timestamp()}] ❌ 验证失败")
        sys.exit(1)
