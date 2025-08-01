#!/usr/bin/env python3
"""
测试UI改进和角色颜色功能
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from app.views.main_console import MainConsoleWindow
from app.utils.character_color_manager import CharacterColorManager
from app.models.models import Cue, SubtitleDocument, Meta, Style

def create_test_data():
    """创建测试数据"""
    cues = [
        Cue(id=1, character="L'HOMME", line="Bonjour, comment allez-vous?", 
            translation={"zh": "你好，你好吗？", "en": "Hello, how are you?"}),
        Cue(id=2, character="LE_PÊCHEUR", line="Très bien, merci!", 
            translation={"zh": "很好，谢谢！", "en": "Very well, thank you!"}),
        Cue(id=3, character="L'HOMME", line="Que faites-vous ici?", 
            translation={"zh": "你在这里做什么？", "en": "What are you doing here?"}),
        Cue(id=4, character="LE_CAPITAINE", line="Je commande ce navire.", 
            translation={"zh": "我指挥这艘船。", "en": "I command this ship."}),
        Cue(id=5, character=None, line="[舞台提示：天空渐暗]", 
            translation={"zh": "[舞台提示：天空渐暗]", "en": "[Stage direction: The sky darkens]"}),
    ]
    return cues

def test_character_color_manager():
    """测试角色颜色管理器"""
    print("测试角色颜色管理器...")
    
    manager = CharacterColorManager()
    
    # 测试添加角色
    manager.add_character("L'HOMME")
    manager.add_character("LE_PÊCHEUR")
    manager.add_character("LE_CAPITAINE")
    
    # 测试获取颜色
    color1 = manager.get_character_color("L'HOMME")
    color2 = manager.get_character_color("LE_PÊCHEUR")
    color3 = manager.get_character_color("LE_CAPITAINE")
    
    print(f"L'HOMME 颜色: {color1}")
    print(f"LE_PÊCHEUR 颜色: {color2}")
    print(f"LE_CAPITAINE 颜色: {color3}")
    
    # 测试从台词导入角色
    test_cues = create_test_data()
    new_count = manager.import_characters_from_cues(test_cues)
    print(f"从台词导入了 {new_count} 个新角色")
    
    all_characters = manager.get_all_characters()
    print(f"所有角色: {all_characters}")
    
    # 清理测试文件
    if os.path.exists("character_colors.json"):
        os.remove("character_colors.json")
    
    print("角色颜色管理器测试通过！")

def main():
    """主函数"""
    print("开始测试UI改进...")
    
    # 测试角色颜色管理器
    test_character_color_manager()
    
    # 启动应用程序测试UI
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = MainConsoleWindow()
    
    # 添加一些测试数据
    test_cues = create_test_data()
    window.script_data.cues = test_cues
    window.script_model.set_cues(test_cues)
    window.theater_model.set_cues(test_cues.copy())
    
    # 启用按钮（模拟数据加载完成）
    window.save_script_btn.setEnabled(True)
    window.add_cue_btn.setEnabled(True)
    window.delete_cue_btn.setEnabled(True)
    window.duplicate_cue_btn.setEnabled(True)
    window.refresh_phonemes_btn.setEnabled(True)
    window.add_language_btn.setEnabled(True)
    window.remove_language_btn.setEnabled(True)
    window.manage_styles_btn.setEnabled(True)
    window._update_theater_buttons()
    
    # 导入角色颜色
    window.character_color_manager.import_characters_from_cues(test_cues)
    
    window.show()
    
    print("UI测试窗口已打开")
    print("请测试以下功能：")
    print("1. 编辑模式：管理样式按钮")
    print("2. 剧场模式：同步编辑模式数据、按角色筛选、管理角色颜色")
    print("3. 表格中的角色颜色显示")
    print("4. 角色颜色管理对话框")
    print("5. 角色筛选对话框")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
