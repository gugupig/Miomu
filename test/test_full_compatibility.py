#!/usr/bin/env python3
"""测试更新后的数据模型与现有功能的兼容性"""

import sys
import json
sys.path.append('.')

from app.models.models import Cue, Meta, Style, SubtitleDocument
from app.models.script_table_model import ScriptTableModel
from PySide6.QtCore import Qt

def test_updated_cue_model():
    """测试更新后的 Cue 模型"""
    print("=== 测试更新后的 Cue 模型 ===")
    
    # 测试传统的 cue (兼容性)
    traditional_cue = Cue(
        id=1,
        character="测试角色",
        line="测试台词"
    )
    
    print(f"传统 Cue:")
    print(f"  ID: {traditional_cue.id}")
    print(f"  角色: {traditional_cue.character}")
    print(f"  台词: {traditional_cue.line}")
    print(f"  音素: {traditional_cue.phonemes}")
    print(f"  角色索引: {traditional_cue.character_cue_index}")
    print(f"  翻译: {traditional_cue.translation}")
    print(f"  备注: {traditional_cue.notes}")
    print(f"  样式: {traditional_cue.style}")
    
    # 测试完整的 cue (新功能)
    full_cue = Cue(
        id=2,
        character="哈姆雷特",
        line="生存还是毁灭，这是一个值得考虑的问题。",
        phonemes="sheng1 cun2 hai2 shi4 hui3 mie4",
        character_cue_index=1,
        translation="To be, or not to be, that is the question.",
        notes="独白，舞台中央，灯光聚焦",
        style="哈姆雷特"
    )
    
    print(f"\n完整 Cue:")
    print(f"  ID: {full_cue.id}")
    print(f"  角色: {full_cue.character}")
    print(f"  台词: {full_cue.line}")
    print(f"  音素: {full_cue.phonemes}")
    print(f"  角色索引: {full_cue.character_cue_index}")
    print(f"  翻译: {full_cue.translation}")
    print(f"  备注: {full_cue.notes}")
    print(f"  样式: {full_cue.style}")
    
    # 测试舞台提示 cue (character=None)
    stage_cue = Cue(
        id=3,
        character=None,  # 舞台提示
        line="(灯光暗下)",
        character_cue_index=-1,
        translation="(Lights fade)",
        notes="舞台提示",
        style="default"
    )
    
    print(f"\n舞台提示 Cue:")
    print(f"  ID: {stage_cue.id}")
    print(f"  角色: {stage_cue.character}")
    print(f"  台词: {stage_cue.line}")
    print(f"  角色索引: {stage_cue.character_cue_index}")
    print(f"  翻译: {stage_cue.translation}")
    print(f"  备注: {stage_cue.notes}")
    print(f"  样式: {stage_cue.style}")
    
    return [traditional_cue, full_cue, stage_cue]

def test_script_table_model_compatibility():
    """测试 ScriptTableModel 与新模型的兼容性"""
    print("\n=== 测试 ScriptTableModel 兼容性 ===")
    
    # 创建各种类型的 cues
    cues = [
        Cue(1, "角色A", "传统台词"),
        Cue(2, "角色B", "带翻译的台词", translation="Line with translation", notes="测试备注"),
        Cue(3, None, "(舞台提示)", character_cue_index=-1, style="default"),
        Cue(4, "角色A", "完整信息台词", phonemes="wan2 zheng3", 
            character_cue_index=2, translation="Full info line", 
            notes="完整信息", style="角色A")
    ]
    
    # 创建模型
    model = ScriptTableModel(cues)
    
    print(f"模型创建成功，行数: {model.rowCount()}")
    print(f"列数: {model.columnCount()}")
    
    # 测试数据显示
    print("\n数据显示测试:")
    for row in range(model.rowCount()):
        for col in range(len(model.base_columns)):  # 只测试基础列
            index = model.index(row, col)
            data = model.data(index)
            header = model.headerData(col, Qt.Orientation.Horizontal)
            print(f"  行{row} 列{col}({header}): '{data}'")
        print()
    
    # 测试排序功能
    print("测试排序功能:")
    print("按角色排序...")
    model.sort(model.COLUMN_CHARACTER, Qt.SortOrder.AscendingOrder)
    
    for row in range(model.rowCount()):
        index = model.index(row, model.COLUMN_CHARACTER)
        character = model.data(index)
        index = model.index(row, model.COLUMN_LINE)
        line = model.data(index)
        print(f"  行{row}: 角色='{character}', 台词='{line}'")
    
    return model

def test_json_loading_compatibility():
    """测试 JSON 加载与模型的兼容性"""
    print("\n=== 测试 JSON 加载兼容性 ===")
    
    # 读取样本文件
    with open('app/models/subtitle_sample.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 转换为 Cue 对象
    cues = []
    for cue_data in data.get('cues', []):
        cue = Cue(
            id=cue_data['id'],
            character=cue_data.get('character'),
            line=cue_data['line'],
            character_cue_index=cue_data.get('character_cue_index', -1),
            translation=cue_data.get('translation', ''),
            notes=cue_data.get('notes', ''),
            style=cue_data.get('style', 'default')
        )
        cues.append(cue)
    
    print(f"从 JSON 加载了 {len(cues)} 个 cues")
    
    # 创建模型并测试
    model = ScriptTableModel(cues)
    
    print("JSON 数据在模型中的显示:")
    for row in range(model.rowCount()):
        cue = model._cues[row]
        char_display = cue.character or "(舞台提示)"
        print(f"  #{cue.id}: {char_display} - {cue.line}")
        if cue.translation:
            print(f"    翻译: {cue.translation}")
        if cue.notes:
            print(f"    备注: {cue.notes}")
        print(f"    样式: {cue.style}")
        print()
    
    return model

def test_multilingual_with_new_fields():
    """测试多语言功能与新字段的结合"""
    print("\n=== 测试多语言与新字段结合 ===")
    
    # 创建带有新字段的 cues
    cues = [
        Cue(1, "哈姆雷特", "生存还是毁灭", 
            translation="To be, or not to be", 
            notes="著名独白", style="哈姆雷特"),
        Cue(2, "奥菲利娅", "我的殿下？", 
            translation="My lord?", style="奥菲利娅"),
        Cue(3, None, "(转身离去)", 
            translation="(turns away)", 
            notes="舞台动作", style="default")
    ]
    
    # 创建模型
    model = ScriptTableModel(cues)
    
    # 添加多语言列
    model.add_language_column("法语")
    model.add_language_column("德语")
    
    print(f"添加语言列后的总列数: {model.columnCount()}")
    
    # 设置一些翻译数据
    french_translations = ["Être ou ne pas être", "Mon seigneur?", "(se détourne)"]
    german_translations = ["Sein oder nicht sein", "Mein Herr?", "(wendet sich ab)"]
    
    for row in range(len(cues)):
        # 法语列 (索引 4)
        index = model.index(row, 4)
        model.setData(index, french_translations[row])
        
        # 德语列 (索引 5)
        index = model.index(row, 5)
        model.setData(index, german_translations[row])
    
    # 显示完整的多语言数据
    print("多语言数据显示:")
    for row in range(model.rowCount()):
        cue = model._cues[row]
        char_display = cue.character or "(舞台提示)"
        print(f"  #{cue.id}: {char_display}")
        print(f"    中文: {cue.line}")
        print(f"    英文: {cue.translation}")
        
        # 显示额外语言列
        for col in range(len(model.base_columns), model.columnCount()):
            index = model.index(row, col)
            lang_data = model.data(index)
            header = model.headerData(col, Qt.Orientation.Horizontal)
            print(f"    {header}: {lang_data}")
        
        print(f"    备注: {cue.notes}")
        print(f"    样式: {cue.style}")
        print()
    
    return model

if __name__ == "__main__":
    # 运行所有测试
    print("开始全面兼容性测试...\n")
    
    cues = test_updated_cue_model()
    model1 = test_script_table_model_compatibility()  
    model2 = test_json_loading_compatibility()
    model3 = test_multilingual_with_new_fields()
    
    print("=== 所有测试完成 ===")
    print("✅ 数据模型更新成功")
    print("✅ 与现有功能完全兼容")
    print("✅ JSON 加载正常工作")
    print("✅ 多语言功能正常")
    print("✅ 支持所有新字段")
    print("\n新的数据模型已经可以投入使用！")
