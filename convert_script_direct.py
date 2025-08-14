#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接使用 enhanced_script_loader 的 load_script 方法转换脚本
"""

import json
import sys
from pathlib import Path

# 添加项目路径到 sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.data.enhanced_script_loader import EnhancedScriptLoader
from app.core.g2p.g2p_manager import G2PManager

def main():
    """主函数"""
    print("🔄 使用 load_script 方法转换 script_dialogues.json...")
    
    # 检查输入文件
    input_file = 'script_dialogues.json'
    if not Path(input_file).exists():
        print(f"❌ 输入文件不存在: {input_file}")
        return 1
    
    print(f"✅ 找到输入文件: {input_file}")
    
    # 初始化G2P转换器
    try:
        print("正在初始化G2P转换器...")
        g2p_manager = G2PManager()
        g2p_converter = g2p_manager.get_current_engine()
        print('✅ G2P转换器初始化成功')
    except Exception as e:
        print(f'⚠️ G2P转换器初始化失败: {e}')
        print("继续使用None转换器...")
        g2p_converter = None

    # 创建增强版加载器
    print("正在创建增强版加载器...")
    loader = EnhancedScriptLoader(g2p_converter)
    print("✅ 加载器创建成功")

    # 直接使用 load_script 方法
    try:
        output_file = 'script_dialogues_new_format.json'
        
        print(f'🔄 开始使用 load_script 加载 {input_file}...')
        document, report = loader.load_script(input_file)
        print("✅ load_script 调用成功")
        
        # 简化报告显示
        print(f"📊 加载结果: 总共 {len(document.cues)} 条台词")
        print(f"📝 标题: {document.meta.title}")
        print(f"🌍 语言: {', '.join(document.meta.language) if document.meta.language else '未指定'}")
        
        # 检查 ngram 功能
        ngram_count = sum(1 for cue in document.cues if cue.line_ngram)
        phoneme_ngram_count = sum(1 for cue in document.cues if cue.line_ngram_phonemes)
        print(f"✅ 包含 line_ngram 的台词: {ngram_count}")
        print(f"✅ 包含 line_ngram_phonemes 的台词: {phoneme_ngram_count}")
        
        # 准备输出数据
        print("📝 准备输出数据...")
        output_data = {
            'meta': {
                'title': document.meta.title,
                'author': document.meta.author,
                'version': document.meta.version,
                'description': document.meta.description,
                'language': document.meta.language,
                'created_at': document.meta.created_at,
                'updated_at': document.meta.updated_at,
                'license': document.meta.license,
                'hash': getattr(document.meta, 'hash', None)
            },
            'styles': {name: {
                'font': style.font,
                'size': style.size,
                'color': style.color,
                'pos': style.pos
            } for name, style in document.styles.items()},
            'cues': []
        }
        
        # 转换cues数据
        print("🔄 转换cues数据...")
        for cue in document.cues:
            cue_data = {
                'id': cue.id,
                'character': cue.character,
                'line': cue.line,
                'pure_line': getattr(cue, 'pure_line', ''),
                'phonemes': cue.phonemes,
                'character_cue_index': cue.character_cue_index,
                'translation': cue.translation,
                'notes': cue.notes,
                'style': cue.style,
                'head_tok': cue.head_tok,
                'head_phonemes': cue.head_phonemes,
                'tail_tok': cue.tail_tok,
                'tail_phonemes': cue.tail_phonemes,
                'line_ngram': [list(ngram) for ngram in cue.line_ngram] if cue.line_ngram else [],
                'line_ngram_phonemes': [list(ngram) for ngram in cue.line_ngram_phonemes] if cue.line_ngram_phonemes else []
            }
            output_data['cues'].append(cue_data)
        
        # 保存到文件
        print("💾 保存到文件...")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f'\n✅ 转换完成！输出文件: {output_file}')
        print(f'📊 总共处理了 {len(document.cues)} 条台词')
        
        # 显示前几条转换结果
        print('\n📝 前3条台词的line_ngram示例:')
        count = 0
        for i, cue in enumerate(document.cues):
            if cue.line_ngram and count < 3:
                print(f'   {cue.id}. {cue.character}: {cue.line}')
                ngram_display = cue.line_ngram[:3] if len(cue.line_ngram) > 3 else cue.line_ngram
                print(f'      line_ngram: {ngram_display}{"..." if len(cue.line_ngram) > 3 else ""}')
                if cue.line_ngram_phonemes:
                    phoneme_display = cue.line_ngram_phonemes[:2] if len(cue.line_ngram_phonemes) > 2 else cue.line_ngram_phonemes
                    print(f'      line_ngram_phonemes: {phoneme_display}{"..." if len(cue.line_ngram_phonemes) > 2 else ""}')
                print()
                count += 1
        
        if count == 0:
            print("   没有找到包含 line_ngram 的台词")

        # 最终统计信息
        total_ngrams = sum(len(cue.line_ngram) for cue in document.cues if cue.line_ngram)
        total_phoneme_ngrams = sum(len(cue.line_ngram_phonemes) for cue in document.cues if cue.line_ngram_phonemes)
        
        print(f'\n📊 最终统计:')
        print(f'   包含 line_ngram 的台词: {ngram_count}/{len(document.cues)}')
        print(f'   包含 line_ngram_phonemes 的台词: {phoneme_ngram_count}/{len(document.cues)}')
        print(f'   总 line_ngram 数量: {total_ngrams}')
        print(f'   总 line_ngram_phonemes 数量: {total_phoneme_ngrams}')

    except Exception as e:
        print(f'❌ 转换失败: {e}')
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
