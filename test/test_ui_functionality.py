#!/usr/bin/env python3
"""
Miomu UI 功能测试脚本
"""
import sys
import os
from pathlib import Path

# 设置项目根目录
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🚀 开始测试 Miomu UI 功能...")
print(f"📁 项目目录: {project_root}")
print(f"🐍 Python 版本: {sys.version}")

def test_ui_components():
    """测试UI组件"""
    try:
        print("\n1️⃣ 导入Qt模块...")
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        print("✅ Qt模块导入成功")
        
        print("\n2️⃣ 创建应用程序...")
        app = QApplication(sys.argv)
        app.setApplicationName("Miomu UI Test")
        print("✅ QApplication 创建成功")
        
        print("\n3️⃣ 导入主控制台...")
        from app.views.main_console import MainConsoleWindow
        print("✅ MainConsoleWindow 导入成功")
        
        print("\n4️⃣ 创建主窗口...")
        window = MainConsoleWindow()
        print("✅ MainConsoleWindow 创建成功")
        
        print("\n5️⃣ 检查UI文件集成...")
        if hasattr(window, 'ui'):
            print("✅ 使用UI文件模式")
            print(f"   - 标签页组件: {'✅' if hasattr(window, 'tab_widget') else '❌'}")
            print(f"   - 编辑表格: {'✅' if hasattr(window, 'script_table') else '❌'}")
            print(f"   - 剧场表格: {'✅' if hasattr(window, 'theater_table') else '❌'}")
            print(f"   - 加载按钮: {'✅' if hasattr(window, 'load_script_btn') else '❌'}")
            print(f"   - 播放按钮: {'✅' if hasattr(window, 'play_btn') else '❌'}")
            print(f"   - 角色颜色按钮: {'✅' if hasattr(window, 'character_color_btn') else '❌'}")
        else:
            print("⚠️ 使用代码生成模式")
            
        print("\n6️⃣ 检查核心功能...")
        print(f"   - 角色颜色管理器: {'✅' if hasattr(window, 'character_color_manager') else '❌'}")
        print(f"   - 脚本数据模型: {'✅' if hasattr(window, 'script_model') else '❌'}")
        print(f"   - 剧场数据模型: {'✅' if hasattr(window, 'theater_model') else '❌'}")
        print(f"   - 工作线程: {'✅' if hasattr(window, 'worker_thread') else '❌'}")
        
        print("\n7️⃣ 显示主窗口...")
        window.show()
        window.setWindowTitle("Miomu UI 测试 - 所有功能正常！")
        print("✅ 窗口显示成功")
        
        print("\n🎉 UI功能测试完成！")
        print("💡 提示：")
        print("   - 可以尝试点击'加载剧本'按钮")
        print("   - 可以测试角色颜色管理功能")
        print("   - 可以在编辑模式和剧场模式之间切换")
        print("   - 按 Ctrl+C 退出程序")
        
        # 启动Qt事件循环
        return app.exec()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("\n📋 解决方案：")
        print("1. 确保安装了 PySide6: pip install PySide6")
        print("2. 检查项目目录结构和__init__.py文件")
        return 1
        
    except Exception as e:
        print(f"❌ 运行时错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

def test_dialog_creation():
    """测试对话框创建"""
    try:
        print("\n🔧 测试对话框功能...")
        
        from app.ui.character_color_dialog import CharacterColorDialog
        from app.utils.character_color_manager import CharacterColorManager
        
        color_manager = CharacterColorManager()
        
        print("✅ 角色颜色对话框类导入成功")
        
        # 注意：这里不实际创建对话框，因为需要父窗口
        print("✅ 对话框功能准备就绪")
        
    except Exception as e:
        print(f"⚠️ 对话框测试警告: {e}")

if __name__ == "__main__":
    print("=" * 50)
    print("     🎭 MIOMU UI 功能测试")
    print("=" * 50)
    
    # 预先测试对话框
    test_dialog_creation()
    
    # 运行主要UI测试
    exit_code = test_ui_components()
    
    print("\n" + "=" * 50)
    print("测试完成！")
    sys.exit(exit_code)
