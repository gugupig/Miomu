"""
ScriptTableModel - 专门用于编辑模式的表格模型
提供完整的 MVC 分离，支持复杂编辑功能
"""
import logging
from typing import List, Optional, Any, Union
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QPersistentModelIndex, Signal
from PySide6.QtGui import QBrush, QColor, QFont

from app.models.models import Cue


class ScriptTableModel(QAbstractTableModel):
    """
    剧本表格数据模型
    直接封装 script_data.cues 列表，提供完整的编辑支持
    """
    
    # 自定义信号
    dataModified = Signal()  # 数据被修改时发出
    cueAdded = Signal(int)   # 添加台词时发出 (index)
    cueRemoved = Signal(int) # 删除台词时发出 (index)
    validationError = Signal(str, int, int)  # 验证错误 (message, row, column)
    
    # 列定义
    COLUMN_ID = 0
    COLUMN_CHARACTER = 1
    COLUMN_LINE = 2
    COLUMN_PHONEMES = 3
    
    COLUMN_NAMES = ["ID", "角色", "台词", "音素"]
    COLUMN_COUNT = len(COLUMN_NAMES)
    
    def __init__(self, cues: Optional[List[Cue]] = None, parent=None):
        super().__init__(parent)
        self._cues: List[Cue] = cues or []
        self._original_cues: List[Cue] = []  # 用于撤销功能
        self._modified = False
        self._read_only_columns = {self.COLUMN_ID, self.COLUMN_PHONEMES}  # 只读列
        
        # 保存原始数据用于撤销
        self.save_snapshot()
        
    def save_snapshot(self):
        """保存当前状态的快照，用于撤销功能"""
        self._original_cues = [
            Cue(
                id=cue.id,
                character=cue.character,
                line=cue.line,
                phonemes=getattr(cue, 'phonemes', '')
            ) for cue in self._cues
        ]
        
    def restore_snapshot(self):
        """恢复到快照状态"""
        if self._original_cues:
            self.beginResetModel()
            self._cues = [
                Cue(
                    id=cue.id,
                    character=cue.character,
                    line=cue.line,
                    phonemes=getattr(cue, 'phonemes', '')
                ) for cue in self._original_cues
            ]
            self._modified = False
            self.endResetModel()
            logging.info("已恢复到上次保存的状态")
            
    def set_cues(self, cues: List[Cue]):
        """设置新的台词列表"""
        self.beginResetModel()
        self._cues = cues
        self._modified = False
        self.endResetModel()
        self.save_snapshot()
        
    def get_cues(self) -> List[Cue]:
        """获取当前台词列表"""
        return self._cues
        
    def is_modified(self) -> bool:
        """检查数据是否被修改"""
        return self._modified
        
    def mark_saved(self):
        """标记数据已保存"""
        self._modified = False
        self.save_snapshot()
        
    # === QAbstractTableModel 必需方法 ===
    
    def rowCount(self, parent: Union[QModelIndex, QPersistentModelIndex] = QModelIndex()) -> int:
        """返回行数"""
        if parent.isValid():
            return 0
        return len(self._cues)
        
    def columnCount(self, parent: Union[QModelIndex, QPersistentModelIndex] = QModelIndex()) -> int:
        """返回列数"""
        if parent.isValid():
            return 0
        return self.COLUMN_COUNT
        
    def data(self, index: Union[QModelIndex, QPersistentModelIndex], role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """返回指定位置的数据"""
        if not index.isValid():
            return None
            
        row, col = index.row(), index.column()
        if not (0 <= row < len(self._cues) and 0 <= col < self.COLUMN_COUNT):
            return None
            
        cue = self._cues[row]
        
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if col == self.COLUMN_ID:
                return str(cue.id)
            elif col == self.COLUMN_CHARACTER:
                return cue.character
            elif col == self.COLUMN_LINE:
                return cue.line
            elif col == self.COLUMN_PHONEMES:
                return getattr(cue, 'phonemes', '')
                
        elif role == Qt.ItemDataRole.BackgroundRole:
            # 只读列使用不同背景色
            if col in self._read_only_columns:
                return QBrush(QColor(240, 240, 240))
                
        elif role == Qt.ItemDataRole.FontRole:
            # 音素列使用等宽字体
            if col == self.COLUMN_PHONEMES:
                font = QFont("Consolas", 9)
                return font
                
        elif role == Qt.ItemDataRole.ToolTipRole:
            if col == self.COLUMN_ID:
                return "台词ID（只读）"
            elif col == self.COLUMN_CHARACTER:
                return "角色名称（可编辑）"
            elif col == self.COLUMN_LINE:
                return "台词内容（可编辑）"
            elif col == self.COLUMN_PHONEMES:
                return "音素转换结果（只读）"
                
        return None
        
    def setData(self, index: Union[QModelIndex, QPersistentModelIndex], value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        """设置指定位置的数据"""
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
            
        row, col = index.row(), index.column()
        if not (0 <= row < len(self._cues) and 0 <= col < self.COLUMN_COUNT):
            return False
            
        # 检查只读列
        if col in self._read_only_columns:
            return False
            
        cue = self._cues[row]
        old_value = None
        new_value = str(value).strip()
        
        # 验证数据
        if not self._validate_data(new_value, row, col):
            return False
            
        # 更新数据
        try:
            if col == self.COLUMN_CHARACTER:
                old_value = cue.character
                cue.character = new_value
            elif col == self.COLUMN_LINE:
                old_value = cue.line
                cue.line = new_value
            else:
                return False
                
            # 标记数据已修改
            if old_value != new_value:
                self._modified = True
                self.dataChanged.emit(index, index, [role])
                self.dataModified.emit()
                logging.debug(f"更新台词 {cue.id}: {col} 列从 '{old_value}' 改为 '{new_value}'")
                
            return True
            
        except Exception as e:
            logging.error(f"设置数据失败: {e}")
            return False
            
    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """返回表头数据"""
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            if 0 <= section < len(self.COLUMN_NAMES):
                return self.COLUMN_NAMES[section]
        elif orientation == Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return str(section + 1)  # 行号从1开始
            
        return None
        
    def flags(self, index: Union[QModelIndex, QPersistentModelIndex]) -> Qt.ItemFlag:
        """返回指定位置的标志"""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
            
        col = index.column()
        base_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        
        # 只读列不可编辑
        if col in self._read_only_columns:
            return base_flags
        else:
            return base_flags | Qt.ItemFlag.ItemIsEditable
            
    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        """排序"""
        if not (0 <= column < self.COLUMN_COUNT):
            return
            
        self.layoutAboutToBeChanged.emit()
        
        try:
            reverse = (order == Qt.SortOrder.DescendingOrder)
            
            if column == self.COLUMN_ID:
                self._cues.sort(key=lambda cue: cue.id, reverse=reverse)
            elif column == self.COLUMN_CHARACTER:
                self._cues.sort(key=lambda cue: cue.character, reverse=reverse)
            elif column == self.COLUMN_LINE:
                self._cues.sort(key=lambda cue: cue.line, reverse=reverse)
            elif column == self.COLUMN_PHONEMES:
                self._cues.sort(key=lambda cue: getattr(cue, 'phonemes', ''), reverse=reverse)
                
            self._modified = True
            self.dataModified.emit()
            
        except Exception as e:
            logging.error(f"排序失败: {e}")
            
        self.layoutChanged.emit()
        
    # === 扩展功能方法 ===
    
    def _validate_data(self, value: str, row: int, col: int) -> bool:
        """验证数据有效性"""
        try:
            if col == self.COLUMN_CHARACTER:
                if not value:
                    self.validationError.emit("角色名称不能为空", row, col)
                    return False
                if len(value) > 50:
                    self.validationError.emit("角色名称过长（最多50字符）", row, col)
                    return False
                    
            elif col == self.COLUMN_LINE:
                if not value:
                    self.validationError.emit("台词内容不能为空", row, col)
                    return False
                if len(value) > 1000:
                    self.validationError.emit("台词内容过长（最多1000字符）", row, col)
                    return False
                    
            return True
            
        except Exception as e:
            self.validationError.emit(f"验证数据时出错: {str(e)}", row, col)
            return False
            
    def add_cue(self, character: str = "", line: str = "", index: Optional[int] = None) -> bool:
        """添加新台词"""
        try:
            # 生成新ID
            max_id = max((cue.id for cue in self._cues), default=0)
            new_id = max_id + 1
            
            # 创建新台词
            new_cue = Cue(
                id=new_id,
                character=character,
                line=line,
                phonemes=""  # 需要重新生成
            )
            
            # 确定插入位置
            if index is None:
                index = len(self._cues)
            else:
                index = max(0, min(index, len(self._cues)))
                
            # 插入数据
            self.beginInsertRows(QModelIndex(), index, index)
            self._cues.insert(index, new_cue)
            self.endInsertRows()
            
            self._modified = True
            self.dataModified.emit()
            self.cueAdded.emit(index)
            
            logging.info(f"添加新台词: ID={new_id}, 角色='{character}', 位置={index}")
            return True
            
        except Exception as e:
            logging.error(f"添加台词失败: {e}")
            return False
            
    def remove_cue(self, index: int) -> bool:
        """删除台词"""
        if not (0 <= index < len(self._cues)):
            return False
            
        try:
            cue = self._cues[index]
            
            self.beginRemoveRows(QModelIndex(), index, index)
            del self._cues[index]
            self.endRemoveRows()
            
            self._modified = True
            self.dataModified.emit()
            self.cueRemoved.emit(index)
            
            logging.info(f"删除台词: ID={cue.id}, 角色='{cue.character}'")
            return True
            
        except Exception as e:
            logging.error(f"删除台词失败: {e}")
            return False
            
    def duplicate_cue(self, index: int) -> bool:
        """复制台词"""
        if not (0 <= index < len(self._cues)):
            return False
            
        try:
            original_cue = self._cues[index]
            return self.add_cue(
                character=original_cue.character,
                line=f"{original_cue.line} (副本)",
                index=index + 1
            )
            
        except Exception as e:
            logging.error(f"复制台词失败: {e}")
            return False
            
    def move_cue(self, from_index: int, to_index: int) -> bool:
        """移动台词位置"""
        if not (0 <= from_index < len(self._cues) and 0 <= to_index < len(self._cues)):
            return False
            
        if from_index == to_index:
            return True
            
        try:
            # 计算实际移动的目标位置
            if from_index < to_index:
                dest_index = to_index
            else:
                dest_index = to_index
                
            self.beginMoveRows(QModelIndex(), from_index, from_index, QModelIndex(), dest_index)
            cue = self._cues.pop(from_index)
            
            # 调整插入位置
            if from_index < to_index:
                self._cues.insert(to_index - 1, cue)
            else:
                self._cues.insert(to_index, cue)
                
            self.endMoveRows()
            
            self._modified = True
            self.dataModified.emit()
            
            logging.info(f"移动台词: 从位置 {from_index} 到位置 {to_index}")
            return True
            
        except Exception as e:
            logging.error(f"移动台词失败: {e}")
            return False
            
    def batch_update_character(self, old_character: str, new_character: str) -> int:
        """批量更新角色名称"""
        updated_count = 0
        
        try:
            for row, cue in enumerate(self._cues):
                if cue.character == old_character:
                    cue.character = new_character
                    index = self.index(row, self.COLUMN_CHARACTER)
                    self.dataChanged.emit(index, index, [Qt.ItemDataRole.EditRole])
                    updated_count += 1
                    
            if updated_count > 0:
                self._modified = True
                self.dataModified.emit()
                logging.info(f"批量更新角色名称: '{old_character}' -> '{new_character}', 共 {updated_count} 条")
                
            return updated_count
            
        except Exception as e:
            logging.error(f"批量更新角色名称失败: {e}")
            return 0
            
    def search_cues(self, text: str, column: Optional[int] = None) -> List[int]:
        """搜索台词，返回匹配的行索引列表"""
        if not text:
            return []
            
        matches = []
        text_lower = text.lower()
        
        try:
            for row, cue in enumerate(self._cues):
                match_found = False
                
                if column is None or column == self.COLUMN_CHARACTER:
                    if text_lower in cue.character.lower():
                        match_found = True
                        
                if column is None or column == self.COLUMN_LINE:
                    if text_lower in cue.line.lower():
                        match_found = True
                        
                if column is None or column == self.COLUMN_PHONEMES:
                    phonemes = getattr(cue, 'phonemes', '')
                    if text_lower in phonemes.lower():
                        match_found = True
                        
                if match_found:
                    matches.append(row)
                    
            logging.debug(f"搜索 '{text}' 找到 {len(matches)} 个匹配项")
            return matches
            
        except Exception as e:
            logging.error(f"搜索失败: {e}")
            return []
            
    def get_cue_by_row(self, row: int) -> Optional[Cue]:
        """根据行索引获取台词对象"""
        if 0 <= row < len(self._cues):
            return self._cues[row]
        return None
        
    def get_row_by_cue_id(self, cue_id: int) -> int:
        """根据台词ID获取行索引"""
        for row, cue in enumerate(self._cues):
            if cue.id == cue_id:
                return row
        return -1
        
    def refresh_phonemes(self, g2p_converter):
        """刷新所有台词的音素"""
        try:
            lines = [cue.line for cue in self._cues]
            all_phonemes = g2p_converter.batch_convert(lines)
            
            for cue, phonemes in zip(self._cues, all_phonemes):
                cue.phonemes = phonemes
                
            # 刷新音素列的显示
            top_left = self.index(0, self.COLUMN_PHONEMES)
            bottom_right = self.index(len(self._cues) - 1, self.COLUMN_PHONEMES)
            self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.DisplayRole])
            
            self._modified = True
            self.dataModified.emit()
            
            logging.info(f"已刷新 {len(self._cues)} 条台词的音素")
            
        except Exception as e:
            logging.error(f"刷新音素失败: {e}")
