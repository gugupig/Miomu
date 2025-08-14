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
    hash: Optional[str] = None  # 文件内容哈希值，用于缓存验证

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
    pure_line: str = ""  # 去除标点符号的台词（保留法语特殊字符）
    phonemes: Optional[str] = ""  # 音素转换结果
    character_cue_index: int = -1  # 角色台词索引
    translation: Dict[str, str] = field(default_factory=dict)  # 多语言翻译字典
    notes: Optional[str] = ""  # 备注
    style: str = "default"  # 样式名称
    # 新增：头部和尾部预处理字段
    head_tok: List[str] = field(default_factory=list)  # 头部词语列表
    head_phonemes: List[str] = field(default_factory=list)  # 头部音素列表
    tail_tok: List[str] = field(default_factory=list)  # 尾部词语列表
    tail_phonemes: List[str] = field(default_factory=list)  # 尾部音素列表
    # 新增：整句N-gram 特征字段
    line_ngram: List[tuple] = field(default_factory=list)  # 整句n-gram元组列表
    line_ngram_phonemes: List[tuple] = field(default_factory=list)  # 整句音素n-gram元组列表
    
    def get_translation(self, language_code: str) -> str:
        """获取指定语言的翻译"""
        return self.translation.get(language_code, "")
    
    def set_translation(self, language_code: str, text: str):
        """设置指定语言的翻译"""
        self.translation[language_code] = text
    
    def get_ngrams(self, n: int = 3, use_phonemes: bool = False) -> List[tuple]:
        """
        获取指定大小的n-gram特征
        
        Args:
            n: n-gram大小
            use_phonemes: 是否使用音素版本
            
        Returns:
            n-gram元组列表
        """
        if use_phonemes:
            ngrams = self.line_ngram_phonemes
        else:
            ngrams = self.line_ngram
        
        # 过滤指定大小的n-grams
        return [ngram for ngram in ngrams if len(ngram) == n]
    
    def has_ngrams(self) -> bool:
        """检查是否包含n-gram特征"""
        return bool(self.line_ngram or self.line_ngram_phonemes)
    
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
        """获取所有可用的语言列表"""
        languages = set()
        
        # 从meta中获取语言
        if self.meta.language:
            languages.update(self.meta.language)
        
        # 从cues的translation中获取语言
        for cue in self.cues:
            if cue.translation:
                languages.update(cue.translation.keys())
        
        return sorted(list(languages))
    
    def add_language_to_all_cues(self, language_code: str, default_text: str = ""):
        """为所有cue添加新语言列"""
        for cue in self.cues:
            if not cue.has_translation(language_code):
                cue.set_translation(language_code, default_text)
