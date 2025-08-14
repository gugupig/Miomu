#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script Conversion Utilities
为Miomu项目提供剧本格式转换和音素处理功能
"""

import json
import re
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import sys
import os
import unicodedata

# 确保可以导入项目模块
current_dir = Path(__file__).parent
if current_dir.name == 'utils':
    # 如果在utils目录中
    sys.path.insert(0, str(current_dir.parent))
    sys.path.insert(0, str(current_dir.parent / "app"))
else:
    # 如果在项目根目录中
    sys.path.insert(0, str(current_dir))
    sys.path.insert(0, str(current_dir / "app"))

try:
    from app.core.g2p.epitran_g2p import EpitranG2P
    G2P_AVAILABLE = True
except ImportError:
    EpitranG2P = None
    G2P_AVAILABLE = False


class ScriptConverter:
    """剧本转换器类，提供音素转换和n-gram生成功能"""
    
    def __init__(self, language: str = 'fra-Latn', use_fallback: bool = True):
        """
        初始化转换器
        
        Args:
            language: 语言代码
            use_fallback: 如果G2P不可用，是否使用后备方案
        """
        self.language = language
        self.use_fallback = use_fallback
        self.g2p = None
        self._fallback_mode = False
        
        if G2P_AVAILABLE and EpitranG2P:
            try:
                self.g2p = EpitranG2P(language=language)
                print(f"✅ G2P转换器初始化成功 ({language})")
            except Exception as e:
                print(f"⚠️ G2P转换器初始化失败: {e}")
                if use_fallback:
                    print("🔄 将使用后备音素转换方案")
                    self._fallback_mode = True
                else:
                    raise
        else:
            if use_fallback:
                print("⚠️ Epitran不可用，使用后备音素转换方案")
                self._fallback_mode = True
            else:
                raise ImportError("Epitran库不可用且未启用后备方案")
    
    @staticmethod
    def clean_french_text(text: str) -> str:
        """
        清理法语文本，去除标点符号但保留法语特殊字符
        
        Args:
            text: 输入文本
            
        Returns:
            清理后的文本
        """
        if not text:
            return ""
        
        # 保留的法语特殊字符
        french_special_chars = set('àáâäçèéêëïîôùúûüÿñæœÀÁÂÄÇÈÉÊËÏÎÔÙÚÛÜŸÑÆŒ')
        
        # 去除标点符号，但保留字母、数字、空格和法语特殊字符
        cleaned_chars = []
        for char in text:
            if (char.isalnum() or 
                char.isspace() or 
                char in french_special_chars or
                unicodedata.category(char).startswith('L')):  # 所有字母类字符
                cleaned_chars.append(char)
            elif char in '-\'':  # 保留连字符和撇号（法语常用）
                cleaned_chars.append(char)
        
        # 合并连续空格
        cleaned_text = ''.join(cleaned_chars)
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
        
        return cleaned_text
    
    def _simple_phoneme_fallback(self, text: str) -> str:
        """
        简单的音素转换后备方案（主要针对法语）
        
        Args:
            text: 输入文本
            
        Returns:
            近似音素字符串
        """
        if not text:
            return ""
        
        text = text.lower()
        
        # 法语音素映射规则
        replacements = {
            'qu': 'k',
            'ch': 'ʃ',
            'j': 'ʒ',
            'gn': 'ɲ',
            'tion': 'sjɔ̃',
            'eau': 'o',
            'au': 'o',
            'ou': 'u',
            'ai': 'ɛ',
            'ei': 'ɛ',
            'oi': 'wa',
            'an': 'ɑ̃',
            'en': 'ɑ̃',
            'in': 'ɛ̃',
            'on': 'ɔ̃',
            'un': 'œ̃',
            'è': 'ɛ',
            'é': 'e',
            'ê': 'ɛ',
            'à': 'a',
            'ç': 's',
            'c': 'k',  # 简化处理
            'x': 'ks',
        }
        
        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
        
        return result
    
    def convert_to_phonemes(self, text: str) -> str:
        """
        将文本转换为音素
        
        Args:
            text: 输入文本
            
        Returns:
            音素字符串
        """
        if not text or not text.strip():
            return ""
        
        if self._fallback_mode or not self.g2p:
            return self._simple_phoneme_fallback(text)
        else:
            try:
                return self.g2p.convert(text)
            except Exception as e:
                print(f"⚠️ 音素转换失败，使用后备方案: {e}")
                return self._simple_phoneme_fallback(text)
    
    @staticmethod
    def tokenize_text(text: str, clean_punctuation: bool = True) -> List[str]:
        """
        将文本分词为token列表
        
        Args:
            text: 输入文本
            clean_punctuation: 是否在分词前清理标点符号
            
        Returns:
            token列表
        """
        if not text or not text.strip():
            return []
        
        # 如果需要清理标点符号，先清理
        if clean_punctuation:
            text = ScriptConverter.clean_french_text(text)
        
        # 使用正则表达式分词，针对清理后的文本
        if clean_punctuation:
            # 对于清理后的文本，只需要按空格分词，保留连字符
            tokens = re.findall(r'\S+', text.lower())
        else:
            # 对于原始文本，保留标点符号
            tokens = re.findall(r'\w+|[^\w\s]', text.lower())
        
        return [token for token in tokens if token.strip()]
    
    @staticmethod
    def create_ngrams(tokens: List[str], n: int = 3) -> List[Tuple[str, ...]]:
        """
        从token列表创建n-gram元组列表
        
        Args:
            tokens: token列表
            n: n-gram的大小
            
        Returns:
            n-gram元组列表
        """
        if not tokens or len(tokens) < n:
            return []
        
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i:i + n])
            ngrams.append(ngram)
        
        return ngrams
    
    @staticmethod
    def get_head_tail_tokens(tokens: List[str], head_size: int = 2, tail_size: int = 3) -> Tuple[List[str], List[str]]:
        """
        获取token列表的头部和尾部
        
        Args:
            tokens: token列表
            head_size: 头部大小
            tail_size: 尾部大小
            
        Returns:
            (头部tokens, 尾部tokens)
        """
        if not tokens:
            return [], []
        
        head_tokens = tokens[:head_size] if len(tokens) >= head_size else tokens[:]
        tail_tokens = tokens[-tail_size:] if len(tokens) >= tail_size else tokens[:]
        
        return head_tokens, tail_tokens
    
    def process_cue(self, cue_data: Dict[str, Any], n: int = 3, head_size: int = 2, tail_size: int = 3) -> Dict[str, Any]:
        """
        处理单个cue，添加音素和n-gram信息
        
        Args:
            cue_data: 原始cue数据
            n: n-gram大小
            head_size: 头部token数量
            tail_size: 尾部token数量
            
        Returns:
            处理后的cue数据
        """
        # 复制原有数据
        processed_cue = cue_data.copy()
        
        # 获取台词文本
        line = cue_data.get('line', '')
        
        # 生成清理后的台词（去除标点符号）
        pure_line = self.clean_french_text(line)
        processed_cue['pure_line'] = pure_line
        
        # 音素转换（使用清理后的台词）
        phonemes = self.convert_to_phonemes(pure_line)
        processed_cue['phonemes'] = phonemes
        
        # 确保必要字段存在
        if 'translation' not in processed_cue:
            processed_cue['translation'] = {}
        if 'notes' not in processed_cue:
            processed_cue['notes'] = ""
        if 'style' not in processed_cue:
            processed_cue['style'] = "default"
        
        # Token化（使用清理后的台词）
        tokens = self.tokenize_text(pure_line, clean_punctuation=False)  # pure_line已经清理过了
        
        # 获取头部和尾部tokens
        head_tokens, tail_tokens = self.get_head_tail_tokens(tokens, head_size, tail_size)
        
        # 头部和尾部音素转换
        head_phonemes = [self.convert_to_phonemes(token) for token in head_tokens]
        tail_phonemes = [self.convert_to_phonemes(token) for token in tail_tokens]
        
        # 添加新字段
        processed_cue['head_tok'] = head_tokens
        processed_cue['head_phonemes'] = head_phonemes
        processed_cue['tail_tok'] = tail_tokens
        processed_cue['tail_phonemes'] = tail_phonemes
        
        # 创建n-grams
        head_ngrams = self.create_ngrams(head_tokens, n)
        tail_ngrams = self.create_ngrams(tail_tokens, n)
        head_ngram_phonemes = self.create_ngrams(head_phonemes, n)
        tail_ngram_phonemes = self.create_ngrams(tail_phonemes, n)
        
        processed_cue['head_ngram'] = head_ngrams
        processed_cue['tail_ngram'] = tail_ngrams
        processed_cue['head_ngram_phonemes'] = head_ngram_phonemes
        processed_cue['tail_ngram_phonemes'] = tail_ngram_phonemes
        
        return processed_cue
    
    def convert_script(self, 
                      input_file: str, 
                      output_file: str, 
                      n: int = 3, 
                      head_size: int = 2, 
                      tail_size: int = 3,
                      verbose: bool = True) -> bool:
        """
        转换完整的剧本文件
        
        Args:
            input_file: 输入文件路径
            output_file: 输出文件路径
            n: n-gram大小
            head_size: 头部token数量
            tail_size: 尾部token数量
            verbose: 是否显示详细输出
            
        Returns:
            转换是否成功
        """
        try:
            # 读取输入文件
            if verbose:
                print(f"📖 正在读取输入文件: {input_file}")
            
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'cues' not in data:
                raise ValueError("输入文件格式错误：缺少 'cues' 字段")
            
            if verbose:
                print(f"📝 找到 {len(data['cues'])} 个对话条目")
            
            # 处理每个cue
            processed_cues = []
            for i, cue in enumerate(data['cues']):
                if verbose and (i + 1) % 10 == 0:
                    print(f"⚙️ 处理进度: {i+1}/{len(data['cues'])}")
                
                processed_cue = self.process_cue(cue, n, head_size, tail_size)
                processed_cues.append(processed_cue)
            
            # 构建输出数据 - 包含完整的文档结构
            output_data = {}
            
            # 处理 meta 信息
            if 'meta' in data:
                output_data['meta'] = data['meta']
                if verbose:
                    print(f"📋 保留原有 meta 信息")
            else:
                # 创建默认 meta 信息
                from datetime import datetime
                default_meta = {
                    "title": Path(input_file).stem,
                    "author": "",
                    "translator": "",
                    "version": "1.0",
                    "description": f"转换自 {Path(input_file).name}",
                    "language": ["fra-Latn"],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "license": ""
                }
                output_data['meta'] = default_meta
                if verbose:
                    print(f"📋 创建默认 meta 信息")
            
            # 处理 styles 信息
            if 'styles' in data:
                output_data['styles'] = data['styles']
                if verbose:
                    print(f"🎨 保留原有 styles 信息")
            else:
                # 创建默认 styles
                default_styles = {
                    "default": {
                        "font": "Noto Sans",
                        "size": 42,
                        "color": "#FFFFFF",
                        "pos": "bottom"
                    }
                }
                output_data['styles'] = default_styles
                if verbose:
                    print(f"🎨 创建默认 styles 信息")
            
            # 添加处理后的 cues
            output_data['cues'] = processed_cues
            
            # 保存输出文件
            if verbose:
                print(f"💾 正在保存输出文件: {output_file}")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            
            if verbose:
                print(f"✅ 转换成功！处理了 {len(processed_cues)} 个对话条目")
            
            return True
            
        except Exception as e:
            print(f"❌ 转换失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def convert_script_dialogues_to_converted(input_file: str, 
                                        output_file: str, 
                                        language: str = 'fra-Latn',
                                        n: int = 2,
                                        head_size: int = 2,
                                        tail_size: int = 3,
                                        verbose: bool = True) -> bool:
    """
    便捷函数：将script_dialogues转换为script_dialogues_converted格式
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径
        language: 语言代码
        n: n-gram大小
        head_size: 头部token数量 
        tail_size: 尾部token数量
        verbose: 是否显示详细输出
        c
    Returns:
        转换是否成功
    """
    converter = ScriptConverter(language=language, use_fallback=True)
    return converter.convert_script(input_file, output_file, n, head_size, tail_size, verbose)


if __name__ == '__main__':
    # 示例用法
    success = convert_script_dialogues_to_converted(
        'script_dialogues.json',
        'script_dialogues_converted.json',
        language='fra-Latn',
        n=2
    )
    
    if success:
        print("🎉 转换完成！")
    else:
        print("❌ 转换失败！")
