"""
G2P引擎管理器
统一管理所有G2P引擎的选择、创建和切换
"""

from typing import Optional, Dict, Any, List, Tuple
import logging
import os
import sys
from enum import Enum


class G2PEngineType(Enum):
    """G2P引擎类型枚举"""
    EPITRAN = "epitran"
    CHARSIU = "charsiu"
    PHONEMIZER = "phonemizer"
    SIMPLE = "simple"


class G2PManager:
    """G2P引擎管理器"""
    
    def __init__(self):
        self.current_engine_type = G2PEngineType.EPITRAN  # 默认使用Epitran
        self.current_language = "fra-Latn"  # 默认法语
        self.current_engine = None
        
        # 设置编码环境
        self._setup_encoding_environment()
        
        # 引擎配置信息
        self.engine_configs = {
            G2PEngineType.EPITRAN: {
                "name": "Epitran G2P",
                "description": "基于规则的多语言G2P，稳定可靠",
                "languages": {
                    "法语": "fra-Latn",
                    "英语": "eng-Latn", 
                    "德语": "deu-Latn",
                    "西班牙语": "spa-Latn",
                    "意大利语": "ita-Latn",
                    "中文": "cmn-Hans",
                    "日语": "jpn-Jpan"
                },
                "default_language": "fra-Latn",
                "requires_install": ["epitran"],
                "stability": "高",
                "speed": "快"
            },
            G2PEngineType.CHARSIU: {
                "name": "CharsiuG2P (ByT5)",
                "description": "基于AI的神经网络G2P，支持100种语言",
                "languages": {
                    "法语": "fra",
                    "英语": "eng",
                    "德语": "deu", 
                    "西班牙语": "spa",
                    "意大利语": "ita",
                    "中文": "cmn",
                    "日语": "jpn",
                    "俄语": "rus",
                    "阿拉伯语": "ara",
                    "印地语": "hin"
                },
                "default_language": "fra",
                "requires_install": ["transformers", "torch"],
                "stability": "中",
                "speed": "中"
            },
            G2PEngineType.PHONEMIZER: {
                "name": "Phonemizer G2P", 
                "description": "基于espeak-ng的专业G2P，质量高",
                "languages": {
                    "法语": "fr-fr",
                    "英语": "en-us",
                    "德语": "de-de",
                    "西班牙语": "es-es", 
                    "意大利语": "it-it",
                    "中文": "zh-cn"
                },
                "default_language": "fr-fr",
                "requires_install": ["phonemizer", "espeak-ng"],
                "stability": "高",
                "speed": "中"
            },
            G2PEngineType.SIMPLE: {
                "name": "Simple G2P",
                "description": "简单G2P，无依赖保底方案",
                "languages": {
                    "法语": "fr",
                    "英语": "en", 
                    "中文": "zh",
                    "通用": "universal"
                },
                "default_language": "fr",
                "requires_install": [],
                "stability": "中",
                "speed": "极快"
            }
        }
        
    def get_available_engines(self) -> List[Tuple[G2PEngineType, Dict[str, Any]]]:
        """获取可用的引擎列表，按推荐优先级排序"""
        available = []
        
        for engine_type in [G2PEngineType.EPITRAN, G2PEngineType.CHARSIU, 
                           G2PEngineType.PHONEMIZER, G2PEngineType.SIMPLE]:
            if self._check_engine_availability(engine_type):
                available.append((engine_type, self.engine_configs[engine_type]))
                
        return available
        
    def _check_engine_availability(self, engine_type: G2PEngineType) -> bool:
        """检查引擎是否可用"""
        try:
            if engine_type == G2PEngineType.EPITRAN:
                from app.core.g2p.epitran_g2p import EpitranG2P
                return True
            elif engine_type == G2PEngineType.CHARSIU:
                from app.core.g2p.charsiu_g2p import CharsiuG2P
                return True
            elif engine_type == G2PEngineType.PHONEMIZER:
                from app.core.g2p.phonemizer_g2p import PhonemizerG2P
                return True
            elif engine_type == G2PEngineType.SIMPLE:
                from app.core.g2p.simple_g2p import SimpleG2P
                return True
        except ImportError as e:
            logging.debug(f"引擎 {engine_type.value} 不可用: {e}")
            return False
        except Exception as e:
            logging.warning(f"检查引擎 {engine_type.value} 时出错: {e}")
            return False
            
        return False
        
    def create_engine(self, engine_type, language: Optional[str] = None):
        """创建G2P引擎实例"""
        # 处理字符串类型的engine_type
        if isinstance(engine_type, str):
            try:
                engine_type = G2PEngineType(engine_type)
            except ValueError:
                raise ValueError(f"不支持的引擎类型: {engine_type}")
        
        if engine_type is None:
            engine_type = self.current_engine_type
            
        if language is None:
            language = self.current_language
            
        try:
            if engine_type == G2PEngineType.EPITRAN:
                from app.core.g2p.epitran_g2p import EpitranG2P
                engine = EpitranG2P(language=str(language))
                logging.info(f"✅ 创建Epitran G2P引擎成功，语言: {language}")
                
            elif engine_type == G2PEngineType.CHARSIU:
                from app.core.g2p.charsiu_g2p import CharsiuG2P
                engine = CharsiuG2P(language=str(language))
                logging.info(f"✅ 创建CharsiuG2P引擎成功，语言: {language}")
                
            elif engine_type == G2PEngineType.PHONEMIZER:
                from app.core.g2p.phonemizer_g2p import PhonemizerG2P
                engine = PhonemizerG2P(language=str(language))
                logging.info(f"创建Phonemizer G2P引擎，语言: {language}")
                
            elif engine_type == G2PEngineType.SIMPLE:
                from app.core.g2p.simple_g2p import SimpleG2P
                engine = SimpleG2P(language=str(language))
                logging.info(f"创建Simple G2P引擎，语言: {language}")
                
            else:
                raise ValueError(f"不支持的引擎类型: {engine_type}")
                
            self.current_engine = engine
            self.current_engine_type = engine_type
            self.current_language = language
            
            return engine
            
        except Exception as e:
            error_msg = str(e)
            
            # 特殊处理编码错误
            if "codec can't decode" in error_msg or "illegal multibyte sequence" in error_msg:
                logging.error(f"❌ 创建G2P引擎失败 ({engine_type.value}): 编码问题 - {e}")
                logging.info("💡 这可能是由于系统编码设置导致的，正在尝试备用引擎...")
            else:
                logging.error(f"❌ 创建G2P引擎失败 ({engine_type.value}): {e}")
            
            # 尝试降级到下一个可用引擎
            return self._fallback_create_engine(engine_type)
            
    def _fallback_create_engine(self, failed_engine_type: G2PEngineType):
        """创建备用引擎"""
        # 定义降级顺序
        fallback_order = [
            G2PEngineType.EPITRAN,
            G2PEngineType.SIMPLE,  # Simple作为最后保底
            G2PEngineType.PHONEMIZER,
            G2PEngineType.CHARSIU
        ]
        
        # 移除失败的引擎类型
        if failed_engine_type in fallback_order:
            fallback_order.remove(failed_engine_type)
            
        for engine_type in fallback_order:
            if self._check_engine_availability(engine_type):
                try:
                    # 使用该引擎类型的默认语言
                    default_lang = self.engine_configs[engine_type]["default_language"]
                    return self.create_engine(engine_type, default_lang)
                except Exception as e:
                    logging.warning(f"备用引擎 {engine_type.value} 也失败: {e}")
                    continue
                    
        raise RuntimeError("所有G2P引擎都不可用")
        
    def get_best_available_engine(self):
        """获取最佳可用引擎"""
        # 按优先级尝试创建引擎
        priority_order = [
            G2PEngineType.EPITRAN,    # 主要推荐
            G2PEngineType.CHARSIU,    # AI强大但可能不稳定
            G2PEngineType.PHONEMIZER, # 质量高但依赖复杂
            G2PEngineType.SIMPLE      # 保底方案
        ]
        
        for engine_type in priority_order:
            if self._check_engine_availability(engine_type):
                try:
                    default_lang = self.engine_configs[engine_type]["default_language"]
                    engine = self.create_engine(engine_type, default_lang)
                    logging.info(f"选择最佳可用引擎: {self.engine_configs[engine_type]['name']}")
                    return engine
                except Exception as e:
                    logging.warning(f"尝试引擎 {engine_type.value} 失败: {e}")
                    continue
                    
        raise RuntimeError("没有可用的G2P引擎")
        
    def switch_engine(self, engine_type: G2PEngineType, language: Optional[str] = None):
        """切换G2P引擎"""
        if language is None:
            language = self.engine_configs[engine_type]["default_language"]
            
        old_engine_type = self.current_engine_type
        
        try:
            new_engine = self.create_engine(engine_type, language)
            
            # 清理旧引擎（如果有cleanup方法）
            if self.current_engine and hasattr(self.current_engine, 'cleanup'):
                try:
                    self.current_engine.cleanup()
                except Exception as e:
                    logging.warning(f"清理旧引擎时出错: {e}")
                
            self.current_engine = new_engine
            self.current_engine_type = engine_type
            self.current_language = language
            
            logging.info(f"G2P引擎已切换: {old_engine_type.value} -> {engine_type.value}")
            return new_engine
            
        except Exception as e:
            logging.error(f"切换G2P引擎失败: {e}")
            raise
            
    def get_current_engine(self):
        """获取当前引擎"""
        if self.current_engine is None:
            self.current_engine = self.get_best_available_engine()
        return self.current_engine
        
    def get_default_engine(self) -> str:
        """获取默认引擎名称"""
        return self.current_engine_type.value
        
    def set_default_engine(self, engine_name: str):
        """设置默认引擎"""
        try:
            # 将字符串转换为枚举
            engine_type = G2PEngineType(engine_name)
            self.current_engine_type = engine_type
            # 清空当前引擎，下次使用时会重新创建
            self.current_engine = None
        except ValueError:
            raise ValueError(f"不支持的引擎类型: {engine_name}")
        
    def get_current_engine_info(self) -> Dict[str, Any]:
        """获取当前引擎信息"""
        if self.current_engine is None:
            self.get_current_engine()
            
        return {
            "type": self.current_engine_type,
            "name": self.engine_configs[self.current_engine_type]["name"],
            "language": self.current_language,
            "config": self.engine_configs[self.current_engine_type]
        }
        
    def get_engine_languages(self, engine_type: G2PEngineType) -> Dict[str, str]:
        """获取指定引擎支持的语言"""
        return self.engine_configs[engine_type]["languages"]
        
    def convert_text(self, text: str, engine_type: Optional[G2PEngineType] = None, language: Optional[str] = None) -> str:
        """使用指定引擎转换文本"""
        if engine_type is not None or language is not None:
            # 临时切换引擎
            temp_engine = self.create_engine(engine_type, language)
            return temp_engine.convert(text)
        else:
            # 使用当前引擎
            engine = self.get_current_engine()
            return engine.convert(text)
            
    def batch_convert(self, texts: List[str], engine_type: Optional[G2PEngineType] = None, language: Optional[str] = None) -> List[str]:
        """批量转换文本"""
        if engine_type is not None or language is not None:
            # 临时切换引擎
            temp_engine = self.create_engine(engine_type, language)
            if hasattr(temp_engine, 'batch_convert'):
                return temp_engine.batch_convert(texts)
            else:
                return [temp_engine.convert(text) for text in texts]
        else:
            # 使用当前引擎
            engine = self.get_current_engine()
            if hasattr(engine, 'batch_convert'):
                return engine.batch_convert(texts)
            else:
                return [engine.convert(text) for text in texts]
    
    def _setup_encoding_environment(self):
        """设置UTF-8编码环境，解决Epitran编码问题"""
        try:
            # 设置Python IO编码
            if 'PYTHONIOENCODING' not in os.environ:
                os.environ['PYTHONIOENCODING'] = 'utf-8'
            
            # 设置语言环境
            if sys.platform.startswith('win'):
                if 'LANG' not in os.environ:
                    os.environ['LANG'] = 'en_US.UTF-8'
                if 'LC_ALL' not in os.environ:
                    os.environ['LC_ALL'] = 'en_US.UTF-8'
            
            logging.debug("G2P编码环境已设置")
        except Exception as e:
            logging.warning(f"设置G2P编码环境时出错: {e}")
