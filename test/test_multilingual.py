#!/usr/bin/env python3
"""测试多语言功能的简单脚本"""

import sys
sys.path.append('.')

from app.models.script_table_model import ScriptTableModel
from app.data.script_data import ScriptData, Cue
from app.models.models import Cue
from PySide6.QtCore import Qt

def test_multilingual_feature():
    """测试多语言功能"""
    print("=== 多语言功能测试 ===")
    
    # 创建测试数据
    cues = [
        Cue(1, "角色A", "Hello world"),
        Cue(2, "角色B", "How are you?"),
        Cue(3, "角色A", "I'm fine, thank you.")
    ]
    
    # 创建模型
    model = ScriptTableModel(cues)
    
    print(f"初始列数: {model.columnCount()}")
    print(f"基础列: {model.base_columns}")
    
    # 添加中文列
    success = model.add_language_column("中文")
    print(f"添加中文列: {success}")
    print(f"添加后列数: {model.columnCount()}")
    
    # 添加一些中文翻译
    from PySide6.QtCore import QModelIndex
    print("\n=== 添加中文翻译 ===")
    index = model.index(0, 3)  # 第0行，第3列应该是音素列
    print(f"索引(0,3) - 应该是音素列: {model.data(index)}")
    
    index = model.index(0, 4)  # 第0行，第4列应该是中文列
    print(f"索引(0,4) - 应该是中文列: {model.data(index)}")
    print(f"设置中文翻译...")
    success = model.setData(index, "你好世界")
    print(f"设置成功: {success}")
    print(f"设置后的数据: {model.data(index)}")
    
    index = model.index(1, 4)  # 第1行，第4列
    model.setData(index, "你好吗？")
    
    index = model.index(2, 4)  # 第2行，第4列
    model.setData(index, "我很好，谢谢。")
    
    # 验证数据
    print("\n=== 验证数据 ===")
    for row in range(model.rowCount()):
        for col in range(model.columnCount()):
            index = model.index(row, col)
            data = model.data(index)
            header = model.headerData(col, Qt.Orientation.Horizontal)
            print(f"行{row} 列{col}({header}): {data}")
    
    # 添加法语列
    success = model.add_language_column("法语")
    print(f"\n添加法语列: {success}")
    print(f"添加后列数: {model.columnCount()}")
    
    # 添加一些法语翻译
    index = model.index(0, 5)  # 第0行，第5列（法语列）
    model.setData(index, "Bonjour le monde")
    
    # 验证最终状态
    print("\n=== 最终状态 ===")
    print(f"总列数: {model.columnCount()}")
    print(f"语言列: {model.get_language_columns()}")
    
    # 测试移除语言列
    print("\n=== 测试移除语言列 ===")
    success = model.remove_language_column("中文")
    print(f"移除中文列: {success}")
    print(f"移除后列数: {model.columnCount()}")
    print(f"剩余语言列: {model.get_language_columns()}")
    
    # 验证移除后的数据
    print("\n=== 移除后验证数据 ===")
    for row in range(model.rowCount()):
        for col in range(model.columnCount()):
            index = model.index(row, col)
            data = model.data(index)
            header = model.headerData(col, Qt.Orientation.Horizontal)
            print(f"行{row} 列{col}({header}): {data}")
    
    print("完成测试！")

if __name__ == "__main__":
    test_multilingual_feature()
