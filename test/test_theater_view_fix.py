#!/usr/bin/env python3
"""
测试theater_view修复
"""
import sys
import os
from pathlib import Path

def setup_environment():
    """设置环境"""
    project_root = Path(__file__).parent
    os.chdir(str(project_root))
    sys.path.insert(0, str(project_root))

def test_theater_view_fix():
    """测试theater_view修复"""
    setup_environment()
    
    try:
        print("🧪 测试theater_view修复...")
        
        # 导入必要模块
        from PySide6.QtWidgets import QApplication
        from app.views.main_console import MainConsoleWindow
        
        # 创建应用
        app = QApplication(sys.argv)
        
        # 创建主窗口
        print("创建主窗口...")
        window = MainConsoleWindow()
        
        # 检查theater相关组件
        print("检查theater组件...")
        
        components = {
            'theater_table': hasattr(window, 'theater_table') and window.theater_table is not None,
            'theater_view': hasattr(window, 'theater_view') and window.theater_view is not None,
            'script_table': hasattr(window, 'script_table') and window.script_table is not None,
            'script_view': hasattr(window, 'script_view') and window.script_view is not None,
        }
        
        print("\n📊 组件检查结果:")
        for name, exists in components.items():
            status = "✅" if exists else "❌"
            print(f"  {status} {name}: {'存在' if exists else '缺失'}")
        
        # 检查别名是否指向同一个对象
        if components['theater_table'] and components['theater_view']:
            same_object = window.theater_table is window.theater_view
            print(f"\n🔗 theater_table 和 theater_view 别名检查: {'✅ 指向同一对象' if same_object else '❌ 不同对象'}")
            
        if components['script_table'] and components['script_view']:
            same_object = window.script_table is window.script_view
            print(f"🔗 script_table 和 script_view 别名检查: {'✅ 指向同一对象' if same_object else '❌ 不同对象'}")
        
        # 测试完成
        all_ok = all(components.values())
        if all_ok:
            print("\n🎉 所有表格组件都已正确创建！")
            return True
        else:
            print("\n⚠️ 部分表格组件缺失")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_theater_view_fix()
    print(f"\n测试{'成功' if success else '失败'}")
    sys.exit(0 if success else 1)
