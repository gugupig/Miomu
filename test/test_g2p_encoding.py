#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试G2P编码问题修复
"""

import sys
import os
from pathlib import Path

def setup_environment():
    """设置环境"""
    project_root = Path(__file__).parent
    os.chdir(str(project_root))
    sys.path.insert(0, str(project_root))

def test_g2p_encoding_fix():
    """测试G2P编码问题修复"""
    setup_environment()
    
    try:
        print("🧪 测试G2P编码问题修复...")
        
        # 导入G2P管理器
        from app.core.g2p.g2p_manager import G2PManager, G2PEngineType
        
        # 创建G2P管理器
        print("创建G2P管理器...")
        g2p_manager = G2PManager()
        
        # 测试法语Epitran引擎
        print(f"\n🔍 测试法语Epitran引擎...")
        try:
            engine = g2p_manager.create_engine(G2PEngineType.EPITRAN, "fra-Latn")
            if engine:
                print(f"✅ Epitran引擎创建成功")
                
                # 测试转换
                test_text = "bonjour"
                result = engine.convert(test_text)
                print(f"✅ 转换测试: '{test_text}' -> '{result}'")
            else:
                print(f"❌ Epitran引擎创建失败")
                
        except Exception as e:
            print(f"❌ Epitran引擎测试失败: {e}")
            
        # 测试自动回退机制
        print(f"\n🔍 测试自动回退机制...")
        available_engines = g2p_manager.get_available_engines()
        print(f"可用引擎: {[engine[0].value for engine in available_engines]}")
        
        # 获取当前引擎
        current_engine = g2p_manager.get_current_engine_info()
        print(f"当前引擎: {current_engine}")
        
        print(f"\n🎉 G2P编码问题修复测试完成!")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_g2p_encoding_fix()
    print(f"\n测试{'成功' if success else '失败'}")
    sys.exit(0 if success else 1)
