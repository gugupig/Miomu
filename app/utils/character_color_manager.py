"""
角色颜色管理功能模块
用于管理不同角色的显示颜色配置
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QColor
import json
import os

@dataclass
class CharacterColor:
    """角色颜色配置"""
    name: str
    color: str = "#000000"  # 默认黑色
    is_system: bool = False  # 是否为系统内置角色
    
    def to_qcolor(self) -> QColor:
        """转换为QColor对象"""
        return QColor(self.color)
    
    def set_from_qcolor(self, qcolor: QColor):
        """从QColor对象设置颜色"""
        self.color = qcolor.name()

class CharacterColorManager(QObject):
    """角色颜色管理器"""
    
    # 信号
    colors_changed = Signal()  # 颜色配置发生变化
    character_added = Signal(str)  # 添加了新角色
    character_removed = Signal(str)  # 删除了角色
    
    # 默认颜色调色板
    DEFAULT_COLORS = [
        "#FF6B6B",  # 红色
        "#4ECDC4",  # 青色
        "#45B7D1",  # 蓝色
        "#96CEB4",  # 绿色
        "#FECA57",  # 黄色
        "#FF9FF3",  # 粉色
        "#54A0FF",  # 深蓝色
        "#5F27CD",  # 紫色
        "#00D2D3",  # 青绿色
        "#FF9F43",  # 橙色
        "#8395A7",  # 灰色
        "#222F3E",  # 深灰色
    ]
    
    def __init__(self, config_file: Optional[str] = None):
        super().__init__()
        self.config_file = config_file or "character_colors.json"
        self.character_colors: Dict[str, CharacterColor] = {}
        self._color_index = 0  # 用于自动分配颜色
        
        # 加载配置
        self.load_config()
    
    def get_character_color(self, character_name: Optional[str]) -> str:
        """获取角色颜色，如果角色不存在则自动创建"""
        if not character_name:
            return "#808080"  # 灰色用于无角色的台词
        
        if character_name not in self.character_colors:
            self.add_character(character_name)
        
        return self.character_colors[character_name].color
    
    def get_character_qcolor(self, character_name: Optional[str]) -> QColor:
        """获取角色QColor对象"""
        return QColor(self.get_character_color(character_name))
    
    def add_character(self, character_name: str, color: Optional[str] = None) -> bool:
        """添加新角色"""
        if character_name in self.character_colors:
            return False  # 角色已存在
        
        if color is None:
            color = self._get_next_default_color()
        
        self.character_colors[character_name] = CharacterColor(
            name=character_name,
            color=color,
            is_system=False
        )
        
        self.character_added.emit(character_name)
        self.colors_changed.emit()
        return True
    
    def remove_character(self, character_name: str) -> bool:
        """删除角色"""
        if character_name not in self.character_colors:
            return False
        
        character_color = self.character_colors[character_name]
        if character_color.is_system:
            return False  # 不能删除系统角色
        
        del self.character_colors[character_name]
        self.character_removed.emit(character_name)
        self.colors_changed.emit()
        return True
    
    def set_character_color(self, character_name: str, color: str):
        """设置角色颜色"""
        if character_name not in self.character_colors:
            self.add_character(character_name, color)
        else:
            self.character_colors[character_name].color = color
            self.colors_changed.emit()
    
    def get_all_characters(self) -> List[str]:
        """获取所有角色名称列表"""
        return sorted(self.character_colors.keys())
    
    def get_character_colors_dict(self) -> Dict[str, str]:
        """获取角色颜色字典"""
        return {name: char.color for name, char in self.character_colors.items()}
    
    def import_characters_from_cues(self, cues: List) -> int:
        """从台词列表中导入角色，返回新增角色数量"""
        new_count = 0
        characters = set()
        
        # 收集所有角色名称
        for cue in cues:
            if hasattr(cue, 'character') and cue.character:
                characters.add(cue.character)
        
        # 添加新角色
        for character in characters:
            if self.add_character(character):
                new_count += 1
        
        return new_count
    
    def reset_to_default_colors(self):
        """重置所有角色为默认颜色"""
        self._color_index = 0
        for character_name in self.character_colors:
            if not self.character_colors[character_name].is_system:
                self.character_colors[character_name].color = self._get_next_default_color()
        
        self.colors_changed.emit()
    
    def _get_next_default_color(self) -> str:
        """获取下一个默认颜色"""
        color = self.DEFAULT_COLORS[self._color_index % len(self.DEFAULT_COLORS)]
        self._color_index += 1
        return color
    
    def load_config(self):
        """加载颜色配置"""
        if not os.path.exists(self.config_file):
            self._create_default_config()
            return
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.character_colors.clear()
            for name, color_data in data.get('character_colors', {}).items():
                if isinstance(color_data, str):
                    # 兼容旧格式
                    self.character_colors[name] = CharacterColor(
                        name=name,
                        color=color_data,
                        is_system=False
                    )
                else:
                    # 新格式
                    self.character_colors[name] = CharacterColor(
                        name=name,
                        color=color_data.get('color', '#000000'),
                        is_system=color_data.get('is_system', False)
                    )
            
            self._color_index = data.get('color_index', 0)
            
        except Exception as e:
            print(f"加载角色颜色配置失败: {e}")
            self._create_default_config()
    
    def save_config(self):
        """保存颜色配置"""
        try:
            data = {
                'character_colors': {
                    name: {
                        'color': char.color,
                        'is_system': char.is_system
                    } for name, char in self.character_colors.items()
                },
                'color_index': self._color_index
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            print(f"保存角色颜色配置失败: {e}")
    
    def _create_default_config(self):
        """创建默认配置"""
        self.character_colors = {
            "旁白": CharacterColor("旁白", "#808080", is_system=True),
            "未知角色": CharacterColor("未知角色", "#000000", is_system=True)
        }
        self._color_index = 0
        self.save_config()
