"""
ScriptTableModel - 专门用于编辑模式的表格模型
提供完整的 MVC 分离，支持复杂编辑功能和角色颜色显示
"""
import logging
from typing import List, Optional, Any, Union, Dict, Set
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex, QPersistentModelIndex, Signal
from PySide6.QtGui import QBrush, QColor, QFont

from app.models.models import Cue
from app.utils.character_color_manager import CharacterColorManager


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
    
    # 基础列（不包含音素，因为现在要根据是否有翻译动态调整）
    BASE_COLUMN_NAMES = ["序号", "角色", "台词"]
    # 音素列现在只在没有翻译语言时显示
    PHONEMES_COLUMN_NAME = "音素"
    
    def __init__(self, cues: Optional[List[Cue]] = None, character_color_manager: Optional[CharacterColorManager] = None, parent=None):
        super().__init__(parent)
        self._cues: List[Cue] = cues or []
        self._original_cues: List[Cue] = []  # 用于撤销功能
        self._modified = False
        self._read_only_columns = {self.COLUMN_ID, self.COLUMN_PHONEMES}  # 只读列
        
        # 角色颜色管理器
        self.character_color_manager = character_color_manager
        if self.character_color_manager:
            self.character_color_manager.colors_changed.connect(self._on_colors_changed)
        
        # 新增：支持动态翻译列  
        self.translation_columns: Dict[str, str] = {}  # 显示名 -> 语言代码
        self.extra_columns: Dict[str, List[str]] = {}  # 为兼容性保留，列名 -> 数据列表
        # 动态生成当前使用的列名
        self._current_columns = self.BASE_COLUMN_NAMES.copy()
        
        # 新增：语言列过滤支持（用于剧场模式）
        self._visible_languages: Optional[Set[str]] = None  # 可见的语言代码集合
        
        # 新增：高亮支持
        self._highlighted_rows: Set[int] = set()
        
        # 角色筛选
        self._filtered_characters: Optional[Set[str]] = None
        self._visible_rows: List[int] = []  # 可见行索引
        
        # 保存原始数据用于撤销
        self.save_snapshot()
        self._update_visible_rows()
        
        # 更新列显示
        self._update_current_columns()
        
    def _update_current_columns(self):
        """根据当前状态更新显示的列"""
        # 基础列始终包含 ID, 角色, 台词
        self._current_columns = self.BASE_COLUMN_NAMES.copy()
        
        # 如果有翻译语言，显示翻译列（考虑语言过滤）
        if self.translation_columns:
            for display_name, lang_code in self.translation_columns.items():
                # 如果设置了语言过滤，只显示选中的语言
                if self._visible_languages is None or lang_code in self._visible_languages:
                    self._current_columns.append(display_name)
        # 注意：不再显示音素列，音素数据仅用于后台对齐
        
        # 兼容性：添加extra_columns
        self._current_columns.extend(list(self.extra_columns.keys()))
        
    def save_snapshot(self):
        """保存当前状态的快照，用于撤销功能"""
        self._original_cues = [
            Cue(
                id=cue.id,
                character=cue.character,
                line=cue.line,
                phonemes=getattr(cue, 'phonemes', ''),
                character_cue_index=getattr(cue, 'character_cue_index', -1),
                translation=getattr(cue, 'translation', {}).copy(),  # 深拷贝字典
                notes=getattr(cue, 'notes', ''),
                style=getattr(cue, 'style', 'default')
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
                    phonemes=getattr(cue, 'phonemes', ''),
                    character_cue_index=getattr(cue, 'character_cue_index', -1),
                    translation=getattr(cue, 'translation', {}).copy(),  # 深拷贝字典
                    notes=getattr(cue, 'notes', ''),
                    style=getattr(cue, 'style', 'default')
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
        
        # 清理之前的翻译列配置，避免加载新剧本时列累积
        self.translation_columns.clear()
        self.extra_columns.clear()
        
        # 清理语言过滤设置
        self._visible_languages = None
        
        # 更新列显示
        self._update_current_columns()
        
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
        """返回行数（考虑筛选）"""
        if parent.isValid():
            return 0
        return len(self._visible_rows) if self._filtered_characters is not None else len(self._cues)
        
    def columnCount(self, parent: Union[QModelIndex, QPersistentModelIndex] = QModelIndex()) -> int:
        """返回列数"""
        if parent.isValid():
            return 0
        return len(self._current_columns)
        
    def data(self, index: Union[QModelIndex, QPersistentModelIndex], role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        """返回指定位置的数据"""
        if not index.isValid():
            return None
            
        row, col = index.row(), index.column()
        if not (0 <= row < self.rowCount() and 0 <= col < self.columnCount()):
            return None
        
        # 转换为实际行索引（考虑筛选）
        actual_row = self.get_actual_row(row) if self._filtered_characters is not None else row
        if actual_row < 0 or actual_row >= len(self._cues):
            return None
            
        cue = self._cues[actual_row]
        
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            # 根据当前列的配置返回数据
            if col < len(self.BASE_COLUMN_NAMES):
                # 基础列: ID, 角色, 台词
                if col == self.COLUMN_ID:
                    # 显示角色的character_cue_index值而不是id
                    return str(getattr(cue, 'character_cue_index', ''))
                elif col == self.COLUMN_CHARACTER:
                    return cue.character or ""  # 处理 None 的情况
                elif col == self.COLUMN_LINE:
                    return cue.line
            else:
                # 翻译列处理（音素列不再显示）
                translation_index = col - len(self.BASE_COLUMN_NAMES)
                if translation_index < len(self.translation_columns):
                    # 获取翻译列的显示名
                    display_names = list(self.translation_columns.keys())
                    display_name = display_names[translation_index]
                    # 获取对应的语言代码
                    lang_code = self.translation_columns[display_name]
                    
                    # 确保Cue有translation字典
                    if not hasattr(cue, 'translation') or cue.translation is None:
                        cue.translation = {}
                    
                    # 如果该语言的key不存在，自动添加并设置为空字符串
                    if lang_code not in cue.translation:
                        cue.translation[lang_code] = ""
                        logging.debug(f"为台词 {cue.id} 自动添加翻译语言 {lang_code} 的空值")
                    
                    return cue.translation[lang_code]
                    
                # 为兼容性保留extra_columns处理
                extra_index = translation_index - len(self.translation_columns)
                extra_keys = list(self.extra_columns.keys())
                if extra_index >= 0 and extra_index < len(extra_keys):
                    language = extra_keys[extra_index]
                    return self.extra_columns[language][row] if row < len(self.extra_columns[language]) else ""
                    
        elif role == Qt.ItemDataRole.BackgroundRole:
            # 高亮显示
            if self.is_row_highlighted(actual_row):
                return QBrush(QColor(100, 200, 100, 100))
            # 只读列使用不同背景色：只有ID列是只读的
            if col == self.COLUMN_ID:
                return QBrush(QColor(240, 240, 240))
                
        elif role == Qt.ItemDataRole.ForegroundRole:
            # 角色颜色显示 - ID列和角色列使用相同颜色
            if self.character_color_manager and (col == self.COLUMN_ID or col == self.COLUMN_CHARACTER):
                character = cue.character
                color = self.character_color_manager.get_character_color(character)
                return QBrush(QColor(color))
            # 为台词列也应用角色颜色（可选）
            elif self.character_color_manager and col == self.COLUMN_LINE:
                character = cue.character
                color = self.character_color_manager.get_character_color(character)
                return QBrush(QColor(color))
                
        elif role == Qt.ItemDataRole.FontRole:
            # 角色名称使用粗体
            if col == self.COLUMN_CHARACTER:
                font = QFont()
                font.setBold(True)
                return font
                
        elif role == Qt.ItemDataRole.ToolTipRole:
            if col == self.COLUMN_ID:
                return "角色台词索引（只读）"
            elif col == self.COLUMN_CHARACTER:
                return "角色名称（可编辑）"
            elif col == self.COLUMN_LINE:
                return "台词内容（可编辑）"
            else:
                # 翻译列的提示
                translation_index = col - len(self.BASE_COLUMN_NAMES)
                if translation_index < len(self.translation_columns):
                    display_names = list(self.translation_columns.keys())
                    language_name = display_names[translation_index]
                    return f"{language_name} 翻译（可编辑）"
                
        return None
        
    def setData(self, index: Union[QModelIndex, QPersistentModelIndex], value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        """设置指定位置的数据"""
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
            
        row, col = index.row(), index.column()
        if not (0 <= row < len(self._cues) and 0 <= col < self.columnCount()):
            return False
            
        # 检查只读列：只有ID列是只读的
        if col == self.COLUMN_ID:
            return False
            
        cue = self._cues[row]
        old_value = None
        new_value = str(value).strip()
        
        # 验证数据
        if not self._validate_data(new_value, row, col):
            return False
            
        # 更新数据
        try:
            if col < len(self.BASE_COLUMN_NAMES):
                # 基础列
                if col == self.COLUMN_CHARACTER:
                    old_value = cue.character
                    cue.character = new_value
                elif col == self.COLUMN_LINE:
                    old_value = cue.line
                    cue.line = new_value
                else:
                    return False
            else:
                # 翻译列处理（音素列不再可编辑）
                translation_index = col - len(self.BASE_COLUMN_NAMES)
                
                if translation_index < len(self.translation_columns):
                    # 翻译列编辑
                    display_names = list(self.translation_columns.keys())
                    display_name = display_names[translation_index]
                    lang_code = self.translation_columns[display_name]
                    
                    # 确保Cue有translation字典
                    if not hasattr(cue, 'translation') or cue.translation is None:
                        cue.translation = {}
                    
                    old_value = cue.translation.get(lang_code, "")
                    cue.translation[lang_code] = new_value
                    
                else:
                    # 兼容性处理extra_columns
                    extra_index = translation_index - len(self.translation_columns)
                    languages = list(self.extra_columns.keys())
                    if extra_index >= 0 and extra_index < len(languages):
                        language = languages[extra_index]
                        if row < len(self.extra_columns[language]):
                            old_value = self.extra_columns[language][row]
                        else:
                            # 扩展列表到所需长度
                            while len(self.extra_columns[language]) <= row:
                                self.extra_columns[language].append("")
                            old_value = ""
                        self.extra_columns[language][row] = new_value
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
            if section < len(self._current_columns):
                return self._current_columns[section]
        elif orientation == Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return str(section + 1)  # 行号从1开始
        return None
        
    def flags(self, index: Union[QModelIndex, QPersistentModelIndex]) -> Qt.ItemFlag:
        """返回指定位置的标志"""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
            
        col = index.column()
        base_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        
        # 只读列不可编辑：只有ID列是只读的
        if col == self.COLUMN_ID:
            return base_flags
        else:
            return base_flags | Qt.ItemFlag.ItemIsEditable
            
    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        """排序"""
        if not (0 <= column < len(self._current_columns)):
            return
            
        self.layoutAboutToBeChanged.emit()
        
        try:
            reverse = (order == Qt.SortOrder.DescendingOrder)
            
            if column == self.COLUMN_ID:
                self._cues.sort(key=lambda cue: cue.id, reverse=reverse)
            elif column == self.COLUMN_CHARACTER:
                self._cues.sort(key=lambda cue: cue.character or "", reverse=reverse)
            elif column == self.COLUMN_LINE:
                self._cues.sort(key=lambda cue: cue.line, reverse=reverse)
            # 音素列不再显示，因此不需要排序逻辑
                
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
                character=original_cue.character or "",  # 处理 None 值
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
                    if cue.character and text_lower in cue.character.lower():  # 检查 None
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
            
    # === 多语言支持方法 ===
    
    def add_language_column(self, language_name: str, lang_code: str, translations: List[str] | None = None) -> bool:
        """添加新翻译语言列"""
        if language_name in self.translation_columns:
            return False
            
        self.beginInsertColumns(QModelIndex(), self.columnCount(), self.columnCount())
        self.translation_columns[language_name] = lang_code
        
        # 更新列显示
        self._update_current_columns()
        
        # 如果提供了翻译数据，设置到对应的Cue对象中
        if translations is not None:
            for i, translation in enumerate(translations):
                if i < len(self._cues):
                    cue = self._cues[i]
                    if not hasattr(cue, 'translation') or cue.translation is None:
                        cue.translation = {}
                    cue.translation[lang_code] = translation
        
        self.endInsertColumns()
        
        self._modified = True
        self.dataModified.emit()
        return True
        
    def ensure_translation_completeness(self):
        """确保所有台词的翻译字典包含所有语言的key"""
        if not self.translation_columns:
            return
            
        fixed_count = 0
        for cue in self._cues:
            # 确保台词有translation字典
            if not hasattr(cue, 'translation') or cue.translation is None:
                cue.translation = {}
                fixed_count += 1
            
            # 为每个翻译语言确保有对应的key
            for lang_name, lang_code in self.translation_columns.items():
                if lang_code not in cue.translation:
                    cue.translation[lang_code] = ""
                    fixed_count += 1
                    logging.debug(f"为台词 {cue.id} 自动添加翻译语言 {lang_code} 的空值")
        
        if fixed_count > 0:
            logging.info(f"修复了 {fixed_count} 个缺失的翻译字典条目")
            self._modified = True
            self.dataModified.emit()
        
    def remove_language_column(self, language_name: str) -> bool:
        """移除翻译语言列"""
        if language_name not in self.translation_columns:
            return False
            
        # 找到列索引
        column_index = len(self.BASE_COLUMN_NAMES) + list(self.translation_columns.keys()).index(language_name)
        lang_code = self.translation_columns[language_name]
        
        self.beginRemoveColumns(QModelIndex(), column_index, column_index)
        
        # 从所有Cue对象中移除对应的翻译数据
        for cue in self._cues:
            if hasattr(cue, 'translation') and cue.translation and lang_code in cue.translation:
                del cue.translation[lang_code]
        
        del self.translation_columns[language_name]
        
        # 更新列显示
        self._update_current_columns()
        
        self.endRemoveColumns()
        
        self._modified = True
        self.dataModified.emit()
        return True
        
    def get_language_columns(self) -> List[str]:
        """获取所有翻译语言列名"""
        return list(self.translation_columns.keys())
        
    def set_translation(self, row: int, language_name: str, translation: str) -> bool:
        """设置指定行和语言的翻译"""
        if language_name not in self.translation_columns or row < 0 or row >= len(self._cues):
            return False
            
        lang_code = self.translation_columns[language_name]
        cue = self._cues[row]
        
        if not hasattr(cue, 'translation') or cue.translation is None:
            cue.translation = {}
            
        cue.translation[lang_code] = translation
        
        # 发射数据变化信号
        column_index = len(self.BASE_COLUMN_NAMES) + list(self.translation_columns.keys()).index(language_name)
        index = self.index(row, column_index)
        self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
        
        self._modified = True
        self.dataModified.emit()
        return True
        
    def get_translation(self, row: int, language_name: str) -> str:
        """获取指定行和语言的翻译"""
        if language_name not in self.translation_columns or row < 0 or row >= len(self._cues):
            return ""
            
        lang_code = self.translation_columns[language_name]
        cue = self._cues[row]
        
        if hasattr(cue, 'translation') and cue.translation and lang_code in cue.translation:
            return cue.translation[lang_code]
        return ""
    
    # === 角色颜色相关方法 ===
    
    def set_character_color_manager(self, manager: CharacterColorManager):
        """设置角色颜色管理器"""
        if self.character_color_manager:
            self.character_color_manager.colors_changed.disconnect(self._on_colors_changed)
            
        self.character_color_manager = manager
        if self.character_color_manager:
            self.character_color_manager.colors_changed.connect(self._on_colors_changed)
            
        # 重新渲染表格
        self.layoutChanged.emit()
    
    def _on_colors_changed(self):
        """颜色配置变化时的处理"""
        # 重新渲染角色列和台词列
        if self.rowCount() > 0:
            top_left = self.index(0, self.COLUMN_CHARACTER)
            bottom_right = self.index(self.rowCount() - 1, self.COLUMN_LINE)
            self.dataChanged.emit(top_left, bottom_right, [Qt.ItemDataRole.ForegroundRole])
    
    # === 角色筛选相关方法 ===
    
    def set_character_filter(self, characters: Optional[Set[str]]):
        """设置角色筛选器"""
        self._filtered_characters = characters
        self._update_visible_rows()
        self.layoutChanged.emit()
    
    def clear_character_filter(self):
        """清除角色筛选器"""
        self._filtered_characters = None
        self._update_visible_rows()
        self.layoutChanged.emit()
    
    def _update_visible_rows(self):
        """更新可见行列表"""
        if self._filtered_characters is None:
            # 没有筛选，显示所有行
            self._visible_rows = list(range(len(self._cues)))
        else:
            # 根据角色筛选
            self._visible_rows = []
            for i, cue in enumerate(self._cues):
                if cue.character in self._filtered_characters or cue.character is None:
                    self._visible_rows.append(i)
    
    def get_actual_row(self, visible_row: int) -> int:
        """将可见行索引转换为实际行索引"""
        if 0 <= visible_row < len(self._visible_rows):
            return self._visible_rows[visible_row]
        return -1
    
    def get_visible_row(self, actual_row: int) -> int:
        """将实际行索引转换为可见行索引"""
        try:
            return self._visible_rows.index(actual_row)
        except ValueError:
            return -1
    
    def get_all_characters(self) -> Set[str]:
        """获取所有角色名称"""
        characters = set()
        for cue in self._cues:
            if cue.character:
                characters.add(cue.character)
        return characters
        
    # === 高亮支持方法 ===
    
    def highlight_row(self, row: int):
        """高亮指定行"""
        if 0 <= row < len(self._cues):
            self._highlighted_rows.add(row)
            # 通知视图更新整行
            left_index = self.index(row, 0)
            right_index = self.index(row, self.columnCount() - 1)
            self.dataChanged.emit(left_index, right_index, [Qt.ItemDataRole.BackgroundRole])
            
    def clear_highlighting(self):
        """清除所有高亮"""
        if self._highlighted_rows:
            highlighted_rows = list(self._highlighted_rows)
            self._highlighted_rows.clear()
            
            # 通知视图更新这些行
            for row in highlighted_rows:
                left_index = self.index(row, 0)
                right_index = self.index(row, self.columnCount() - 1)
                self.dataChanged.emit(left_index, right_index, [Qt.ItemDataRole.BackgroundRole])
                
    def is_row_highlighted(self, row: int) -> bool:
        """检查行是否被高亮"""
        return row in self._highlighted_rows
        
    # === 语言列过滤方法 ===
    
    def set_visible_languages(self, language_codes: Optional[Set[str]]):
        """设置可见的语言列（用于剧场模式）"""
        if self._visible_languages == language_codes:
            return  # 没有变化，直接返回
            
        self._visible_languages = language_codes
        
        # 重新计算列数
        old_column_count = self.columnCount()
        self._update_current_columns()
        new_column_count = self.columnCount()
        
        # 通知视图列结构发生变化
        if old_column_count != new_column_count:
            self.beginResetModel()
            self.endResetModel()
        else:
            # 列数相同但内容可能不同，刷新所有数据
            if self._cues:
                top_left = self.index(0, 0)
                bottom_right = self.index(len(self._cues) - 1, new_column_count - 1)
                self.dataChanged.emit(top_left, bottom_right)
        
    def clear_language_filter(self):
        """清除语言过滤，显示所有翻译列"""
        self.set_visible_languages(None)
        
    def get_visible_languages(self) -> Optional[Set[str]]:
        """获取当前可见的语言代码集合"""
        return self._visible_languages
        
    def get_all_translation_languages(self) -> Dict[str, str]:
        """获取所有可用的翻译语言（显示名 -> 语言代码）"""
        return self.translation_columns.copy()
