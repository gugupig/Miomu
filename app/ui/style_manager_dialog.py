"""
样式管理对话框
"""
import logging
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Slot

try:
    from app.ui.ui_style_manager_dialog import Ui_StyleManagerDialog
    USE_UI_FILE = True
except ImportError:
    USE_UI_FILE = False
    logging.warning("StyleManagerDialog UI文件未找到")


class StyleManagerDialog(QDialog):
    """样式管理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        if USE_UI_FILE:
            self.ui = Ui_StyleManagerDialog()
            self.ui.setupUi(self)
            self.setup_ui_connections()
        else:
            self.setup_fallback_ui()
    
    def setup_ui_connections(self):
        """设置UI连接"""
        if hasattr(self.ui, 'buttonBox'):
            self.ui.buttonBox.accepted.connect(self.accept)
            self.ui.buttonBox.rejected.connect(self.reject)
    
    def setup_fallback_ui(self):
        """设置回退UI"""
        self.setWindowTitle("样式管理")
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("样式管理功能"))
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
