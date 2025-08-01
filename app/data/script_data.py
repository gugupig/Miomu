from typing import List
from PySide6.QtCore import QObject # 继承QObject以便未来增加信号
from app.models.models import Cue
from app.core.g2p.base import G2PConverter

class ScriptData(QObject):
    """
    剧本数据的管理中心。
    负责加载、解析、预处理和存储所有Cue对象。
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cues: List[Cue] = []
        self.filepath: str = ""

    def load_from_file(self, filepath: str, g2p_converter: G2PConverter) -> bool:
        """
        从JSON文件加载剧本，并执行G2P预处理。
        这是之前Player中的_load_cues逻辑。
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
                    character=r["character"],
                    line=r["line"],
                    phonemes=phoneme_str
                ))
            except KeyError as e:
                print(f"⚠️ Field missing {e} in record: {r}")
        
        print(f"[*] Successfully loaded and processed {len(self.cues)} cues.")
        return True
        
    def save_to_file(self, filepath: str | None = None) -> bool:
        """
        保存剧本数据到JSON文件
        """
        import json
        target_path = filepath or self.filepath
        
        if not target_path:
            raise ValueError("没有指定保存路径")
            
        try:
            # 转换为JSON格式
            cues_data = []
            for cue in self.cues:
                cue_data = {
                    "id": cue.id,
                    "character": cue.character,
                    "line": cue.line
                }
                
                # 添加新字段（如果存在且非默认值）
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
                
            print(f"[*] Script saved to: {target_path}")
            self.filepath = target_path
            return True
            
        except Exception as e:
            print(f"⚠️ Error saving script: {e}")
            return False