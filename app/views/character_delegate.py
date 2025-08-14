"""
CharacterDelegate - 角色列的下拉菜单委托
为编辑模式的角色列提供下拉菜单功能
"""
import logging
from typing import Set, List, Optional, Union
from PySide6.QtCore import QModelIndex, QPersistentModelIndex, Qt
from PySide6.QtWidgets import QStyledItemDelegate, QComboBox, QWidget
from PySide6.QtGui import QPainter

from app.models.models import Cue


class CharacterDelegate(QStyledItemDelegate):
    """角色列的下拉菜单委托"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._character_list: List[str] = []
        self._auto_update = True  # 是否自动更新角色列表
        
    def set_character_list(self, characters: List[str]):
        """设置角色列表"""
        self._character_list = sorted(list(set(characters)))  # 去重并排序
        logging.debug(f"CharacterDelegate: 设置角色列表 {self._character_list}")
        
    def get_character_list(self) -> List[str]:
        """获取当前角色列表"""
        return self._character_list.copy()
        
    def add_character(self, character: str):
        """添加新角色到列表"""
        if character and character not in self._character_list:
            self._character_list.append(character)
            self._character_list.sort()
            logging.debug(f"CharacterDelegate: 添加角色 '{character}'")
            
    def remove_character(self, character: str):
        """从列表中移除角色"""
        if character in self._character_list:
            self._character_list.remove(character)
            logging.debug(f"CharacterDelegate: 移除角色 '{character}'")
            
    def update_characters_from_model(self, model):
        """从表格模型自动更新角色列表"""
        if not self._auto_update or not model:
            return
            
        try:
            characters = set()
            
            # 从模型中提取所有角色
            for row in range(model.rowCount()):
                character_index = model.index(row, 1)  # 角色列是第1列（索引1）
                character = model.data(character_index, Qt.ItemDataRole.DisplayRole)
                if character and isinstance(character, str) and character.strip():
                    characters.add(character.strip())
                    
            # 更新角色列表
            new_list = sorted(list(characters))
            if new_list != self._character_list:
                self._character_list = new_list
                logging.debug(f"CharacterDelegate: 自动更新角色列表 {self._character_list}")
                
        except Exception as e:
            logging.error(f"CharacterDelegate: 自动更新角色列表失败: {e}")
            
    def createEditor(self, parent: QWidget, option, index: Union[QModelIndex, QPersistentModelIndex]) -> QWidget:
        """创建编辑器 - 下拉菜单"""
        try:
            # 在创建编辑器前，尝试从模型更新角色列表
            if hasattr(index, 'model') and index.model():
                self.update_characters_from_model(index.model())
            
            # 创建下拉菜单
            combo_box = QComboBox(parent)
            combo_box.setEditable(True)  # 允许输入新的角色名
            combo_box.setInsertPolicy(QComboBox.InsertPolicy.InsertAlphabetically)  # 按字母顺序插入
            
            # 添加现有角色到下拉菜单
            combo_box.addItems(self._character_list)
            
            # 设置样式
            combo_box.setStyleSheet("""
                QComboBox {
                    border: 1px solid #3daee9;
                    border-radius: 3px;
                    padding: 2px 5px;
                    background-color: white;
                }
                QComboBox:focus {
                    border: 2px solid #3daee9;
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border: 2px solid #666;
                    border-top: none;
                    border-right: none;
                    width: 6px;
                    height: 6px;
                    margin: 2px;
                    transform: rotate(-45deg);
                }
            """)
            
            logging.debug(f"CharacterDelegate: 创建编辑器，角色选项: {self._character_list}")
            return combo_box
            
        except Exception as e:
            logging.error(f"CharacterDelegate: 创建编辑器失败: {e}")
            # 失败时返回默认编辑器
            return super().createEditor(parent, option, index)
            
    def setEditorData(self, editor: QWidget, index: Union[QModelIndex, QPersistentModelIndex]):
        """设置编辑器的初始数据"""
        try:
            if not isinstance(editor, QComboBox):
                super().setEditorData(editor, index)
                return
                
            # 获取当前值
            current_value = index.model().data(index, Qt.ItemDataRole.EditRole)
            if current_value is None:
                current_value = ""
            else:
                current_value = str(current_value)
            
            # 设置下拉菜单的当前值
            combo_box = editor
            
            # 如果当前值在列表中，选择它
            index_in_list = combo_box.findText(current_value)
            if index_in_list >= 0:
                combo_box.setCurrentIndex(index_in_list)
            else:
                # 如果不在列表中，设置为可编辑文本
                combo_box.setEditText(current_value)
                
            logging.debug(f"CharacterDelegate: 设置编辑器数据为 '{current_value}'")
            
        except Exception as e:
            logging.error(f"CharacterDelegate: 设置编辑器数据失败: {e}")
            super().setEditorData(editor, index)
            
    def setModelData(self, editor: QWidget, model, index: Union[QModelIndex, QPersistentModelIndex]):
        """将编辑器的数据设置回模型"""
        try:
            if not isinstance(editor, QComboBox):
                super().setModelData(editor, model, index)
                return
                
            combo_box = editor
            new_value = combo_box.currentText().strip()
            
            # 设置模型数据
            success = model.setData(index, new_value, Qt.ItemDataRole.EditRole)
            
            if success:
                # 如果是新角色，添加到列表中
                if new_value and new_value not in self._character_list:
                    self.add_character(new_value)
                    
                logging.debug(f"CharacterDelegate: 设置模型数据为 '{new_value}'")
            else:
                logging.warning(f"CharacterDelegate: 设置模型数据失败 '{new_value}'")
                
        except Exception as e:
            logging.error(f"CharacterDelegate: 设置模型数据失败: {e}")
            super().setModelData(editor, model, index)
            
    def updateEditorGeometry(self, editor: QWidget, option, index: Union[QModelIndex, QPersistentModelIndex]):
        """更新编辑器的几何属性"""
        try:
            # 让编辑器稍微大一点，提供更好的用户体验
            rect = option.rect
            rect.setHeight(max(rect.height(), 25))  # 最小高度25像素
            editor.setGeometry(rect)
            
        except Exception as e:
            logging.error(f"CharacterDelegate: 更新编辑器几何属性失败: {e}")
            super().updateEditorGeometry(editor, option, index)
            
    def paint(self, painter: QPainter, option, index: Union[QModelIndex, QPersistentModelIndex]):
        """自定义绘制 - 显示下拉箭头提示"""
        try:
            # 使用默认绘制
            super().paint(painter, option, index)
            
            # 可以在这里添加自定义的视觉提示，比如小的下拉箭头
            # 但为了简单起见，暂时使用默认样式
            
        except Exception as e:
            logging.error(f"CharacterDelegate: 绘制失败: {e}")
            super().paint(painter, option, index)
            
    def set_auto_update(self, enabled: bool):
        """设置是否自动从模型更新角色列表"""
        self._auto_update = enabled
        logging.debug(f"CharacterDelegate: 自动更新设置为 {enabled}")
