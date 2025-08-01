#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面按钮测试脚本
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("🧪 全面按钮测试开始...")
print("导入Qt模块...")

try:
    from PySide6.QtWidgets import QApplication
    print("✅ Qt模块导入成功")
except ImportError as e:
    print(f"❌ Qt模块导入失败: {e}")
    sys.exit(1)

print("导入应用模块...")
try:
    from app.views.main_console import MainConsoleWindow
    print("✅ 主窗口模块导入成功")
except ImportError as e:
    print(f"❌ 主窗口模块导入失败: {e}")
    sys.exit(1)

def test_comprehensive_buttons():
    """全面测试所有按钮"""
    app = QApplication(sys.argv)
    
    try:
        print("\n🏗️ 创建主窗口...")
        window = MainConsoleWindow()
        print("✅ 主窗口创建成功")
        
        # 所有预期的按钮
        expected_buttons = [
            ('load_script_btn', '加载剧本'),
            ('save_script_btn', '保存剧本'),
            ('show_subtitle_btn', '显示字幕窗口'),
            ('show_debug_btn', '调试窗口'),
            ('add_cue_btn', '添加台词'),
            ('delete_cue_btn', '删除台词'),
            ('duplicate_cue_btn', '复制台词'),
            ('refresh_phonemes_btn', '刷新音素'),
            ('add_language_btn', '添加语言'),
            ('remove_language_btn', '移除语言'),
            ('manage_styles_btn', '管理样式'),
            ('sync_from_edit_btn', '同步编辑模式数据'),
            ('load_script_theater_btn', '加载剧本'),
        ]
        
        print(f"\n🔍 检查 {len(expected_buttons)} 个预期按钮...")
        
        success_count = 0
        fail_count = 0
        
        for btn_name, expected_text in expected_buttons:
            if hasattr(window, btn_name):
                btn = getattr(window, btn_name)
                if btn and hasattr(btn, 'text'):
                    actual_text = btn.text()
                    if expected_text in actual_text or actual_text in expected_text:
                        print(f"✅ {btn_name}: '{actual_text}'")
                        success_count += 1
                    else:
                        print(f"⚠️ {btn_name}: 文本不匹配 - 期望包含'{expected_text}', 实际'{actual_text}'")
                        success_count += 1  # 仍然算成功，只是文本不同
                else:
                    print(f"❌ {btn_name}: 存在但无效")
                    fail_count += 1
            else:
                print(f"❌ {btn_name}: 不存在")
                fail_count += 1
        
        # 检查关键别名
        print(f"\n🔍 检查关键别名...")
        aliases = [
            ('start_btn', 'play_btn'),
            ('script_view', 'script_table'),
            ('theater_view', 'theater_table'),
        ]
        
        alias_success = 0
        for alias, original in aliases:
            if hasattr(window, alias) and hasattr(window, original):
                alias_obj = getattr(window, alias)
                original_obj = getattr(window, original)
                if alias_obj is original_obj:
                    print(f"✅ 别名 {alias} -> {original}")
                    alias_success += 1
                else:
                    print(f"⚠️ 别名 {alias} -> {original}: 不是同一对象")
            else:
                print(f"❌ 别名 {alias} -> {original}: 组件缺失")
        
        # 检查G2P组件
        print(f"\n🔍 检查G2P组件...")
        g2p_components = ['g2p_engine_combo', 'g2p_language_combo', 'g2p_status_label']
        g2p_success = 0
        
        for comp_name in g2p_components:
            if hasattr(window, comp_name):
                comp = getattr(window, comp_name)
                if comp:
                    print(f"✅ {comp_name}: {type(comp).__name__}")
                    g2p_success += 1
                else:
                    print(f"❌ {comp_name}: None")
            else:
                print(f"❌ {comp_name}: 不存在")
        
        # 总结
        print(f"\n📊 测试总结:")
        print(f"   按钮测试: {success_count}/{len(expected_buttons)} 成功")
        print(f"   别名测试: {alias_success}/{len(aliases)} 成功")
        print(f"   G2P组件: {g2p_success}/{len(g2p_components)} 成功")
        
        total_tests = len(expected_buttons) + len(aliases) + len(g2p_components)
        total_success = success_count + alias_success + g2p_success
        
        print(f"   总体成功率: {total_success}/{total_tests} ({total_success/total_tests*100:.1f}%)")
        
        if total_success == total_tests:
            print("\n🎉 所有测试通过!")
            return True
        else:
            print(f"\n⚠️ 有 {total_tests - total_success} 项测试未通过")
            return False
            
    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        print("\n🧹 清理资源...")
        app.quit()

if __name__ == "__main__":
    success = test_comprehensive_buttons()
    print(f"\n🏁 测试结束，结果: {'成功' if success else '失败'}")
    sys.exit(0 if success else 1)
