#!/usr/bin/env python3
"""
测试所有按钮修复
"""
import sys
import os
from pathlib import Path

def setup_environment():
    """设置环境"""
    project_root = Path(__file__).parent
    os.chdir(str(project_root))
    sys.path.insert(0, str(project_root))

def test_all_buttons():
    """测试所有按钮修复"""
    setup_environment()
    
    try:
        print("🧪 测试所有按钮修复...")
        
        # 导入必要模块
        from PySide6.QtWidgets import QApplication
        from app.views.main_console import MainConsoleWindow
        
        # 创建应用
        app = QApplication(sys.argv)
        
        # 创建主窗口
        print("创建主窗口...")
        window = MainConsoleWindow()
        
        # 检查所有关键按钮
        print("检查按钮...")
        
        # 基本按钮（UI文件中存在的）
        ui_buttons = [
            'load_script_btn',
            'save_script_btn', 
            'play_btn',
            'start_btn',  # 别名
            'pause_btn',
            'stop_btn',
            'show_subtitle_btn',
            'show_debug_btn',
        ]
        
        # 编辑按钮（可能需要动态创建的）
        edit_buttons = [
            'add_cue_btn',
            'delete_cue_btn',
            'duplicate_cue_btn',
            'refresh_phonemes_btn',
            'add_language_btn',
            'remove_language_btn',
            'manage_styles_btn',
        ]
        
        # 表格组件
        table_components = [
            'script_table',
            'script_view',  # 别名
            'theater_table',
            'theater_view',  # 别名
        ]
        
        all_components = ui_buttons + edit_buttons + table_components
        
        print(f"\n📊 检查 {len(all_components)} 个组件:")
        
        results = {}
        for component in all_components:
            exists = hasattr(window, component) and getattr(window, component) is not None
            results[component] = exists
            status = "✅" if exists else "❌"
            print(f"  {status} {component}")
        
        # 统计结果
        total = len(all_components)
        existing = sum(results.values())
        missing = total - existing
        
        print(f"\n📈 结果统计:")
        print(f"  总组件数: {total}")
        print(f"  ✅ 存在: {existing}")
        print(f"  ❌ 缺失: {missing}")
        print(f"  成功率: {existing/total*100:.1f}%")
        
        # 显示缺失的组件
        if missing > 0:
            print(f"\n❌ 缺失的组件:")
            for component, exists in results.items():
                if not exists:
                    print(f"  • {component}")
        
        return missing == 0
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_all_buttons()
    print(f"\n测试{'成功' if success else '失败'}")
    sys.exit(0 if success else 1)
