#!/usr/bin/env python3
"""
测试G2P组件修复
"""
import sys
import os
from pathlib import Path

def setup_environment():
    """设置环境"""
    project_root = Path(__file__).parent
    os.chdir(str(project_root))
    sys.path.insert(0, str(project_root))

def test_g2p_components():
    """测试G2P组件创建"""
    setup_environment()
    
    try:
        print("🧪 测试G2P组件修复...")
        
        # 导入必要模块
        from PySide6.QtWidgets import QApplication
        from app.views.main_console import MainConsoleWindow
        
        # 创建应用
        app = QApplication(sys.argv)
        
        # 创建主窗口
        print("创建主窗口...")
        window = MainConsoleWindow()
        
        # 检查G2P组件是否存在
        print("检查G2P组件...")
        
        components = {
            'g2p_engine_combo': hasattr(window, 'g2p_engine_combo') and window.g2p_engine_combo is not None,
            'g2p_language_combo': hasattr(window, 'g2p_language_combo') and window.g2p_language_combo is not None,
            'g2p_status_label': hasattr(window, 'g2p_status_label') and window.g2p_status_label is not None,
            'g2p_manager': hasattr(window, 'g2p_manager') and window.g2p_manager is not None,
        }
        
        print("\n📊 组件检查结果:")
        for name, exists in components.items():
            status = "✅" if exists else "❌"
            print(f"  {status} {name}: {'存在' if exists else '缺失'}")
        
        # 检查G2P引擎
        if components['g2p_manager']:
            try:
                engines = window.g2p_manager.get_available_engines()
                print(f"\n🔧 可用G2P引擎: {len(engines)} 个")
                for engine_type, config in engines:
                    print(f"  • {config['name']}")
                    
                current_engine = window.g2p_manager.get_current_engine_info()
                print(f"\n🎯 当前引擎: {current_engine['name']} ({current_engine['language']})")
                
            except Exception as e:
                print(f"❌ G2P管理器错误: {e}")
        
        # 检查UI组件内容
        if components['g2p_engine_combo']:
            count = window.g2p_engine_combo.count()
            print(f"\n📋 引擎选择框项目数: {count}")
            
        if components['g2p_language_combo']:
            count = window.g2p_language_combo.count()
            print(f"📋 语言选择框项目数: {count}")
            
        if components['g2p_status_label'] and hasattr(window.g2p_status_label, 'text'):
            try:
                text = window.g2p_status_label.text()
                print(f"📊 状态标签文本: '{text}'")
            except AttributeError:
                print("📊 状态标签无法获取文本")
        
        # 测试完成
        all_ok = all(components.values())
        if all_ok:
            print("\n🎉 所有G2P组件都已正确创建！")
            return True
        else:
            print("\n⚠️ 部分G2P组件缺失，但系统应该仍能运行")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_g2p_components()
    print(f"\n测试{'成功' if success else '失败'}")
    sys.exit(0 if success else 1)
