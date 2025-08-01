"""
角色筛选对话框
用于按角色筛选台词显示
"""

from typing import Set, List
from PySide6.QtWidgets import (
    QDialog, QListWidget, QListWidgetItem, QPushButton,
    QVBoxLayout, QHBoxLayout, QLabel, QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, Slot

class CharacterFilterDialog(QDialog):
    """角色筛选对话框"""
    
    filter_changed = Signal(set)  # 筛选条件变化信号
    
    def __init__(self, all_characters: Set[str], selected_characters: Set[str] = None, parent=None):
        super().__init__(parent)
        self.all_characters = sorted(all_characters)
        self.selected_characters = selected_characters if selected_characters is not None else set(all_characters)
        self.setup_ui()
        self.connect_signals()
        self.load_characters()
    
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("按角色筛选台词")
        self.setModal(True)
        self.resize(400, 300)
        
        layout = QVBoxLayout(self)
        
        # 说明标签
        self.instruction_label = QLabel("选择要显示的角色，取消选择的角色将被隐藏：")
        self.instruction_label.setWordWrap(True)
        layout.addWidget(self.instruction_label)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        self.select_all_button = QPushButton("全选")
        self.select_none_button = QPushButton("全不选")
        self.invert_selection_button = QPushButton("反选")
        
        toolbar_layout.addWidget(self.select_all_button)
        toolbar_layout.addWidget(self.select_none_button)
        toolbar_layout.addWidget(self.invert_selection_button)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # 角色列表
        self.character_list_widget = QListWidget()
        layout.addWidget(self.character_list_widget)
        
        # 状态标签
        status_layout = QHBoxLayout()
        self.status_label = QLabel()
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # 按钮
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        layout.addWidget(self.button_box)
    
    def connect_signals(self):
        """连接信号槽"""
        self.select_all_button.clicked.connect(self.select_all)
        self.select_none_button.clicked.connect(self.select_none)
        self.invert_selection_button.clicked.connect(self.invert_selection)
        
        self.character_list_widget.itemChanged.connect(self.update_status)
        
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
    
    def load_characters(self):
        """加载角色到列表"""
        self.character_list_widget.clear()
        
        for character in self.all_characters:
            item = QListWidgetItem(character)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            
            # 设置选中状态
            if character in self.selected_characters:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            
            self.character_list_widget.addItem(item)
        
        self.update_status()
    
    @Slot()
    def select_all(self):
        """全选"""
        for i in range(self.character_list_widget.count()):
            item = self.character_list_widget.item(i)
            item.setCheckState(Qt.CheckState.Checked)
        self.update_status()
    
    @Slot()
    def select_none(self):
        """全不选"""
        for i in range(self.character_list_widget.count()):
            item = self.character_list_widget.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)
        self.update_status()
    
    @Slot()
    def invert_selection(self):
        """反选"""
        for i in range(self.character_list_widget.count()):
            item = self.character_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                item.setCheckState(Qt.CheckState.Unchecked)
            else:
                item.setCheckState(Qt.CheckState.Checked)
        self.update_status()
    
    @Slot()
    def update_status(self):
        """更新状态显示"""
        total_count = self.character_list_widget.count()
        selected_count = 0
        
        for i in range(total_count):
            item = self.character_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_count += 1
        
        self.status_label.setText(f"共 {total_count} 个角色，已选择 {selected_count} 个")
    
    def get_selected_characters(self) -> Set[str]:
        """获取选中的角色"""
        selected = set()
        
        for i in range(self.character_list_widget.count()):
            item = self.character_list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected.add(item.text())
        
        return selected
    
    def accept(self):
        """确认对话框"""
        selected = self.get_selected_characters()
        self.filter_changed.emit(selected)
        super().accept()
