#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版剧本加载器
支持meta词条检验、dataclass格式校验、音素检验、缓存等功能
"""

import json
import logging
import hashlib
import pickle
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import asdict, is_dataclass
from datetime import datetime

from app.models.models import Meta, Style, Cue, SubtitleDocument
from app.core.g2p.base import G2PConverter
try:
    from app.utils.script_conversion_utils import ScriptConverter
    CONVERSION_AVAILABLE = True
except ImportError:
    ScriptConverter = None
    CONVERSION_AVAILABLE = False


class ScriptValidationError(Exception):
    """剧本验证错误"""
    pass


class EnhancedScriptLoader:
    """增强版剧本加载器"""
    
    def __init__(self, g2p_converter: Optional[G2PConverter] = None, head_tail_count: int = 5):
        self.g2p_converter = g2p_converter
        self.validation_results = {}
        self.conversion_results = {}
        self.head_tail_count = head_tail_count  # 头部和尾部词语数量
        self.cache_dir = Path("cache/scripts")  # 缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
    def load_script(self, filepath: str) -> Tuple[SubtitleDocument, Dict[str, Any]]:
        """
        加载剧本文件
        
        Returns:
            Tuple[SubtitleDocument, Dict]: (加载的文档, 加载报告)
        """
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"剧本文件不存在: {file_path}")
            
        print(f"🔍 开始加载剧本: {file_path.name}")
        
        # 1. 计算文件哈希
        file_hash = self._calculate_file_hash(file_path)
        print(f"🔍 文件哈希: {file_hash[:16]}...")
        
        # 2. 检查缓存
        cached_document = self._load_from_cache(file_hash)
        if cached_document:
            print("✅ 从缓存加载成功")
            report = self._generate_cache_report(cached_document)
            return cached_document, report
        
        # 3. 加载JSON数据
        raw_data = self._load_json(file_path)
        
        # 4. 检查是否有meta词条
        has_meta = self._check_meta_field(raw_data)
        
        if not has_meta:
            print("⚠️ 未发现meta词条，调用转换脚本...")
            raw_data = self._convert_legacy_format(raw_data, file_path)
            
        # 5. 进行dataclass格式校验
        print("🔍 进行dataclass格式校验...")
        document = self._validate_and_create_document(raw_data)
        
        # 6. 设置文件哈希到meta中
        document.meta.hash = file_hash
        document.meta.updated_at = datetime.now().isoformat()
        
        # 7. 检查音素并进行G2P处理
        print("🔍 检查音素数据...")
        g2p_results = self._process_phonemes(document)
        
        # 8. 处理头部和尾部词语
        print("🔍 处理头部和尾部词语...")
        head_tail_results = self._process_head_tail_tokens(document)
        
        # 9. 处理整句n-gram生成
        print("🔍 生成整句n-gram特征...")
        ngram_results = self._process_line_ngrams(document, n=2)
        
        # 10. 保存到缓存
        self._save_to_cache(document, file_hash)
        
        # 11. 生成加载报告
        report = self._generate_load_report(document, g2p_results, head_tail_results, ngram_results)
        
        print("✅ 剧本加载完成")
        return document, report
        
    def _load_json(self, filepath: Path) -> Dict[str, Any]:
        """加载JSON文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ JSON文件加载成功: {len(str(data))} 字符")
            return data
        except json.JSONDecodeError as e:
            raise ScriptValidationError(f"JSON格式错误: {e}")
        except Exception as e:
            raise ScriptValidationError(f"文件读取失败: {e}")
            
    def _check_meta_field(self, data: Dict[str, Any]) -> bool:
        """检查是否有meta词条"""
        has_meta = 'meta' in data
        if has_meta:
            print("✅ 发现meta词条，使用新格式")
        else:
            print("⚠️ 未发现meta词条，检测到旧格式")
        return has_meta
        
    def _convert_legacy_format(self, data: Dict[str, Any], filepath: Path) -> Dict[str, Any]:
        """转换旧格式到新格式"""
        print("🔄 转换旧格式到新格式...")
        
        # 创建默认meta信息
        meta = {
            "title": filepath.stem,
            "author": "",
            "translator": "",
            "version": "1.0",
            "description": f"从旧格式转换: {filepath.name}",
            "language": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "license": ""
        }
        
        # 创建新格式数据
        new_data = {
            "meta": meta,
            "styles": {
                "default": {
                    "font": "Noto Sans",
                    "size": 42,
                    "color": "#FFFFFF",
                    "pos": "bottom"
                }
            },
            "cues": data.get("cues", [])
        }
        
        # 检测并添加语言信息
        languages = self._detect_languages(new_data["cues"])
        new_data["meta"]["language"] = languages
        
        print(f"✅ 格式转换完成，检测到语言: {languages}")
        return new_data
    
    def load_converted_script(self, filepath: str, validate_ngrams: bool = True) -> Tuple[SubtitleDocument, Dict[str, Any]]:
        """
        加载已转换的剧本文件（包含n-gram特征）
        
        Args:
            filepath: 文件路径
            validate_ngrams: 是否验证n-gram特征
            
        Returns:
            Tuple[SubtitleDocument, Dict]: (加载的文档, 加载报告)
        """
        file_path = Path(filepath)
        if not file_path.exists():
            raise FileNotFoundError(f"剧本文件不存在: {file_path}")
            
        print(f"🔍 开始加载转换格式剧本: {file_path.name}")
        
        # 加载JSON数据
        data = self._load_json(file_path)
        
        # 初始化报告
        report = {
            "file_path": str(file_path),
            "format_type": "converted",
            "has_ngrams": False,
            "ngram_stats": {},
            "validation_results": {},
            "loading_time": "",
            "total_cues": 0,
            "characters": [],
            "languages": []
        }
        
        start_time = datetime.now()
        
        try:
            # 检查是否是转换格式
            if 'cues' not in data:
                raise ScriptValidationError("转换格式文件必须包含'cues'字段")
            
            cues_data = data['cues']
            report["total_cues"] = len(cues_data)
            
            # 检查n-gram特征
            ngram_features = self._analyze_ngram_features(cues_data)
            report["has_ngrams"] = ngram_features["has_ngrams"]
            report["ngram_stats"] = ngram_features
            
            # 转换为Cue对象
            cues = []
            characters = set()
            languages = set()
            
            for cue_data in cues_data:
                # 创建Cue对象，支持新的n-gram字段
                cue = Cue(
                    id=cue_data.get('id', 0),
                    character=cue_data.get('character'),
                    line=cue_data.get('line', ''),
                    pure_line=cue_data.get('pure_line', ''),
                    phonemes=cue_data.get('phonemes', ''),
                    character_cue_index=cue_data.get('character_cue_index', -1),
                    translation=cue_data.get('translation', {}),
                    notes=cue_data.get('notes', ''),
                    style=cue_data.get('style', 'default'),
                    head_tok=cue_data.get('head_tok', []),
                    head_phonemes=cue_data.get('head_phonemes', []),
                    tail_tok=cue_data.get('tail_tok', []),
                    tail_phonemes=cue_data.get('tail_phonemes', []),
                    line_ngram=self._convert_to_tuples(cue_data.get('line_ngram', [])),
                    line_ngram_phonemes=self._convert_to_tuples(cue_data.get('line_ngram_phonemes', []))
                )
                
                cues.append(cue)
                
                # 收集统计信息
                if cue.character:
                    characters.add(cue.character)
                
                if cue.translation:
                    languages.update(cue.translation.keys())
            
            # 创建默认meta和styles（如果不存在）
            meta = Meta(
                title=file_path.stem,
                author="",
                language=list(languages),
                created_at=datetime.now().isoformat()
            )
            
            styles = {"default": Style()}
            
            # 创建文档
            document = SubtitleDocument(
                meta=meta,
                styles=styles,
                cues=cues
            )
            
            # 完成报告
            report["characters"] = sorted(list(characters))
            report["languages"] = sorted(list(languages))
            report["loading_time"] = str(datetime.now() - start_time)
            
            # 验证n-grams（如果需要）
            if validate_ngrams and report["has_ngrams"]:
                validation_results = self._validate_ngrams(cues)
                report["validation_results"]["ngrams"] = validation_results
            
            print(f"✅ 转换格式剧本加载成功")
            return document, report
            
        except Exception as e:
            print(f"❌ 加载失败: {e}")
            raise ScriptValidationError(f"转换格式剧本加载失败: {e}")

    def _analyze_ngram_features(self, cues_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析n-gram特征"""
        ngram_fields = ['line_ngram', 'line_ngram_phonemes']
        
        stats = {
            "has_ngrams": False,
            "total_cues_with_ngrams": 0,
            "ngram_field_counts": {},
            "average_ngrams_per_cue": 0,
            "ngram_size_distribution": {}
        }
        
        total_ngrams = 0
        cues_with_ngrams = 0
        size_counts = {}
        
        for field in ngram_fields:
            stats["ngram_field_counts"][field] = 0
        
        for cue_data in cues_data:
            cue_has_ngrams = False
            cue_ngram_count = 0
            
            for field in ngram_fields:
                if field in cue_data and cue_data[field]:
                    stats["ngram_field_counts"][field] += 1
                    cue_has_ngrams = True
                    
                    # 统计n-gram数量和大小
                    for ngram in cue_data[field]:
                        if isinstance(ngram, (list, tuple)):
                            total_ngrams += 1
                            cue_ngram_count += 1
                            size = len(ngram)
                            size_counts[size] = size_counts.get(size, 0) + 1
            
            if cue_has_ngrams:
                cues_with_ngrams += 1
        
        stats["has_ngrams"] = cues_with_ngrams > 0
        stats["total_cues_with_ngrams"] = cues_with_ngrams
        stats["average_ngrams_per_cue"] = total_ngrams / max(len(cues_data), 1)
        stats["ngram_size_distribution"] = size_counts
        
        return stats

    def _convert_to_tuples(self, ngram_list: List) -> List[tuple]:
        """
        将n-gram列表转换为tuple列表
        处理JSON反序列化时list转tuple的问题
        
        Args:
            ngram_list: n-gram列表，可能包含list或已经是tuple
            
        Returns:
            List[tuple]: 转换后的tuple列表
        """
        if not ngram_list:
            return []
        
        result = []
        for item in ngram_list:
            if isinstance(item, (list, tuple)):
                result.append(tuple(item))
            else:
                # 单个元素，包装成tuple
                result.append((item,))
        
        return result

    def _validate_ngrams(self, cues: List[Cue]) -> Dict[str, Any]:
        """验证n-gram特征的一致性"""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "total_checked": len(cues)
        }
        
        for i, cue in enumerate(cues):
            # 检查line_ngram的基本完整性
            if cue.line_ngram:
                for ngram in cue.line_ngram:
                    if isinstance(ngram, (list, tuple)):
                        # 可以在这里添加更多验证逻辑
                        if len(ngram) == 0:
                            validation["warnings"].append(
                                f"Cue {cue.id}: 发现空的line_ngram"
                            )
            
            # 检查音素n-gram的完整性
            if cue.line_ngram_phonemes:
                for ngram in cue.line_ngram_phonemes:
                    if isinstance(ngram, (list, tuple)):
                        if len(ngram) == 0:
                            validation["warnings"].append(
                                f"Cue {cue.id}: 发现空的line_ngram_phonemes"
                            )
        
        return validation

    def convert_and_load(self, input_file: str, language: str = 'fra-Latn', n: int = 2) -> Tuple[SubtitleDocument, Dict[str, Any]]:
        """
        转换并加载剧本文件
        
        Args:
            input_file: 输入文件路径
            language: 语言代码
            n: n-gram大小
            
        Returns:
            Tuple[SubtitleDocument, Dict]: (加载的文档, 加载报告)
        """
        print(f"🔄 开始转换和加载剧本: {input_file}")
        
        # 生成临时输出文件名
        input_path = Path(input_file)
        temp_output = input_path.parent / f"{input_path.stem}_converted_temp.json"
        
        try:
            # 执行转换
            if not CONVERSION_AVAILABLE or not ScriptConverter:
                raise ScriptValidationError("转换工具不可用")
                
            converter = ScriptConverter(language=language, use_fallback=True)
            success = converter.convert_script(
                input_file=str(input_path),
                output_file=str(temp_output),
                n=n,
                verbose=False  # 减少输出
            )
            
            if not success:
                raise ScriptValidationError("剧本转换失败")
            
            # 加载转换后的文件
            document, report = self.load_converted_script(str(temp_output))
            
            # 清理临时文件
            if temp_output.exists():
                temp_output.unlink()
            
            # 统一报告格式，添加缺失的file_info字段
            if "file_info" not in report:
                report["file_info"] = {
                    "title": document.meta.title,
                    "author": document.meta.author,
                    "version": document.meta.version,
                    "languages": document.meta.language,
                    "total_cues": len(document.cues),
                    "hash": getattr(document.meta, 'hash', None)
                }
            
            report["conversion_performed"] = True
            report["conversion_params"] = {"language": language, "n": n}
            
            return document, report
            
        except Exception as e:
            # 清理临时文件
            if temp_output.exists():
                temp_output.unlink()
            raise ScriptValidationError(f"转换和加载失败: {e}")

        return new_data
        
    def _detect_languages(self, cues: List[Dict]) -> List[str]:
        """检测剧本中的语言"""
        languages = set()
        
        for cue in cues:
            # 检查translation字段
            if "translation" in cue and isinstance(cue["translation"], dict):
                languages.update(cue["translation"].keys())
                
        # 添加原始语言（假设为法语，根据您的剧本内容）
        if any("character" in cue and cue.get("line", "") for cue in cues):
            languages.add("fr")  # 法语
            
        return sorted(list(languages))
        
    def _validate_and_create_document(self, data: Dict[str, Any]) -> SubtitleDocument:
        """验证数据格式并创建文档对象"""
        errors = []
        
        try:
            # 验证meta字段
            meta_data = data.get("meta", {})
            meta = Meta(**meta_data) if meta_data else Meta()
            
            # 验证styles字段
            styles_data = data.get("styles", {"default": {}})
            styles = {}
            for name, style_data in styles_data.items():
                try:
                    styles[name] = Style(**style_data)
                except Exception as e:
                    errors.append(f"样式 '{name}' 格式错误: {e}")
                    styles[name] = Style()  # 使用默认样式
                    
            # 验证cues字段
            cues_data = data.get("cues", [])
            cues = []
            
            for i, cue_data in enumerate(cues_data):
                try:
                    # 处理可能缺失的字段
                    cue_dict = self._normalize_cue_data(cue_data, i)
                    cue = Cue(**cue_dict)
                    cues.append(cue)
                except Exception as e:
                    errors.append(f"台词 {i+1} 格式错误: {e}")
                    # 创建一个最小的有效cue
                    cues.append(Cue(
                        id=i+1,
                        character=cue_data.get("character"),
                        line=cue_data.get("line", ""),
                        phonemes="",
                        notes=f"格式错误: {e}"
                    ))
                    
            if errors:
                print(f"⚠️ 发现 {len(errors)} 个格式问题：")
                for error in errors[:5]:  # 只显示前5个错误
                    print(f"   - {error}")
                if len(errors) > 5:
                    print(f"   ... 还有 {len(errors)-5} 个错误")
                    
            document = SubtitleDocument(meta=meta, styles=styles, cues=cues)
            print(f"✅ 文档创建成功: {len(cues)} 条台词")
            
            self.validation_results = {
                "total_cues": len(cues),
                "valid_cues": len([c for c in cues if c.line]),
                "errors": errors,
                "has_meta": True,
                "languages": document.get_all_languages()
            }
            
            return document
            
        except Exception as e:
            raise ScriptValidationError(f"文档创建失败: {e}")
            
    def _normalize_cue_data(self, cue_data: Dict[str, Any], index: int) -> Dict[str, Any]:
        """标准化cue数据，补充缺失字段"""
        # 生成pure_line（如果原数据中没有）
        line = cue_data.get("line", "")
        pure_line = cue_data.get("pure_line", "")
        if not pure_line and line:
            # 如果没有pure_line，从line生成一个清理版本
            pure_line = self._clean_text_for_ngram(line)
        
        normalized = {
            "id": cue_data.get("id", index + 1),
            "character": cue_data.get("character"),
            "line": line,
            "pure_line": pure_line,
            "phonemes": cue_data.get("phonemes", ""),
            "character_cue_index": cue_data.get("character_cue_index", -1),
            "translation": cue_data.get("translation", {}),
            "notes": cue_data.get("notes", ""),
            "style": cue_data.get("style", "default"),
            # 新增头尾字段
            "head_tok": cue_data.get("head_tok", []),
            "head_phonemes": cue_data.get("head_phonemes", []),
            "tail_tok": cue_data.get("tail_tok", []),
            "tail_phonemes": cue_data.get("tail_phonemes", []),
            # 新增整句n-gram字段（进行类型转换）
            "line_ngram": self._convert_to_tuples(cue_data.get("line_ngram", [])),
            "line_ngram_phonemes": self._convert_to_tuples(cue_data.get("line_ngram_phonemes", []))
        }
        
        # 确保translation是字典
        if not isinstance(normalized["translation"], dict):
            normalized["translation"] = {}
        
        # 确保头尾字段是列表
        for field in ["head_tok", "head_phonemes", "tail_tok", "tail_phonemes"]:
            if not isinstance(normalized[field], list):
                normalized[field] = []
        
        # ngram字段已经在上面处理了类型转换
            
        return normalized
        
    def _process_phonemes(self, document: SubtitleDocument) -> Dict[str, Any]:
        """处理音素数据"""
        if not self.g2p_converter:
            print("⚠️ 未提供G2P转换器，跳过音素处理")
            return {"processed": 0, "skipped": len(document.cues), "errors": []}
            
        processed = 0
        skipped = 0
        errors = []
        
        # 收集需要G2P处理的台词
        lines_to_process = []
        indices_to_process = []
        
        for i, cue in enumerate(document.cues):
            if not cue.line.strip():  # 空台词
                skipped += 1
                continue
                
            if not cue.phonemes or not cue.phonemes.strip():  # 没有音素
                # 优先使用pure_line，如果没有则使用清理后的line
                text_for_g2p = cue.pure_line if cue.pure_line else self._clean_text_for_ngram(cue.line)
                if text_for_g2p.strip():
                    lines_to_process.append(text_for_g2p)
                    indices_to_process.append(i)
                else:
                    skipped += 1
            else:
                print(f"   跳过已有音素的台词 {cue.id}: '{cue.line[:30]}...'")
                skipped += 1
                
        if lines_to_process:
            print(f"🔄 对 {len(lines_to_process)} 条台词进行G2P转换...")
            
            try:
                # 批量G2P转换
                phonemes_results = self.g2p_converter.batch_convert(lines_to_process)
                
                # 更新cue对象的音素
                for idx, phonemes in zip(indices_to_process, phonemes_results):
                    document.cues[idx].phonemes = phonemes
                    processed += 1
                    if processed <= 3:  # 显示前3个转换结果
                        cue = document.cues[idx]
                        print(f"   ✅ {cue.id}: '{cue.line[:20]}...' -> '{phonemes[:30]}...'")
                        
                if processed > 3:
                    print(f"   ... 还有 {processed-3} 条台词完成转换")
                    
            except Exception as e:
                error_msg = f"G2P批量转换失败: {e}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
        else:
            print("✅ 所有台词都已有音素数据")
            
        return {
            "processed": processed,
            "skipped": skipped,
            "errors": errors,
            "total": len(document.cues)
        }
    
    def _calculate_file_hash(self, filepath: Path) -> str:
        """计算文件哈希值"""
        hasher = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    def _load_from_cache(self, file_hash: str) -> Optional[SubtitleDocument]:
        """从缓存加载文档"""
        cache_file = self.cache_dir / f"{file_hash}.cache"
        if not cache_file.exists():
            return None
            
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
                
            # 验证缓存版本兼容性
            if cached_data.get('version') != '1.0':
                print("⚠️ 缓存版本不兼容，重新加载")
                return None
                
            document = cached_data.get('document')
            if isinstance(document, SubtitleDocument):
                return document
                
        except Exception as e:
            print(f"⚠️ 缓存加载失败: {e}")
            
        return None
    
    def _save_to_cache(self, document: SubtitleDocument, file_hash: str):
        """保存文档到缓存"""
        try:
            cache_file = self.cache_dir / f"{file_hash}.cache"
            cache_data = {
                'version': '1.0',
                'document': document,
                'cached_at': datetime.now().isoformat()
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
                
            print(f"✅ 已保存到缓存: {cache_file.name}")
            
        except Exception as e:
            print(f"⚠️ 缓存保存失败: {e}")
    
    def _generate_cache_report(self, document: SubtitleDocument) -> Dict[str, Any]:
        """生成缓存加载报告"""
        return {
            "file_info": {
                "title": document.meta.title,
                "author": document.meta.author,
                "version": document.meta.version,
                "languages": document.meta.language,
                "total_cues": len(document.cues),
                "hash": document.meta.hash
            },
            "validation": {"from_cache": True},
            "g2p_processing": {"from_cache": True},
            "head_tail_processing": {"from_cache": True},
            "summary": {
                "valid_cues": len([c for c in document.cues if c.line.strip()]),
                "empty_cues": len([c for c in document.cues if not c.line.strip()]),
                "cues_with_phonemes": len([c for c in document.cues if c.phonemes and c.phonemes.strip()]),
                "cues_with_head_tail": len([c for c in document.cues if c.head_tok or c.tail_tok]),
                "cues_with_line_ngrams": len([c for c in document.cues if c.line_ngram]),
                "characters": len(set(c.character for c in document.cues if c.character)),
                "available_languages": getattr(document, 'get_all_languages', lambda: [])()
            }
        }
    
    def _process_head_tail_tokens(self, document: SubtitleDocument) -> Dict[str, Any]:
        """处理头部和尾部词语提取和G2P转换"""
        if not self.g2p_converter:
            print("⚠️ 未提供G2P转换器，跳过头尾词语处理")
            return {"processed": 0, "skipped": len(document.cues), "errors": []}
        
        processed = 0
        skipped = 0
        errors = []
        
        for cue in document.cues:
            if not cue.line.strip():  # 空台词
                skipped += 1
                continue
                
            try:
                # 提取头部和尾部词语，优先使用pure_line
                text_to_process = cue.pure_line if cue.pure_line else cue.line
                head_tokens, tail_tokens = self._extract_head_tail_tokens(text_to_process)
                
                # 对词语进行G2P转换
                if head_tokens:
                    head_phonemes = self.g2p_converter.batch_convert(head_tokens)
                    cue.head_tok = head_tokens
                    cue.head_phonemes = head_phonemes
                    
                if tail_tokens:
                    tail_phonemes = self.g2p_converter.batch_convert(tail_tokens)
                    cue.tail_tok = tail_tokens
                    cue.tail_phonemes = tail_phonemes
                
                processed += 1
                
            except Exception as e:
                error_msg = f"处理台词 {cue.id} 头尾词语失败: {e}"
                errors.append(error_msg)
                print(f"⚠️ {error_msg}")
                
        print(f"✅ 头尾词语处理完成: {processed} 条成功, {skipped} 条跳过")
        
        return {
            "processed": processed,
            "skipped": skipped,
            "errors": errors,
            "total": len(document.cues)
        }
    
    def _process_line_ngrams(self, document: SubtitleDocument, n: int = 2) -> Dict[str, Any]:
        """处理整句n-gram生成和音素转换"""
        if not self.g2p_converter:
            print("⚠️ 未提供G2P转换器，跳过整句n-gram处理")
            return {"processed": 0, "skipped": len(document.cues), "errors": []}
        
        processed = 0
        skipped = 0
        errors = []
        
        for cue in document.cues:
            if not cue.line.strip():  # 空台词
                skipped += 1
                continue
                
            try:
                # 使用pure_line生成n-gram，如果没有pure_line则清理原line
                text_to_process = cue.pure_line if cue.pure_line else self._clean_text_for_ngram(cue.line)
                
                # 生成单词级n-gram
                tokens = self._tokenize_for_ngram(text_to_process)
                if tokens:
                    line_ngrams = self._create_ngrams(tokens, n)
                    cue.line_ngram = line_ngrams
                    
                    # 对每个n-gram中的token进行G2P转换，然后生成音素n-gram
                    phoneme_ngrams = []
                    for ngram in line_ngrams:
                        # 将ngram中的每个token转换为音素
                        phoneme_tokens = []
                        for token in ngram:
                            phoneme = self.g2p_converter.convert(token)
                            if phoneme:
                                phoneme_tokens.append(phoneme)
                        
                        if phoneme_tokens:
                            phoneme_ngrams.append(tuple(phoneme_tokens))
                    
                    cue.line_ngram_phonemes = phoneme_ngrams
                
                processed += 1
                
            except Exception as e:
                error_msg = f"处理台词 {cue.id} 整句n-gram失败: {e}"
                errors.append(error_msg)
                print(f"⚠️ {error_msg}")
                
        print(f"✅ 整句n-gram处理完成: {processed} 条成功, {skipped} 条跳过")
        
        return {
            "processed": processed,
            "skipped": skipped,
            "errors": errors,
            "total": len(document.cues)
        }
    
    def _clean_text_for_ngram(self, text: str) -> str:
        """清理文本用于n-gram生成"""
        import re
        # 移除标点符号（包括"-"），保留字母、数字、中文字符和空格
        cleaned = re.sub(r'[^\w\s]', ' ', text)
        # 移除多余空格
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def _tokenize_for_ngram(self, text: str) -> List[str]:
        """将文本分词用于n-gram生成"""
        if not text:
            return []
        return [token.strip() for token in text.split() if token.strip()]
    
    def _create_ngrams(self, tokens: List[str], n: int = 2) -> List[tuple]:
        """创建n-gram列表"""
        if len(tokens) < n:
            return []
        
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = tuple(tokens[i:i + n])
            ngrams.append(ngram)
        
        return ngrams
    
    def _extract_head_tail_tokens(self, line: str) -> Tuple[List[str], List[str]]:
        """
        从台词中提取头部和尾部的N个词语
        
        Args:
            line: 台词文本
            
        Returns:
            Tuple[List[str], List[str]]: (头部词语列表, 尾部词语列表)
        """
        # 简单的词语分割（可以根据需要使用更复杂的分词器）
        # 移除标点符号并分割
        import re
        
        # 移除标点符号（包括"-"），保留字母、数字、中文字符和空格
        cleaned_line = re.sub(r'[^\w\s]', ' ', line)
        tokens = [token.strip() for token in cleaned_line.split() if token.strip()]
        
        if not tokens:
            return [], []
            
        # 提取头部词语
        head_count = min(self.head_tail_count, len(tokens))
        head_tokens = tokens[:head_count]
        
        # 提取尾部词语（避免与头部重复）
        if len(tokens) <= self.head_tail_count:
            # 如果总词语数不超过N，尾部就是剩余的部分
            tail_tokens = tokens[head_count:] if head_count < len(tokens) else []
        else:
            # 如果总词语数超过N，取最后N个
            tail_tokens = tokens[-self.head_tail_count:]
            
        return head_tokens, tail_tokens
        
    def _generate_load_report(self, document: SubtitleDocument, g2p_results: Dict[str, Any], head_tail_results: Optional[Dict[str, Any]] = None, ngram_results: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """生成加载报告"""
        report = {
            "file_info": {
                "title": document.meta.title,
                "author": document.meta.author,
                "version": document.meta.version,
                "languages": document.meta.language,
                "total_cues": len(document.cues),
                "hash": document.meta.hash
            },
            "validation": self.validation_results,
            "g2p_processing": g2p_results,
            "head_tail_processing": head_tail_results or {},
            "ngram_processing": ngram_results or {},
            "summary": {
                "valid_cues": len([c for c in document.cues if c.line.strip()]),
                "empty_cues": len([c for c in document.cues if not c.line.strip()]),
                "cues_with_phonemes": len([c for c in document.cues if c.phonemes and c.phonemes.strip()]),
                "cues_with_head_tail": len([c for c in document.cues if c.head_tok or c.tail_tok]),
                "cues_with_line_ngrams": len([c for c in document.cues if c.line_ngram]),
                "characters": len(set(c.character for c in document.cues if c.character)),
                "available_languages": getattr(document, 'get_all_languages', lambda: [])()
            }
        }
        
        return report
        
    def print_load_report(self, report: Dict[str, Any]):
        """打印加载报告"""
        print("\n" + "="*60)
        print("📋 剧本加载报告")
        print("="*60)
        
        # 文件信息
        file_info = report["file_info"]
        print(f"📝 标题: {file_info['title']}")
        print(f"👤 作者: {file_info['author'] or '未知'}")
        print(f"📅 版本: {file_info['version']}")
        print(f"🌍 语言: {', '.join(file_info['languages']) if file_info['languages'] else '未指定'}")
        if file_info.get('hash'):
            print(f"🔍 文件哈希: {file_info['hash'][:16]}...")
        
        # 统计信息
        summary = report["summary"]
        print(f"\n📊 统计信息:")
        print(f"   总台词数: {file_info['total_cues']}")
        print(f"   有效台词: {summary['valid_cues']}")
        print(f"   空台词: {summary['empty_cues']}")
        print(f"   已有音素: {summary['cues_with_phonemes']}")
        print(f"   已处理头尾: {summary.get('cues_with_head_tail', 0)}")
        print(f"   已生成n-gram: {summary.get('cues_with_line_ngrams', 0)}")
        print(f"   角色数量: {summary['characters']}")
        print(f"   可用语言: {', '.join(summary['available_languages']) if summary['available_languages'] else '无'}")
        
        # G2P处理结果
        g2p = report["g2p_processing"]
        if isinstance(g2p, dict) and not g2p.get("from_cache", False):
            if g2p.get("processed", 0) > 0 or g2p.get("errors"):
                print(f"\n🔤 G2P处理结果:")
                print(f"   已处理: {g2p.get('processed', 0)}")
                print(f"   已跳过: {g2p.get('skipped', 0)}")
                if g2p.get("errors"):
                    print(f"   错误: {len(g2p['errors'])}")
                    for error in g2p["errors"][:3]:
                        print(f"     - {error}")
        
        # 头尾词语处理结果
        head_tail = report.get("head_tail_processing", {})
        if isinstance(head_tail, dict) and not head_tail.get("from_cache", False):
            if head_tail.get("processed", 0) > 0 or head_tail.get("errors"):
                print(f"\n🎯 头尾词语处理结果:")
                print(f"   已处理: {head_tail.get('processed', 0)}")
                print(f"   已跳过: {head_tail.get('skipped', 0)}")
                if head_tail.get("errors"):
                    print(f"   错误: {len(head_tail['errors'])}")
                    for error in head_tail["errors"][:3]:
                        print(f"     - {error}")
        
        # n-gram处理结果
        ngram = report.get("ngram_processing", {})
        if isinstance(ngram, dict) and not ngram.get("from_cache", False):
            if ngram.get("processed", 0) > 0 or ngram.get("errors"):
                print(f"\n🔗 n-gram生成结果:")
                print(f"   已处理: {ngram.get('processed', 0)}")
                print(f"   已跳过: {ngram.get('skipped', 0)}")
                if ngram.get("errors"):
                    print(f"   错误: {len(ngram['errors'])}")
                    for error in ngram["errors"][:3]:
                        print(f"     - {error}")
                        
        # 验证问题
        validation = report["validation"]
        if isinstance(validation, dict) and not validation.get("from_cache", False):
            if validation.get("errors"):
                print(f"\n⚠️ 验证问题: {len(validation['errors'])}")
                for error in validation["errors"][:3]:
                    print(f"   - {error}")
        
        # 缓存信息
        if any(result.get("from_cache", False) for result in [g2p, head_tail, validation]):
            print(f"\n💾 从缓存加载")
                
        print("="*60)


def demo_enhanced_loader():
    """演示增强版加载器"""
    print("🧪 演示增强版剧本加载器\n")
    
    # 假设有G2P转换器
    from app.core.g2p.g2p_manager import G2PManager
    
    try:
        g2p_manager = G2PManager()
        g2p_converter = g2p_manager.get_current_engine()
    except:
        g2p_converter = None
        print("⚠️ G2P转换器不可用，将跳过音素处理")
        
    loader = EnhancedScriptLoader(g2p_converter)
    
    # 测试文件路径
    test_file = "scripts/final_script.json"
    
    try:
        document, report = loader.load_script(test_file)
        loader.print_load_report(report)
        
        # 显示前几条台词
        print(f"\n📝 前3条台词预览:")
        for i, cue in enumerate(document.cues[:3]):
            if cue.line.strip():
                print(f"   {cue.id}. {cue.character or '(舞台提示)'}: {cue.line}")
                if cue.phonemes:
                    print(f"      音素: {cue.phonemes[:50]}...")
                    
    except Exception as e:
        print(f"❌ 加载失败: {e}")


if __name__ == "__main__":
    demo_enhanced_loader()
