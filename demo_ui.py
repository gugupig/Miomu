#!/usr/bin/env python3
"""
Miomu UI 完整功能演示
"""
import sys
import os
from pathlib import Path

def setup_environment():
    """设置环境"""
    project_root = Path(__file__).parent
    os.chdir(str(project_root))
    sys.path.insert(0, str(project_root))
    
    print(f"📁 工作目录: {os.getcwd()}")
    print(f"🐍 Python 路径: {sys.path[0]}")

def main():
    """主函数"""
    setup_environment()
    
    print("🎭 Miomu 剧本对齐系统 UI 演示")
    print("=" * 50)
    
    try:
        # 导入Qt
        print("1. 导入Qt模块...")
        from PySide6.QtWidgets import QApplication, QMessageBox
        from PySide6.QtCore import Qt
        
        # 创建应用
        print("2. 创建Qt应用...")
        app = QApplication(sys.argv)
        app.setApplicationName("Miomu 演示")
        app.setApplicationVersion("1.0")
        
        # 导入主窗口
        print("3. 导入主控制台...")
        from app.views.main_console import MainConsoleWindow
        
        # 创建主窗口
        print("4. 创建主窗口...")
        main_window = MainConsoleWindow()
        
        # 设置窗口属性
        main_window.setWindowTitle("🎭 Miomu - 剧本对齐控制台 [演示模式]")
        main_window.resize(1200, 800)
        
        # 显示欢迎消息
        print("5. 显示窗口...")
        main_window.show()
        
        # 显示功能提示
        welcome_msg = """
🎉 欢迎使用 Miomu 剧本对齐系统！

✨ 主要功能：
• 编辑模式：编辑和管理剧本台词
• 剧场模式：实时语音对齐和字幕显示
• 角色颜色管理：自动为不同角色分配颜色
• 多语言支持：支持多种语言的台词翻译
• 实时日志：查看系统运行状态

🔧 测试建议：
1. 点击"加载剧本"按钮测试文件加载
2. 切换到"剧场模式"查看播放界面
3. 尝试角色颜色管理功能
4. 查看实时日志显示

💡 提示：如果UI文件不可用，系统会自动回退到代码生成的界面
        """
        
        QMessageBox.information(main_window, "欢迎", welcome_msg)
        
        print("✅ UI 启动完成！")
        print("🎮 现在可以测试各种功能了")
        
        # 启动Qt事件循环
        return app.exec()
        
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("\n解决方案:")
        print("1. pip install PySide6")
        print("2. 检查项目结构")
        return 1
        
    except Exception as e:
        print(f"❌ 运行错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    print(f"\n程序结束，退出代码: {exit_code}")
    sys.exit(exit_code)
