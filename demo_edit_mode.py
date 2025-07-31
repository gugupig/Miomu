#!/usr/bin/env python3
"""
演示新编辑模式功能的完整示例
展示如何使用 ScriptTableModel 和改进的主控制台
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from app.views.main_console import MainConsoleWindow
from app.models.script_table_model import ScriptTableModel
from app.models.models import Cue


def demo_edit_mode():
    """演示编辑模式的各种功能"""
    print("=== Miomu 编辑模式功能演示 ===\n")
    
    # 创建应用程序
    app = QApplication.instance() or QApplication(sys.argv)
    
    # 创建主控制台窗口
    print("1. 创建主控制台窗口...")
    console = MainConsoleWindow()
    console.show()
    
    # 获取数据模型
    model = console.script_model
    
    # 创建演示数据
    print("2. 创建演示数据...")
    demo_cues = [
        Cue(id=1, character="叙述者", line="很久很久以前，在一个遥远的地方...", phonemes="narrator_phoneme_1"),
        Cue(id=2, character="主角", line="我必须踏上这段冒险之旅！", phonemes="hero_phoneme_1"),
        Cue(id=3, character="智者", line="年轻人，前路充满危险。", phonemes="sage_phoneme_1"),
        Cue(id=4, character="主角", line="无论多么危险，我都不会退缩！", phonemes="hero_phoneme_2"),
        Cue(id=5, character="叙述者", line="于是，主角开始了他的传奇故事...", phonemes="narrator_phoneme_2"),
    ]
    
    # 设置数据到模型
    model.set_cues(demo_cues)
    print(f"   已加载 {model.rowCount()} 条台词")
    
    # 演示基本编辑功能
    print("\n3. 演示基本编辑功能...")
    
    # 添加新台词
    print("   添加新台词...")
    success = model.add_cue("反派", "你以为你能阻止我吗？哈哈哈！")
    print(f"   添加结果: {success}, 当前台词数: {model.rowCount()}")
    
    # 修改现有台词
    print("   修改台词内容...")
    index = model.index(1, model.COLUMN_LINE)  # 第2行，台词列
    old_line = model.data(index, Qt.ItemDataRole.DisplayRole)
    success = model.setData(index, "我一定要完成这个使命！", Qt.ItemDataRole.EditRole)
    new_line = model.data(index, Qt.ItemDataRole.DisplayRole)
    print(f"   修改前: {old_line}")
    print(f"   修改后: {new_line}")
    print(f"   修改结果: {success}")
    
    # 复制台词
    print("   复制台词...")
    original_count = model.rowCount()
    success = model.duplicate_cue(0)  # 复制第一条台词
    print(f"   复制结果: {success}, 台词数变化: {original_count} -> {model.rowCount()}")
    
    # 演示批量操作
    print("\n4. 演示批量操作...")
    
    # 批量修改角色名称
    print("   批量修改角色名称...")
    count = model.batch_update_character("主角", "英雄")
    print(f"   将 '主角' 改为 '英雄', 共修改 {count} 条台词")
    
    # 搜索功能
    print("   搜索功能演示...")
    matches = model.search_cues("危险")
    print(f"   搜索 '危险' 找到 {len(matches)} 个匹配项，位置: {matches}")
    
    matches = model.search_cues("英雄", model.COLUMN_CHARACTER)
    print(f"   在角色列搜索 '英雄' 找到 {len(matches)} 个匹配项，位置: {matches}")
    
    # 演示数据状态管理
    print("\n5. 演示数据状态管理...")
    print(f"   当前修改状态: {model.is_modified()}")
    
    # 保存快照
    print("   保存当前状态快照...")
    model.save_snapshot()
    model.mark_saved()
    print(f"   保存后修改状态: {model.is_modified()}")
    
    # 进行一些修改
    print("   进行新的修改...")
    model.add_cue("新角色", "这是新添加的台词")
    print(f"   修改后状态: {model.is_modified()}")
    
    # 恢复快照
    print("   恢复到快照状态...")
    old_count = model.rowCount()
    model.restore_snapshot()
    new_count = model.rowCount()
    print(f"   恢复后台词数变化: {old_count} -> {new_count}")
    print(f"   恢复后修改状态: {model.is_modified()}")
    
    # 演示数据验证
    print("\n6. 演示数据验证...")
    
    # 尝试设置空的角色名称（应该失败）
    index = model.index(0, model.COLUMN_CHARACTER)
    success = model.setData(index, "", Qt.ItemDataRole.EditRole)
    print(f"   尝试设置空角色名称: {success} (应该为 False)")
    
    # 尝试设置超长的台词（应该失败）
    index = model.index(0, model.COLUMN_LINE)
    long_line = "这是一个超级超级超级" + "长" * 500 + "的台词"
    success = model.setData(index, long_line, Qt.ItemDataRole.EditRole)
    print(f"   尝试设置超长台词: {success} (应该为 False)")
    
    # 显示最终数据
    print("\n7. 最终数据展示...")
    print("   当前所有台词:")
    for row in range(model.rowCount()):
        id_data = model.data(model.index(row, model.COLUMN_ID), Qt.ItemDataRole.DisplayRole)
        character_data = model.data(model.index(row, model.COLUMN_CHARACTER), Qt.ItemDataRole.DisplayRole)
        line_data = model.data(model.index(row, model.COLUMN_LINE), Qt.ItemDataRole.DisplayRole)
        print(f"   {id_data}: {character_data} - {line_data}")
    
    print(f"\n8. 功能特性总结:")
    print(f"   ✅ 数据模型与显示完全分离")
    print(f"   ✅ 支持添加、删除、复制、修改台词")
    print(f"   ✅ 支持批量操作和搜索")
    print(f"   ✅ 内置数据验证机制")
    print(f"   ✅ 支持撤销/恢复功能")
    print(f"   ✅ 修改状态追踪")
    print(f"   ✅ 信号机制支持UI自动更新")
    
    print(f"\n=== 演示完成！===")
    print(f"窗口已打开，您可以在编辑模式标签页中体验所有功能。")
    print(f"包括右键菜单、工具栏按钮、多选操作等。")
    
    # 如果是直接运行，显示窗口
    if __name__ == "__main__":
        print("\n按 Ctrl+C 退出演示")
        try:
            app.exec()
        except KeyboardInterrupt:
            print("\n演示结束")
    
    return console


if __name__ == "__main__":
    demo_edit_mode()
