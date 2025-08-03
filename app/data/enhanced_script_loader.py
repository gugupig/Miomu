#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版剧本加载器
支持meta词条检验、dataclass格式校验、音素检验等功能
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import asdict, is_dataclass
from datetime import datetime

from app.models.models import Meta, Style, Cue, SubtitleDocument
from app.core.g2p.base import G2PConverter


class ScriptValidationError(Exception):
    """剧本验证错误"""
    pass


class EnhancedScriptLoader:
    """增强版剧本加载器"""
    
    def __init__(self, g2p_converter: Optional[G2PConverter] = None):
        self.g2p_converter = g2p_converter
        self.validation_results = {}
        self.conversion_results = {}
        
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
        
        # 1. 加载JSON数据
        raw_data = self._load_json(file_path)
        
        # 2. 检查是否有meta词条
        has_meta = self._check_meta_field(raw_data)
        
        if not has_meta:
            print("⚠️ 未发现meta词条，调用转换脚本...")
            raw_data = self._convert_legacy_format(raw_data, file_path)
            
        # 3. 进行dataclass格式校验
        print("🔍 进行dataclass格式校验...")
        document = self._validate_and_create_document(raw_data)
        
        # 4. 检查音素并进行G2P处理
        print("🔍 检查音素数据...")
        g2p_results = self._process_phonemes(document)
        
        # 5. 生成加载报告
        report = self._generate_load_report(document, g2p_results)
        
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
        normalized = {
            "id": cue_data.get("id", index + 1),
            "character": cue_data.get("character"),
            "line": cue_data.get("line", ""),
            "phonemes": cue_data.get("phonemes", ""),
            "character_cue_index": cue_data.get("character_cue_index", -1),
            "translation": cue_data.get("translation", {}),
            "notes": cue_data.get("notes", ""),
            "style": cue_data.get("style", "default")
        }
        
        # 确保translation是字典
        if not isinstance(normalized["translation"], dict):
            normalized["translation"] = {}
            
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
                lines_to_process.append(cue.line)
                indices_to_process.append(i)
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
        
    def _generate_load_report(self, document: SubtitleDocument, g2p_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成加载报告"""
        report = {
            "file_info": {
                "title": document.meta.title,
                "author": document.meta.author,
                "version": document.meta.version,
                "languages": document.meta.language,
                "total_cues": len(document.cues)
            },
            "validation": self.validation_results,
            "g2p_processing": g2p_results,
            "summary": {
                "valid_cues": len([c for c in document.cues if c.line.strip()]),
                "empty_cues": len([c for c in document.cues if not c.line.strip()]),
                "cues_with_phonemes": len([c for c in document.cues if c.phonemes and c.phonemes.strip()]),
                "characters": len(set(c.character for c in document.cues if c.character)),
                "available_languages": document.get_all_languages()
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
        
        # 统计信息
        summary = report["summary"]
        print(f"\n📊 统计信息:")
        print(f"   总台词数: {file_info['total_cues']}")
        print(f"   有效台词: {summary['valid_cues']}")
        print(f"   空台词: {summary['empty_cues']}")
        print(f"   已有音素: {summary['cues_with_phonemes']}")
        print(f"   角色数量: {summary['characters']}")
        print(f"   可用语言: {', '.join(summary['available_languages']) if summary['available_languages'] else '无'}")
        
        # G2P处理结果
        g2p = report["g2p_processing"]
        if g2p["processed"] > 0 or g2p["errors"]:
            print(f"\n🔤 G2P处理结果:")
            print(f"   已处理: {g2p['processed']}")
            print(f"   已跳过: {g2p['skipped']}")
            if g2p["errors"]:
                print(f"   错误: {len(g2p['errors'])}")
                for error in g2p["errors"][:3]:
                    print(f"     - {error}")
                    
        # 验证问题
        validation = report["validation"]
        if validation.get("errors"):
            print(f"\n⚠️ 验证问题: {len(validation['errors'])}")
            for error in validation["errors"][:3]:
                print(f"   - {error}")
                
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
