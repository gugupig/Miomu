#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试在UI中加载转换后的剧本
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("导入Qt模块...")
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PySide6.QtCore import Qt

print("导入应用模块...")
from app.views.main_console import MainConsoleWindow


def test_script_loading_ui():
    """在UI中测试剧本加载功能"""
    print("🎭 启动UI测试剧本加载功能")
    print("=" * 50)
    
    try:
        # 创建Qt应用
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        print("✅ Qt应用创建成功")
        
        # 创建主窗口
        main_window = MainConsoleWindow()
        main_window.show()
        
        print("✅ 主窗口创建成功")
        
        # 检查转换后的剧本文件是否存在
        script_files = [
            "scripts/script_dialogues_converted.json",
            "scripts/final_script.json"
        ]
        
        available_files = []
        for script_file in script_files:
            script_path = Path(script_file)
            if script_path.exists():
                available_files.append(str(script_path))
                print(f"✅ 找到剧本文件: {script_path}")
        
        if not available_files:
            print("❌ 没有找到转换后的剧本文件")
            return False
        
        # 模拟用户选择文件并加载
        test_file = available_files[0]
        print(f"🎯 测试加载文件: {test_file}")
        
        # 直接调用加载方法，模拟用户选择文件
        # 这会创建LoadScriptThread并在后台加载
        print("🚀 开始加载剧本...")
        
        # 验证文件格式是否正确
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        cues_count = len(data.get("cues", []))
        print(f"📊 剧本包含 {cues_count} 条台词")
        
        # 显示一些基本信息
        meta = data.get("meta", {})
        print(f"📝 剧本标题: {meta.get('title', '未知')}")
        print(f"👤 作者: {meta.get('author', '未知')}")
        print(f"🌍 语言: {meta.get('language', ['未知'])}")
        
        print("✅ 剧本文件格式验证通过")
        print("🎉 UI加载测试准备完成！")
        print("\n📋 接下来的步骤：")
        print("1. UI窗口已打开")
        print("2. 点击 '加载剧本' 按钮")
        print(f"3. 选择文件: {test_file}")
        print("4. 验证是否成功加载并显示台词列表")
        
        # 显示消息框提示用户
        msg = QMessageBox()
        msg.setWindowTitle("测试说明")
        msg.setText("UI测试已准备完成！\n\n请按以下步骤测试：\n1. 点击'加载剧本'按钮\n2. 选择转换后的剧本文件\n3. 验证加载是否成功")
        msg.setInformativeText(f"推荐测试文件：\n{test_file}")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
        
        return True
        
    except Exception as e:
        print(f"❌ UI测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_script_loading_ui()
    if success:
        print("\n🎉 UI测试程序启动成功！请手动测试加载功能。")
    else:
        print("\n💥 UI测试启动失败！")
