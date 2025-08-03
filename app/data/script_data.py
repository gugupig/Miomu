from typing import List, Dict, Any, Optional, Tuple
from PySide6.QtCore import QObject # 继承QObject以便未来增加信号
from app.models.models import Cue, SubtitleDocument
from app.core.g2p.base import G2PConverter

class ScriptData(QObject):
    """
    剧本数据的管理中心。
    负责加载、解析、预处理和存储所有Cue对象。
    现在使用增强版加载器支持meta词条检验、格式校验等功能。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cues: List[Cue] = []
        self.filepath: str = ""
        self.document: Optional[SubtitleDocument] = None
        self.load_report: Dict[str, Any] = {}

    def load_from_file(self, filepath: str, g2p_converter: G2PConverter) -> bool:
        """
        使用增强版加载器从JSON文件加载剧本
        支持meta词条检验、dataclass格式校验、音素检验等功能
        """
        try:
            from app.data.enhanced_script_loader import EnhancedScriptLoader
            
            print(f"🔍 使用增强版加载器加载剧本: {filepath}")
            
            # 创建增强版加载器
            loader = EnhancedScriptLoader(g2p_converter)
            
            # 加载剧本
            document, report = loader.load_script(filepath)
            
            # 更新本地数据
            self.document = document
            self.cues = document.cues
            self.filepath = filepath
            self.load_report = report
            
            # 打印加载报告
            loader.print_load_report(report)
            
            print(f"✅ 成功加载剧本: {len(self.cues)} 条台词")
            return True
            
        except Exception as e:
            print(f"❌ 增强版加载失败，回退到基础加载器: {e}")
            return self._load_from_file_basic(filepath, g2p_converter)
    
    def _load_from_file_basic(self, filepath: str, g2p_converter: G2PConverter) -> bool:
        """
        基础加载器（保持向后兼容）
        """
        import json
        self.filepath = filepath
        print(f"[*] Loading script from: {self.filepath}")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                raw_cues = json.load(f).get("cues", [])
        except Exception as e:
            print(f"⚠️ Error loading or parsing JSON file: {e}")
            self.cues = []
            return False

        # --- G2P 预处理 ---
        all_lines = [r.get("line", "") for r in raw_cues]
        
        print(f"[*] Pre-processing script with '{type(g2p_converter).__name__}'...")
        all_phonemes = g2p_converter.batch_convert(all_lines)
        print("[*] Script pre-processing complete.")

        # --- 创建Cue对象列表 ---
        self.cues = []
        for r, phoneme_str in zip(raw_cues, all_phonemes):
            try:
                self.cues.append(Cue(
                    id=int(r["id"]),
                    character=r.get("character"),
                    line=r["line"],
                    phonemes=phoneme_str,
                    character_cue_index=r.get("character_cue_index", -1),
                    translation=r.get("translation", {}),
                    notes=r.get("notes", ""),
                    style=r.get("style", "default")
                ))
            except KeyError as e:
                print(f"⚠️ Field missing {e} in record: {r}")
        
        print(f"[*] Successfully loaded and processed {len(self.cues)} cues.")
        return True
        
    def save_to_file(self, filepath: str | None = None) -> bool:
        """
        保存剧本数据到JSON文件
        保存完整的增强格式JSON，包括meta信息和所有数据
        """
        import json
        from datetime import datetime
        
        target_path = filepath or self.filepath
        
        if not target_path:
            raise ValueError("没有指定保存路径")
            
        try:
            # 如果有document对象（增强版加载的），保存完整数据
            if hasattr(self, 'document') and self.document:
                # 使用增强版格式保存
                return self._save_enhanced_format(target_path)
            else:
                # 使用传统格式保存
                return self._save_legacy_format(target_path)
                
        except Exception as e:
            print(f"⚠️ Error saving script: {e}")
            return False
    
    def _save_enhanced_format(self, target_path: str) -> bool:
        """保存增强版格式（包含meta信息）"""
        import json
        from datetime import datetime
        
        # 构建完整的增强格式数据
        save_data = {}
        
        # 添加meta信息
        if self.document and self.document.meta:
            meta = self.document.meta
            save_data["meta"] = {
                "title": meta.title,
                "author": meta.author,
                "translator": meta.translator,
                "version": meta.version,
                "description": meta.description,
                "language": meta.language,
                "created_at": meta.created_at,
                "updated_at": datetime.now().isoformat(),  # 更新保存时间
                "license": meta.license
            }
        
        # 添加样式信息（如果存在）- 转换为字典格式
        if self.document and hasattr(self.document, 'styles'):
            styles = getattr(self.document, 'styles', {})
            if styles:
                # 确保styles是可序列化的字典格式
                save_data["styles"] = self._serialize_styles(styles)
        
        # 添加台词数据
        cues_data = []
        for cue in self.cues:
            cue_data = {
                "id": cue.id,
                "character": cue.character,
                "line": cue.line,
                "phonemes": getattr(cue, 'phonemes', ""),
                "character_cue_index": getattr(cue, 'character_cue_index', -1),
                "translation": getattr(cue, 'translation', {}),
                "notes": getattr(cue, 'notes', ""),
                "style": getattr(cue, 'style', "default")
            }
            cues_data.append(cue_data)
        
        save_data["cues"] = cues_data
        
        # 保存到文件
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
            
        print(f"[*] Enhanced script saved to: {target_path}")
        self.filepath = target_path
        return True
    
    def _serialize_styles(self, styles) -> dict:
        """将样式对象转换为可序列化的字典"""
        if isinstance(styles, dict):
            # 如果已经是字典，检查是否需要序列化内部对象
            serialized = {}
            for key, style in styles.items():
                if hasattr(style, '__dict__'):
                    # 如果是dataclass或对象，转换为字典
                    serialized[key] = {
                        'font': getattr(style, 'font', 'Noto Sans'),
                        'size': getattr(style, 'size', 42),
                        'color': getattr(style, 'color', '#FFFFFF'),
                        'pos': getattr(style, 'pos', 'bottom')
                    }
                else:
                    # 如果已经是字典，直接使用
                    serialized[key] = style
            return serialized
        else:
            # 如果不是字典，返回空字典
            return {}
    
    def _save_legacy_format(self, target_path: str) -> bool:
        """保存传统格式（仅cues）"""
        import json
        
        # 转换为JSON格式
        cues_data = []
        for cue in self.cues:
            cue_data = {
                "id": cue.id,
                "character": cue.character,
                "line": cue.line
            }
            
            # 添加新字段（如果存在且非默认值）
            if hasattr(cue, 'phonemes') and cue.phonemes:
                cue_data["phonemes"] = cue.phonemes
                
            if hasattr(cue, 'character_cue_index') and cue.character_cue_index != -1:
                cue_data["character_cue_index"] = cue.character_cue_index
                
            if hasattr(cue, 'translation') and cue.translation:
                cue_data["translation"] = cue.translation
                
            if hasattr(cue, 'notes') and cue.notes:
                cue_data["notes"] = cue.notes
                
            if hasattr(cue, 'style') and cue.style != "default":
                cue_data["style"] = cue.style
            
            cues_data.append(cue_data)
            
        script_json = {"cues": cues_data}
        
        # 保存到文件
        with open(target_path, 'w', encoding='utf-8') as f:
            json.dump(script_json, f, ensure_ascii=False, indent=2)
            
        print(f"[*] Legacy script saved to: {target_path}")
        self.filepath = target_path
        return True