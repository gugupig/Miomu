#!/usr/bin/env python3
"""测试新的数据模型能否正确处理 subtitle_sample.json"""

import sys
import json
sys.path.append('.')

from app.models.models import Cue, Meta, Style, SubtitleDocument

def test_load_subtitle_sample():
    """测试加载 subtitle_sample.json"""
    print("=== 测试加载字幕样本文件 ===")
    
    # 读取JSON文件
    with open('app/models/subtitle_sample.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("JSON 文件读取成功")
    print(f"包含的主要键: {list(data.keys())}")
    
    # 解析元数据
    meta_data = data.get('meta', {})
    meta = Meta(
        title=meta_data.get('title', ''),
        author=meta_data.get('author', ''),
        translator=meta_data.get('translator', ''),
        version=meta_data.get('version', '1.0'),
        description=meta_data.get('description', ''),
        language=meta_data.get('language', []),
        created_at=meta_data.get('created_at'),
        updated_at=meta_data.get('updated_at'),
        license=meta_data.get('license', '')
    )
    
    print(f"\n元数据解析:")
    print(f"  标题: {meta.title}")
    print(f"  作者: {meta.author}")
    print(f"  翻译: {meta.translator}")
    print(f"  语言: {meta.language}")
    
    # 解析样式
    styles_data = data.get('styles', {})
    styles = {}
    
    for style_name, style_props in styles_data.items():
        style = Style(
            font=style_props.get('font', 'Noto Sans'),
            size=style_props.get('size', 42),
            color=style_props.get('color', '#FFFFFF'),
            pos=style_props.get('pos', 'bottom')
        )
        styles[style_name] = style
    
    print(f"\n样式解析:")
    for name, style in styles.items():
        print(f"  {name}: {style}")
    
    # 解析 cues
    cues_data = data.get('cues', [])
    cues = []
    
    for cue_data in cues_data:
        cue = Cue(
            id=cue_data['id'],
            character=cue_data.get('character'),  # 可能为 null
            line=cue_data['line'],
            character_cue_index=cue_data.get('character_cue_index', -1),
            translation=cue_data.get('translation', ''),
            notes=cue_data.get('notes', ''),
            style=cue_data.get('style', 'default')
        )
        cues.append(cue)
    
    print(f"\nCues 解析 (共 {len(cues)} 条):")
    for cue in cues:
        char_info = f"角色: {cue.character}" if cue.character else "角色: None (舞台提示)"
        print(f"  #{cue.id} - {char_info}")
        print(f"    台词: {cue.line}")
        if cue.translation:
            print(f"    翻译: {cue.translation}")
        if cue.notes:
            print(f"    备注: {cue.notes}")
        print(f"    样式: {cue.style}")
        print()
    
    # 创建完整文档
    document = SubtitleDocument(
        meta=meta,
        styles=styles,
        cues=cues
    )
    
    print("=== 文档创建成功 ===")
    print(f"元数据标题: {document.meta.title}")
    print(f"样式数量: {len(document.styles)}")
    print(f"台词数量: {len(document.cues)}")
    
    # 测试新字段的访问
    print("\n=== 测试新字段访问 ===")
    for cue in document.cues:
        print(f"Cue #{cue.id}:")
        print(f"  character_cue_index: {cue.character_cue_index}")
        print(f"  translation: {cue.translation}")
        print(f"  notes: {cue.notes}")
        print(f"  style: {cue.style}")
    
    print("\n测试完成！")

if __name__ == "__main__":
    test_load_subtitle_sample()
