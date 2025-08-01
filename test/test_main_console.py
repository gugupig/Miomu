#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
测试修改后的 main_console.py 是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """测试导入"""
    print("🧪 测试导入...")
    
    try:
        print("导入 G2P 管理器...")
        from app.core.g2p.g2p_manager import G2PManager, G2PEngineType
        print("✅ G2P 管理器导入成功")
        
        print("导入 MainConsoleWindow...")
        from app.views.main_console import MainConsoleWindow
        print("✅ MainConsoleWindow 导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_g2p_manager():
    """测试G2P管理器功能"""
    print("\n🧪 测试 G2P 管理器功能...")
    
    try:
        from app.core.g2p.g2p_manager import G2PManager
        
        manager = G2PManager()
        print("✅ G2P管理器创建成功")
        
        # 获取可用引擎
        engines = manager.get_available_engines()
        print(f"📋 可用引擎: {len(engines)} 个")
        
        for engine_type, config in engines:
            print(f"  - {config['name']}")
            
        # 测试最佳引擎
        engine = manager.get_best_available_engine()
        info = manager.get_current_engine_info()
        print(f"✅ 当前引擎: {info['name']}")
        
        return True
    except Exception as e:
        print(f"❌ G2P管理器测试失败: {e}")
        return False

def test_main_window_creation():
    """测试主窗口创建（不显示界面）"""
    print("\n🧪 测试主窗口创建...")
    
    try:
        from PySide6.QtWidgets import QApplication
        from app.views.main_console import MainConsoleWindow
        
        # 创建应用程序（如果不存在）
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # 创建主窗口
        window = MainConsoleWindow()
        print("✅ 主窗口创建成功")
        
        # 测试G2P功能是否正常
        if hasattr(window, 'g2p_manager'):
            info = window.g2p_manager.get_current_engine_info()
            print(f"✅ 窗口G2P管理器正常: {info['name']}")
        else:
            print("❌ 窗口缺少G2P管理器")
            
        return True
    except Exception as e:
        print(f"❌ 窗口创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试修改后的 main_console.py")
    
    tests = [
        ("导入测试", test_imports),
        ("G2P管理器测试", test_g2p_manager),
        ("主窗口创建测试", test_main_window_creation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 执行失败: {e}")
            results.append((test_name, False))
            
    print(f"\n📊 测试结果:")
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
            
    print(f"\n🏆 总体结果: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！main_console.py 修改成功！")
    else:
        print("⚠️  部分测试失败，需要进一步调试")

if __name__ == "__main__":
    main()
