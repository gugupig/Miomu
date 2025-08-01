"""
角色过滤对话框
"""
import logging
from typing import Set
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QLabel, QListWidget
from PySide6.QtCore import Slot

try:
    from app.ui.ui_character_filter_dialog import Ui_CharacterFilterDialog
    USE_UI_FILE = True
except ImportError:
    USE_UI_FILE = False
    logging.warning("CharacterFilterDialog UI文件未找到")


class CharacterFilterDialog(QDialog):
    """角色过滤对话框"""
    
    def __init__(self, all_characters: Set[str], selected_characters: Set[str], parent=None):
        super().__init__(parent)
        self.all_characters = all_characters
        self.selected_characters = selected_characters.copy()
        
        if USE_UI_FILE:
            self.ui = Ui_CharacterFilterDialog()
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
    
    def setup_fallback_ui(self):
        """设置回退UI"""
        self.setWindowTitle("角色过滤")
        self.resize(300, 400)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("选择要显示的角色:"))
        
        self.character_list = QListWidget()
        layout.addWidget(self.character_list)
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        layout.addWidget(ok_btn)
    
    def load_characters(self):
        """加载角色列表"""
        if USE_UI_FILE and hasattr(self.ui, 'characterList'):
            # 加载到UI文件的列表中
            pass
        elif hasattr(self, 'character_list'):
            # 回退UI的列表
            for character in self.all_characters:
                self.character_list.addItem(character)
