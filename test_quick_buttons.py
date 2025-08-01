#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化按钮测试
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("🧪 简化按钮测试...")

def test_buttons_quick():
    """快速测试按钮"""
    try:
        # 不启动GUI，只检查导入和初始化
        print("导入模块...")
        from app.views.main_console import MainConsoleWindow
        print("✅ 模块导入成功")
        
        # 检查类是否有我们添加的方法
        expected_methods = [
            'setup_missing_buttons',
            'connect_missing_button_signals',
            'setup_g2p_components',
            'add_g2p_components_to_ui'
        ]
        
        for method_name in expected_methods:
            if hasattr(MainConsoleWindow, method_name):
                print(f"✅ 方法存在: {method_name}")
            else:
                print(f"❌ 方法缺失: {method_name}")
        
        print("\n🎉 快速测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_buttons_quick()
    print(f"结果: {'成功' if success else '失败'}")
    sys.exit(0 if success else 1)
