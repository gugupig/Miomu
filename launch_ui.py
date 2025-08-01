#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# 切换到项目目录
os.chdir(r'f:\Miomu\Miomu')
sys.path.insert(0, r'f:\Miomu\Miomu')

print("🚀 启动 Miomu UI...")

try:
    from PySide6.QtWidgets import QApplication
    from app.views.main_console import MainConsoleWindow
    
    app = QApplication(sys.argv)
    window = MainConsoleWindow()
    window.show()
    
    print("✅ UI 启动成功！")
    print("💡 窗口已显示，可以测试各种功能")
    
    # 启动Qt事件循环
    sys.exit(app.exec())
    
except Exception as e:
    print(f"❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()
    input("按回车键退出...")
