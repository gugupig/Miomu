#!/usr/bin/env python3
"""
测试UI文件集成
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtWidgets import QApplication
from app.views.main_console import MainConsoleWindow

def test_ui_integration():
    """测试UI文件集成"""
    app = QApplication(sys.argv)
    
    try:
        window = MainConsoleWindow()
        print("✅ UI文件集成成功!")
        print(f"使用UI文件: {hasattr(window, 'ui')}")
        
        # 检查重要的UI元素
        ui_elements = [
            'tab_widget', 'script_table', 'theater_table', 
            'load_script_btn', 'save_script_btn', 'play_btn',
            'character_color_btn', 'style_manager_btn'
        ]
        
        for element in ui_elements:
            has_element = hasattr(window, element)
            print(f"  {element}: {'✅' if has_element else '❌'}")
        
        window.show()
        print("主窗口显示成功!")
        
        # 不运行事件循环，只是测试创建
        return True
        
    except Exception as e:
        print(f"❌ UI文件集成失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        app.quit()

if __name__ == "__main__":
    test_ui_integration()
