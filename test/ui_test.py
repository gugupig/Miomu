import sys
sys.path.insert(0, r'f:\Miomu\Miomu')

try:
    from app.ui.ui_main_console_full import Ui_MainWindow
    print("✅ UI文件导入成功!")
    
    from PySide6.QtWidgets import QMainWindow, QApplication
    app = QApplication([])
    
    window = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(window)
    
    print("✅ UI设置成功!")
    print(f"窗口标题: {window.windowTitle()}")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
