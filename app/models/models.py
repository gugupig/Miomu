from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime

@dataclass
class Meta:
    """字幕文件元数据"""
    title: str = ""
    author: str = ""
    translator: str = ""
    version: str = "1.0"
    description: str = ""
    language: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    license: str = ""

@dataclass
class Style:
    """字幕样式定义"""
    font: str = "Noto Sans"
    size: int = 42
    color: str = "#FFFFFF"
    pos: str = "bottom"

@dataclass
class Cue:
    id: int
    character: Optional[str]  # 可能为 null（舞台提示等）
    line: str
    phonemes: Optional[str] = ""  # 音素转换结果
    character_cue_index: int = -1  # 角色台词索引
    translation: Dict[str, str] = field(default_factory=dict)  # 多语言翻译字典
    notes: Optional[str] = ""  # 备注
    style: str = "default"  # 样式名称
    
    def get_translation(self, language_code: str) -> str:
        """获取指定语言的翻译"""
        return self.translation.get(language_code, "")
    
    def set_translation(self, language_code: str, text: str):
        """设置指定语言的翻译"""
        self.translation[language_code] = text
    
    def get_available_languages(self) -> List[str]:
        """获取已有翻译的语言列表"""
        return list(self.translation.keys())
    
    def has_translation(self, language_code: str) -> bool:
        """检查是否有指定语言的翻译"""
        return language_code in self.translation and bool(self.translation[language_code].strip())

@dataclass
class SubtitleDocument:
    """完整的字幕文档结构"""
    meta: Meta = field(default_factory=Meta)
    styles: Dict[str, Style] = field(default_factory=lambda: {"default": Style()})
    cues: List[Cue] = field(default_factory=list)
    
    def get_all_languages(self) -> List[str]:
        """获取文档中所有出现的语言代码"""
        languages = set()
        for cue in self.cues:
            languages.update(cue.get_available_languages())
        return sorted(list(languages))
    
    def add_language_to_all_cues(self, language_code: str, default_text: str = ""):
        """为所有cue添加新语言列"""
        for cue in self.cues:
            if not cue.has_translation(language_code):
                cue.set_translation(language_code, default_text)
