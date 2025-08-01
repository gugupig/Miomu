import sys
import os
sys.path.insert(0, r'f:\Miomu\Miomu')

def test_import():
    try:
        print("步骤1: 导入MainConsoleWindow...")
        from app.views.main_console import MainConsoleWindow
        print("✅ 导入成功!")
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_creation():
    try:
        print("步骤2: 创建QApplication...")
        from PySide6.QtWidgets import QApplication
        app = QApplication([])
        print("✅ QApplication创建成功!")
        
        print("步骤3: 创建MainConsoleWindow...")
        from app.views.main_console import MainConsoleWindow
        window = MainConsoleWindow()
        print("✅ MainConsoleWindow创建成功!")
        
        print(f"使用UI文件: {hasattr(window, 'ui')}")
        
        app.quit()
        return True
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if test_import():
        test_creation()
