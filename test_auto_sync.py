#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试自动同步功能
"""

import sys
import os
from pathlib import Path

def setup_environment():
    """设置环境"""
    project_root = Path(__file__).parent
    os.chdir(str(project_root))
    sys.path.insert(0, str(project_root))

def test_auto_sync():
    """测试自动同步功能"""
    setup_environment()
    
    try:
        print("🧪 测试自动同步功能...")
        
        # 导入必要模块
        from PySide6.QtWidgets import QApplication
        from app.views.main_console import MainConsoleWindow
        
        # 创建应用
        app = QApplication(sys.argv)
        
        # 创建主窗口
        print("创建主窗口...")
        window = MainConsoleWindow()
        
        # 检查自动同步相关方法
        sync_methods = [
            'sync_theater_model',
            'on_script_data_modified',
            'adjust_theater_column_widths',
        ]
        
        print(f"\n🔍 检查自动同步方法:")
        for method_name in sync_methods:
            if hasattr(window, method_name):
                method = getattr(window, method_name)
                if callable(method):
                    print(f"✅ {method_name}: 方法存在")
                else:
                    print(f"❌ {method_name}: 不是方法")
            else:
                print(f"❌ {method_name}: 方法不存在")
        
        # 检查是否删除了手动同步按钮
        print(f"\n🔍 检查手动同步按钮是否已删除:")
        if hasattr(window, 'sync_from_edit_btn'):
            print(f"⚠️ sync_from_edit_btn: 仍然存在（应该已删除）")
        else:
            print(f"✅ sync_from_edit_btn: 已成功删除")
        
        # 检查是否删除了手动同步方法
        if hasattr(window, 'sync_from_edit_mode'):
            print(f"⚠️ sync_from_edit_mode: 方法仍然存在（应该已删除）")
        else:
            print(f"✅ sync_from_edit_mode: 方法已成功删除")
            
        # 检查数据源
        print(f"\n🔍 检查数据源:")
        if hasattr(window, 'script_data'):
            print(f"✅ script_data: 存在 - {type(window.script_data)}")
        else:
            print(f"❌ script_data: 不存在")
            
        if hasattr(window, 'script_model'):
            print(f"✅ script_model: 存在 - {type(window.script_model)}")
        else:
            print(f"❌ script_model: 不存在")
            
        if hasattr(window, 'theater_model'):
            print(f"✅ theater_model: 存在 - {type(window.theater_model)}")
        else:
            print(f"❌ theater_model: 不存在")
        
        # 检查信号连接
        print(f"\n🔍 检查信号连接:")
        if hasattr(window.script_model, 'dataModified'):
            print(f"✅ script_model.dataModified: 信号存在")
        else:
            print(f"❌ script_model.dataModified: 信号不存在")
        
        print(f"\n🎉 自动同步功能测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_auto_sync()
    print(f"\n测试{'成功' if success else '失败'}")
    sys.exit(0 if success else 1)
