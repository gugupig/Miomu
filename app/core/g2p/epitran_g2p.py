from typing import List
import os
import sys
import builtins
from .base import G2PConverter

try:
    import epitran
    EPITRAN_AVAILABLE = True
except ImportError:
    epitran = None
    EPITRAN_AVAILABLE = False

class EpitranG2P(G2PConverter):
    """
    基于 Epitran 库的 G2P 转换器
    支持多种语言的字素到音素转换
    """
    
    def __init__(self, language: str = 'fra-Latn'):
        """
        初始化 Epitran G2P 转换器
        
        Args:
            language: 语言代码，格式：lang-Script (例如: 'fra-Latn', 'eng-Latn', 'cmn-Hans')
                     常用语言代码:
                     - 'fra-Latn': 法语
                     - 'eng-Latn': 英语  
                     - 'deu-Latn': 德语
                     - 'spa-Latn': 西班牙语
                     - 'ita-Latn': 意大利语
                     - 'cmn-Hans': 中文简体
                     - 'jpn-Jpan': 日语
        """
        if not EPITRAN_AVAILABLE:
            raise ImportError("Epitran library is not installed. Please run 'pip install epitran'.")
        
        self.language = language
        
        try:
            # 基本的环境设置（全局monkey patch应该已在main.py中设置）
            self._setup_basic_encoding()
            
            self.epi = epitran.Epitran(self.language)  # type: ignore
            print(f"[EpitranG2P] ✅ Initialized for language: {self.language}")
                
        except Exception as e:
            # 提供友好的错误信息和建议
            print(f"[EpitranG2P] ❌ Failed to initialize for language: {self.language}")
            print(f"Error: {e}")
            
            # 检查是否是编码问题
            if "codec can't decode" in str(e) or "illegal multibyte sequence" in str(e):
                print("💡 这可能是编码问题。请确保:")
                print("   1. 主程序已正确设置全局编码处理")
                print("   2. 系统支持UTF-8编码")
                print("   - Windows: 检查区域设置")
                print("   - Linux/Mac: 检查 LANG 环境变量")
            
            # 提供常用语言代码建议
            common_langs = {
                'fr': 'fra-Latn',
                'en': 'eng-Latn', 
                'de': 'deu-Latn',
                'es': 'spa-Latn',
                'it': 'ita-Latn',
                'zh': 'cmn-Hans',
                'ja': 'jpn-Jpan'
            }
            
            print(f"💡 常用语言代码:")
            for short, full in common_langs.items():
                print(f"   {short} -> {full}")
            
            raise
    
    def _setup_basic_encoding(self):
        """基本编码环境设置（不含monkey patch）"""
        # 基本环境变量设置
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # Windows特定设置
        if os.name == 'nt':
            import locale
            try:
                locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
            except locale.Error:
                try:
                    locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
                except locale.Error:
                    pass

    def convert(self, text: str) -> str:
        """
        转换单个文本字符串为音素
        
        Args:
            text: 输入文本
            
        Returns:
            音素字符串
        """
        if not text or not text.strip():
            return ""
        
        try:
            # Epitran 返回 IPA 音素符号
            phonemes = self.epi.transliterate(text.strip())
            return phonemes
        except Exception as e:
            print(f"[EpitranG2P] Error converting '{text}': {e}")
            # 失败时返回原文本作为后备
            return text.strip()

    def batch_convert(self, texts: List[str]) -> List[str]:
        """
        批量转换文本列表为音素列表
        
        Args:
            texts: 输入文本列表
            
        Returns:
            音素字符串列表
        """
        return [self.convert(text) for text in texts]
    
    def get_available_languages(self) -> List[str]:
        """
        获取支持的语言列表 (如果 epitran 提供此功能)
        
        Returns:
            支持的语言代码列表
        """
        try:
            # 注意: epitran 可能不提供列出所有语言的方法
            # 这里返回一些常用的语言代码
            return [
                'fra-Latn',  # 法语
                'eng-Latn',  # 英语
                'deu-Latn',  # 德语
                'spa-Latn',  # 西班牙语
                'ita-Latn',  # 意大利语
                'por-Latn',  # 葡萄牙语
                'rus-Cyrl',  # 俄语
                'cmn-Hans',  # 中文简体
                'jpn-Jpan',  # 日语
                'kor-Hang',  # 韩语
                'ara-Arab',  # 阿拉伯语
                'hin-Deva',  # 印地语
            ]
        except Exception:
            return []
    
    def test_language_support(self, language: str) -> bool:
        """
        测试指定语言是否受支持
        
        Args:
            language: 语言代码
            
        Returns:
            是否支持该语言
        """
        try:
            if not EPITRAN_AVAILABLE or epitran is None:
                return False
            test_epi = epitran.Epitran(language)  # type: ignore
            # 进行简单测试
            test_result = test_epi.transliterate("test")
            return True
        except Exception:
            return False
