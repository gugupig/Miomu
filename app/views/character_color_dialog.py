"""
角色颜色管理对话框
用于编辑和管理角色显示颜色
"""

import os
from typing import Optional, List, Dict
from PySide6.QtWidgets import (
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QColorDialog, QMessageBox, QInputDialog, QPushButton,
    QAbstractItemView, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor, QPalette
from PySide6.QtUiTools import QUiLoader

from ..utils.character_color_manager import CharacterColorManager, CharacterColor

"""
角色颜色管理对话框
用于编辑和管理角色显示颜色
"""

from typing import Optional, List
from PySide6.QtWidgets import (
    QDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QColorDialog, QMessageBox, QInputDialog, QPushButton,
    QAbstractItemView, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QDialogButtonBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QColor

from ..utils.character_color_manager import CharacterColorManager

class ColorPreviewWidget(QWidget):
    """颜色预览小部件"""
    def __init__(self, color: str = "#FFFFFF", parent=None):
        super().__init__(parent)
        self.setFixedSize(40, 20)
        self.set_color(color)
    
    def set_color(self, color: str):
        """设置颜色"""
        self.color = color
        self.setStyleSheet(f"background-color: {color}; border: 1px solid #999999;")

class CharacterColorDialog(QDialog):
    """角色颜色管理对话框"""
    
    colors_updated = Signal()  # 颜色更新信号
    
    def __init__(self, color_manager: CharacterColorManager, parent=None):
        super().__init__(parent)
        self.color_manager = color_manager
        self.setup_ui()
        self.connect_signals()
        self.load_character_colors()
    
    def setup_ui(self):
        """设置UI"""
        self.setWindowTitle("角色颜色管理")
        self.setModal(True)
        self.resize(600, 400)
        
        layout = QVBoxLayout(self)
        
        # 说明标签
        self.instruction_label = QLabel("为每个角色设置台词显示颜色。双击颜色方块可以修改颜色。")
        self.instruction_label.setWordWrap(True)
        layout.addWidget(self.instruction_label)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        self.add_character_button = QPushButton("添加角色")
        self.remove_character_button = QPushButton("删除角色")
        self.remove_character_button.setEnabled(False)
        self.reset_colors_button = QPushButton("重置默认颜色")
        
        toolbar_layout.addWidget(self.add_character_button)
        toolbar_layout.addWidget(self.remove_character_button)
        toolbar_layout.addWidget(self.reset_colors_button)
        toolbar_layout.addStretch()
        
        layout.addLayout(toolbar_layout)
        
        # 表格
        self.character_color_table = QTableWidget()
        layout.addWidget(self.character_color_table)
        
        # 预览区域
        preview_layout = QHBoxLayout()
        preview_layout.addWidget(QLabel("效果预览："))
        self.preview_text_label = QLabel("示例台词文本")
        self.preview_text_label.setStyleSheet("QLabel { padding: 5px; border: 1px solid gray; background-color: white; }")
        preview_layout.addWidget(self.preview_text_label)
        preview_layout.addStretch()
        
        layout.addLayout(preview_layout)
        
        # 按钮
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(self.button_box)
        
        self.setup_table()
    
    def setup_table(self):
        """设置表格"""
        self.character_color_table.setColumnCount(3)
        self.character_color_table.setHorizontalHeaderLabels(["角色名称", "颜色预览", "颜色值"])
        
        # 设置表格属性
        self.character_color_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.character_color_table.setAlternatingRowColors(True)
        
        # 设置列宽
        header = self.character_color_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        self.character_color_table.setColumnWidth(1, 80)
    
    def connect_signals(self):
        """连接信号槽"""
        self.add_character_button.clicked.connect(self.add_character)
        self.remove_character_button.clicked.connect(self.remove_character)
        self.reset_colors_button.clicked.connect(self.reset_colors)
        
        self.character_color_table.itemSelectionChanged.connect(self.on_selection_changed)
        self.character_color_table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
    
    def load_character_colors(self):
        """加载角色颜色到表格"""
        characters = self.color_manager.get_all_characters()
        self.character_color_table.setRowCount(len(characters))
        
        for row, character_name in enumerate(characters):
            color = self.color_manager.get_character_color(character_name)
            
            # 角色名称
            name_item = QTableWidgetItem(character_name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.character_color_table.setItem(row, 0, name_item)
            
            # 颜色预览
            color_preview = ColorPreviewWidget(color)
            self.character_color_table.setCellWidget(row, 1, color_preview)
            
            # 颜色值
            color_item = QTableWidgetItem(color)
            color_item.setFlags(color_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.character_color_table.setItem(row, 2, color_item)
    
    @Slot()
    def add_character(self):
        """添加角色"""
        text, ok = QInputDialog.getText(self, "添加角色", "请输入角色名称：")
        if ok and text.strip():
            character_name = text.strip()
            if self.color_manager.add_character(character_name):
                self.load_character_colors()
                self.colors_updated.emit()
            else:
                QMessageBox.warning(self, "警告", f"角色 '{character_name}' 已存在！")
    
    @Slot()
    def remove_character(self):
        """删除角色"""
        current_row = self.character_color_table.currentRow()
        if current_row < 0:
            return
        
        name_item = self.character_color_table.item(current_row, 0)
        if not name_item:
            return
            
        character_name = name_item.text()
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除角色 '{character_name}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.color_manager.remove_character(character_name):
                self.load_character_colors()
                self.colors_updated.emit()
            else:
                QMessageBox.warning(self, "警告", "无法删除系统内置角色！")
    
    @Slot()
    def reset_colors(self):
        """重置默认颜色"""
        reply = QMessageBox.question(
            self, "确认重置", 
            "确定要将所有角色重置为默认颜色吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.color_manager.reset_to_default_colors()
            self.load_character_colors()
            self.colors_updated.emit()
    
    @Slot()
    def on_selection_changed(self):
        """选择变化时的处理"""
        current_row = self.character_color_table.currentRow()
        self.remove_character_button.setEnabled(current_row >= 0)
        
        # 更新预览
        if current_row >= 0:
            name_item = self.character_color_table.item(current_row, 0)
            if name_item:
                character_name = name_item.text()
                color = self.color_manager.get_character_color(character_name)
                self.preview_text_label.setStyleSheet(
                    f"QLabel {{ padding: 5px; border: 1px solid gray; "
                    f"background-color: white; color: {color}; }}"
                )
                self.preview_text_label.setText(f"{character_name}: 这是示例台词文本")
    
    @Slot(int, int)
    def on_cell_double_clicked(self, row: int, column: int):
        """单元格双击处理"""
        if column == 1 or column == 2:  # 颜色预览或颜色值列
            name_item = self.character_color_table.item(row, 0)
            if not name_item:
                return
                
            character_name = name_item.text()
            current_color = self.color_manager.get_character_color(character_name)
            
            color_dialog = QColorDialog(QColor(current_color), self)
            if color_dialog.exec() == QColorDialog.DialogCode.Accepted:
                new_color = color_dialog.selectedColor().name()
                self.color_manager.set_character_color(character_name, new_color)
                
                # 更新表格显示
                color_preview = self.character_color_table.cellWidget(row, 1)
                if isinstance(color_preview, ColorPreviewWidget):
                    color_preview.set_color(new_color)
                
                color_item = self.character_color_table.item(row, 2)
                if color_item:
                    color_item.setText(new_color)
                
                self.colors_updated.emit()
                
                # 更新预览
                self.on_selection_changed()
    
    def accept(self):
        """确认对话框"""
        self.color_manager.save_config()
        super().accept()

    def reject(self):
        """取消对话框"""
        # 重新加载配置以撤销未保存的更改
        self.color_manager.load_config()
        super().reject()
