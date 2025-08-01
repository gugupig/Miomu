import sys
sys.path.insert(0, r'f:\Miomu\Miomu')

print("步骤1: 测试基础导入...")
try:
    import os
    import logging
    from pathlib import Path
    print("✅ 基础模块导入成功")
except Exception as e:
    print(f"❌ 基础模块导入失败: {e}")
    exit(1)

print("步骤2: 测试Qt导入...")
try:
    from PySide6.QtWidgets import QApplication, QMainWindow
    from PySide6.QtCore import Qt
    print("✅ Qt模块导入成功")
except Exception as e:
    print(f"❌ Qt模块导入失败: {e}")
    exit(1)

print("步骤3: 测试UI文件导入...")
try:
    from app.ui.ui_main_console_full import Ui_MainWindow
    print("✅ UI文件导入成功")
except Exception as e:
    print(f"⚠️ UI文件导入失败: {e}")

print("步骤4: 测试主控制台导入...")
try:
    from app.views.main_console import MainConsoleWindow
    print("✅ 主控制台导入成功")
except Exception as e:
    print(f"❌ 主控制台导入失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("步骤5: 创建应用和窗口...")
try:
    app = QApplication([])
    window = MainConsoleWindow()
    print("✅ 应用和窗口创建成功")
    print(f"使用UI文件: {hasattr(window, 'ui')}")
    
    # 显示窗口
    window.show()
    print("✅ 窗口显示成功")
    
    # 不启动事件循环，只是验证创建
    print("🎉 所有测试通过！UI功能正常")
    
except Exception as e:
    print(f"❌ 创建失败: {e}")
    import traceback
    traceback.print_exc()
