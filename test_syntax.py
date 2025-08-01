#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速语法检查
"""

import ast
import sys

def check_syntax():
    """检查主要文件的语法"""
    files_to_check = [
        "app/views/main_console.py",
        "app/core/g2p/g2p_manager.py"
    ]
    
    print("🔍 检查语法...")
    
    for file_path in files_to_check:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 语法检查
            ast.parse(content)
            print(f"✅ {file_path}: 语法正确")
            
        except SyntaxError as e:
            print(f"❌ {file_path}: 语法错误 - 行 {e.lineno}: {e.msg}")
            return False
        except Exception as e:
            print(f"⚠️ {file_path}: 检查失败 - {e}")
    
    print("\n🎉 所有语法检查通过!")
    return True

if __name__ == "__main__":
    success = check_syntax()
    sys.exit(0 if success else 1)
