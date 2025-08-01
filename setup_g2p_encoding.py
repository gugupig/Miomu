#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G2P编码问题解决方案
设置正确的编码环境
"""

import os
import sys

def setup_utf8_environment():
    """设置UTF-8编码环境"""
    print("🔧 设置UTF-8编码环境...")
    
    # 设置Python IO编码
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # 设置语言环境
    if sys.platform.startswith('win'):
        # Windows系统
        os.environ['LANG'] = 'en_US.UTF-8'
        os.environ['LC_ALL'] = 'en_US.UTF-8'
        print("✅ Windows UTF-8环境已设置")
    else:
        # Linux/Mac系统
        os.environ['LANG'] = 'en_US.UTF-8'
        os.environ['LC_ALL'] = 'en_US.UTF-8'
        print("✅ Linux/Mac UTF-8环境已设置")
    
    # 设置标准输出编码
    if hasattr(sys.stdout, 'reconfigure'):
        try:
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
            print("✅ 标准输出编码已设置为UTF-8")
        except:
            pass
    
    print("🎉 UTF-8编码环境设置完成")

if __name__ == "__main__":
    setup_utf8_environment()
    
    # 测试编码设置
    print(f"当前编码设置:")
    print(f"  - PYTHONIOENCODING: {os.environ.get('PYTHONIOENCODING', 'unset')}")
    print(f"  - LANG: {os.environ.get('LANG', 'unset')}")
    print(f"  - LC_ALL: {os.environ.get('LC_ALL', 'unset')}")
    print(f"  - 标准输出编码: {sys.stdout.encoding}")
    
    # 现在测试G2P
    try:
        from app.core.g2p.g2p_manager import G2PManager, G2PEngineType
        
        print(f"\n🧪 测试G2P引擎...")
        g2p_manager = G2PManager()
        
        # 尝试创建Epitran引擎
        try:
            engine = g2p_manager.create_engine(G2PEngineType.EPITRAN, "fra-Latn")
            if engine:
                print(f"🎉 Epitran引擎创建成功！")
                result = engine.convert("bonjour")
                print(f"   测试转换: 'bonjour' -> '{result}'")
        except Exception as e:
            print(f"⚠️ Epitran仍然失败: {e}")
            print(f"   但系统会自动使用备用引擎")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
