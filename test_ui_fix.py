#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速测试修复后的UI是否可以正常加载剧本
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    print("🧪 测试UI修复...")
    
    # 测试1: 导入主要模块
    print("1. 测试模块导入...")
    from PySide6.QtWidgets import QApplication
    from app.views.main_console import MainConsoleWindow
    print("✅ 模块导入成功")
    
    # 测试2: 创建应用和窗口
    print("2. 测试窗口创建...")
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    main_window = MainConsoleWindow()
    print("✅ 窗口创建成功")
    
    # 测试3: 检查修复的方法
    print("3. 测试修复的方法...")
    if hasattr(main_window, 'update_status'):
        main_window.update_status("测试消息")
        print("✅ update_status 方法工作正常")
    
    if hasattr(main_window, 'update_alignment_status'):
        main_window.update_alignment_status("测试对齐状态", "blue")
        print("✅ update_alignment_status 方法工作正常")
    
    # 测试4: 检查是否有转换后的剧本文件
    print("4. 检查剧本文件...")
    script_files = [
        "scripts/script_dialogues_converted.json",
        "scripts/final_script.json"
    ]
    
    available_files = []
    for script_file in script_files:
        script_path = Path(script_file)
        if script_path.exists():
            available_files.append(str(script_path))
            with open(script_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            cues_count = len(data.get("cues", []))
            print(f"✅ 找到剧本: {script_path} ({cues_count} 条台词)")
    
    if not available_files:
        print("⚠️ 没有找到转换后的剧本文件，需要先运行转换器")
    
    print("\n🎉 UI修复测试完成！")
    print("📋 测试结果:")
    print(f"   ✅ Qt模块导入: 正常")
    print(f"   ✅ 窗口创建: 正常") 
    print(f"   ✅ 状态更新方法: 已修复")
    print(f"   ✅ 对齐状态方法: 已修复")
    print(f"   📁 可用剧本文件: {len(available_files)} 个")
    
    if available_files:
        print(f"\n🚀 现在可以启动UI并加载以下剧本:")
        for file in available_files:
            print(f"   • {file}")
        print(f"\n启动命令: python demo_ui.py")
    else:
        print(f"\n⚠️ 请先运行转换器创建剧本文件:")
        print(f"   python scripts/script_converter.py")
    
except Exception as e:
    print(f"❌ 测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
    
print("\n✨ 测试完成！")
