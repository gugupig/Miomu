#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试转换后的剧本文件是否可以被Miomu系统正确加载
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.data.script_data import ScriptData


def test_script_loading(script_file: str):
    """测试剧本文件加载"""
    print(f"🎭 测试剧本文件加载: {script_file}")
    print("=" * 50)
    
    try:
        # 1. 测试JSON格式是否正确
        print("📄 1. 验证JSON格式...")
        with open(script_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print("✅ JSON格式正确")
        
        # 2. 测试数据结构
        print("📋 2. 验证数据结构...")
        if "meta" not in data:
            print("❌ 缺少meta字段")
            return False
        if "cues" not in data:
            print("❌ 缺少cues字段")
            return False
        print("✅ 数据结构正确")
        
        # 3. 测试基本字段
        print("🔍 3. 验证必需字段...")
        cues = data["cues"]
        required_fields = ["id", "character", "line"]
        
        for i, cue in enumerate(cues[:5]):  # 检查前5条
            for field in required_fields:
                if field not in cue:
                    print(f"❌ 第{i+1}条台词缺少字段: {field}")
                    return False
        print("✅ 必需字段完整")
        
        # 4. 测试使用ScriptData加载
        print("🚀 4. 使用ScriptData类加载...")
        script_data = ScriptData()
        
        # 手动加载（模拟load_from_file方法）
        script_data.filepath = script_file
        script_data.cues = []
        
        from app.models.models import Cue
        
        for raw_cue in cues:
            try:
                cue = Cue(
                    id=int(raw_cue["id"]),
                    character=raw_cue.get("character"),
                    line=raw_cue["line"],
                    phonemes=raw_cue.get("phonemes", ""),
                    character_cue_index=raw_cue.get("character_cue_index", -1),
                    translation=raw_cue.get("translation", {}),
                    notes=raw_cue.get("notes", ""),
                    style=raw_cue.get("style", "default")
                )
                script_data.cues.append(cue)
            except Exception as e:
                print(f"❌ 创建Cue对象失败 (ID {raw_cue.get('id', '?')}): {e}")
                return False
        
        print("✅ ScriptData加载成功")
        
        # 5. 显示统计信息
        print(f"\n📊 剧本统计:")
        print(f"   📝 总台词数: {len(script_data.cues)}")
        
        # 统计角色
        characters = {}
        for cue in script_data.cues:
            if cue.character:
                characters[cue.character] = characters.get(cue.character, 0) + 1
        
        print(f"   🎭 角色数量: {len(characters)}")
        print(f"   🎬 角色分布:")
        for char, count in sorted(characters.items(), key=lambda x: -x[1])[:10]:
            print(f"      • {char}: {count} 句")
        
        # 统计舞台指示
        notes_count = sum(1 for cue in script_data.cues if cue.notes)
        print(f"   📝 舞台指示: {notes_count} 条")
        
        # 显示前几条台词
        print(f"\n🎭 前5条台词预览:")
        for i, cue in enumerate(script_data.cues[:5]):
            notes_info = f" ({cue.notes})" if cue.notes else ""
            print(f"   {i+1}. [{cue.character}] {cue.line}{notes_info}")
        
        print(f"\n🎉 剧本文件测试通过！可以正常加载到Miomu系统中。")
        return True
        
    except FileNotFoundError:
        print(f"❌ 文件不存在: {script_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ JSON格式错误: {e}")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 测试转换后的剧本文件
    script_files = [
        "scripts/final_script.json",
        "scripts/script_dialogues_converted.json"
    ]
    
    for script_file in script_files:
        script_path = Path(script_file)
        if script_path.exists():
            print()
            success = test_script_loading(str(script_path))
            if not success:
                print(f"💥 {script_file} 测试失败")
            print("-" * 80)
        else:
            print(f"⚠️ 文件不存在: {script_file}")
    
    print("\n✨ 测试完成！")
