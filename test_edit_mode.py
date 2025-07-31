#!/usr/bin/env python3
"""
测试新的编辑模式功能
验证 ScriptTableModel 和改进的 MainConsoleWindow
"""

import sys
import json
import tempfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QModelIndex

from app.models.script_table_model import ScriptTableModel
from app.models.models import Cue


def test_script_table_model():
    """测试 ScriptTableModel 的基本功能"""
    print("=== 测试 ScriptTableModel ===")
    
    # 创建测试数据
    test_cues = [
        Cue(id=1, character="角色A", line="第一句台词", phonemes="phoneme1"),
        Cue(id=2, character="角色B", line="第二句台词", phonemes="phoneme2"),
        Cue(id=3, character="角色A", line="第三句台词", phonemes="phoneme3"),
    ]
    
    # 创建模型
    model = ScriptTableModel(test_cues)
    
    # 测试基本数据访问
    print(f"行数: {model.rowCount()}")
    print(f"列数: {model.columnCount()}")
    
    # 测试数据获取
    for row in range(model.rowCount()):
        for col in range(model.columnCount()):
            index = model.index(row, col)
            data = model.data(index, Qt.ItemDataRole.DisplayRole)
            print(f"[{row},{col}]: {data}")
    
    # 测试数据修改
    print("\n--- 测试数据修改 ---")
    index = model.index(0, model.COLUMN_CHARACTER)
    old_data = model.data(index, Qt.ItemDataRole.DisplayRole)
    print(f"修改前: {old_data}")
    
    success = model.setData(index, "新角色A", Qt.ItemDataRole.EditRole)
    print(f"修改成功: {success}")
    
    new_data = model.data(index, Qt.ItemDataRole.DisplayRole)
    print(f"修改后: {new_data}")
    
    # 测试添加台词
    print("\n--- 测试添加台词 ---")
    original_count = model.rowCount()
    success = model.add_cue("新角色", "新台词")
    print(f"添加成功: {success}")
    print(f"行数变化: {original_count} -> {model.rowCount()}")
    
    # 测试删除台词
    print("\n--- 测试删除台词 ---")
    before_count = model.rowCount()
    success = model.remove_cue(1)  # 删除第二行
    print(f"删除成功: {success}")
    print(f"行数变化: {before_count} -> {model.rowCount()}")
    
    # 测试批量修改
    print("\n--- 测试批量修改角色 ---")
    count = model.batch_update_character("角色A", "统一角色")
    print(f"批量修改了 {count} 条台词")
    
    # 测试搜索
    print("\n--- 测试搜索功能 ---")
    matches = model.search_cues("统一")
    print(f"搜索 '统一' 找到 {len(matches)} 个匹配项: {matches}")
    
    print("ScriptTableModel 测试完成！\n")
    return model


def test_main_console_integration():
    """测试与主控制台的集成"""
    print("=== 测试主控制台集成 ===")
    
    # 创建临时测试文件
    test_data = {
        "cues": [
            {"id": 1, "character": "测试角色1", "line": "这是第一句测试台词"},
            {"id": 2, "character": "测试角色2", "line": "这是第二句测试台词"},
            {"id": 3, "character": "测试角色1", "line": "这是第三句测试台词"},
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
        temp_file = f.name
    
    print(f"创建临时测试文件: {temp_file}")
    
    try:
        # 导入主控制台（这会触发UI组件的创建）
        from app.views.main_console import MainConsoleWindow
        
        app = QApplication.instance() or QApplication(sys.argv)
        
        # 创建主控制台窗口
        console = MainConsoleWindow()
        
        # 测试数据模型集成
        print("测试数据模型集成...")
        model = console.script_model
        
        # 检查初始状态
        print(f"初始行数: {model.rowCount()}")
        print(f"是否已修改: {model.is_modified()}")
        
        # 手动设置一些测试数据
        test_cues = [
            Cue(id=1, character="集成测试角色", line="集成测试台词", phonemes="test_phoneme")
        ]
        model.set_cues(test_cues)
        
        print(f"设置数据后行数: {model.rowCount()}")
        print(f"设置数据后是否已修改: {model.is_modified()}")
        
        # 测试修改数据
        index = model.index(0, model.COLUMN_LINE)
        model.setData(index, "修改后的台词", Qt.ItemDataRole.EditRole)
        
        print(f"修改数据后是否已修改: {model.is_modified()}")
        
        print("主控制台集成测试完成！")
        
    finally:
        # 清理临时文件
        Path(temp_file).unlink(missing_ok=True)
        print(f"清理临时文件: {temp_file}")


def main():
    """主测试函数"""
    print("开始测试新的编辑模式功能...\n")
    
    # 创建QApplication（某些Qt功能需要）
    app = QApplication.instance() or QApplication(sys.argv)
    
    try:
        # 测试数据模型
        model = test_script_table_model()
        
        # 测试集成
        test_main_console_integration()
        
        print("✅ 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
