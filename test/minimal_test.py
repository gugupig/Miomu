#!/usr/bin/env python3
"""
最简单的UI测试
"""
import sys
sys.path.insert(0, r'f:\Miomu\Miomu')

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel

def create_simple_window():
    """创建一个简单的测试窗口"""
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("Miomu UI测试")
    window.setGeometry(100, 100, 800, 600)
    
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    
    layout = QVBoxLayout(central_widget)
    
    # 添加一些测试控件
    layout.addWidget(QLabel("UI文件集成测试"))
    layout.addWidget(QPushButton("测试按钮1"))
    layout.addWidget(QPushButton("测试按钮2"))
    
    # 尝试加载UI文件
    try:
        from app.ui.ui_main_console_full import Ui_MainWindow
        layout.addWidget(QLabel("✅ UI文件导入成功"))
        
        # 创建一个使用UI文件的窗口
        ui_window = QMainWindow()
        ui = Ui_MainWindow()
        ui.setupUi(ui_window)
        
        layout.addWidget(QLabel("✅ UI文件设置成功"))
        
    except Exception as e:
        layout.addWidget(QLabel(f"❌ UI文件错误: {e}"))
    
    window.show()
    print("窗口显示成功！按Ctrl+C退出")
    
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print("用户中断")

if __name__ == "__main__":
    create_simple_window()
