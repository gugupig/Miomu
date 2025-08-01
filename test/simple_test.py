import sys
import os
sys.path.insert(0, r'f:\Miomu\Miomu')

try:
    print("开始测试导入...")
    from app.views.main_console import MainConsoleWindow
    print("✅ MainConsoleWindow 导入成功!")
    
    from PySide6.QtWidgets import QApplication
    app = QApplication([])
    
    window = MainConsoleWindow()
    print("✅ MainConsoleWindow 创建成功!")
    print(f"使用UI文件: {hasattr(window, 'ui')}")
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
except Exception as e:
    print(f"❌ 创建错误: {e}")
    import traceback
    traceback.print_exc()
