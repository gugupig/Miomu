"""
角色颜色管理对话框
"""
import logging
from typing import Optional
from PySide6.QtWidgets import QDialog, QMessageBox
from PySide6.QtCore import Slot
from PySide6.QtGui import QColor

try:
    from app.ui.ui_character_color_dialog import Ui_CharacterColorDialog
    USE_UI_FILE = True
except ImportError:
    USE_UI_FILE = False
    logging.warning("CharacterColorDialog UI文件未找到")

from app.utils.character_color_manager import CharacterColorManager


class CharacterColorDialog(QDialog):
    """角色颜色管理对话框"""
    
    def __init__(self, character_color_manager: CharacterColorManager, parent=None):
        super().__init__(parent)
        self.character_color_manager = character_color_manager
        
        if USE_UI_FILE:
            self.ui = Ui_CharacterColorDialog()
            self.ui.setupUi(self)
            self.setup_ui_connections()
        else:
            self.setup_fallback_ui()
            
        self.load_characters()
    
    def setup_ui_connections(self):
        """设置UI连接"""
        if hasattr(self.ui, 'buttonBox'):
            self.ui.buttonBox.accepted.connect(self.accept)
            self.ui.buttonBox.rejected.connect(self.reject)
        
        # 其他按钮连接
        if hasattr(self.ui, 'addButton'):
            self.ui.addButton.clicked.connect(self.add_character)
        if hasattr(self.ui, 'removeButton'):
            self.ui.removeButton.clicked.connect(self.remove_character)
        if hasattr(self.ui, 'resetButton'):
            self.ui.resetButton.clicked.connect(self.reset_colors)
    
    def setup_fallback_ui(self):
        """设置回退UI"""
        self.setWindowTitle("角色颜色管理")
        self.resize(400, 300)
    
    def load_characters(self):
        """加载角色列表"""
        if USE_UI_FILE and hasattr(self.ui, 'characterTable'):
            # 加载到表格中
            pass
    
    @Slot()
    def add_character(self):
        """添加角色"""
        logging.info("添加角色")
    
    @Slot()
    def remove_character(self):
        """移除角色"""
        logging.info("移除角色")
    
    @Slot()
    def reset_colors(self):
        """重置颜色"""
        logging.info("重置颜色")
