#!/usr/bin/env python3
"""
Miomu - 剧本对齐系统主入口
"""
import os
import sys
import builtins


# 全局智能编码处理（解决Epitran G2P编码问题）
def setup_global_encoding():
    """设置全局UTF-8编码环境和智能文件处理"""
    # 1. 设置环境变量
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['PYTHONUTF8'] = '1'
    if sys.platform.startswith('win'):
        os.environ['LANG'] = 'en_US.UTF-8'
        os.environ['LC_ALL'] = 'en_US.UTF-8'
    
    # 2. 保存原始open函数
    original_open = builtins.open
    
    def smart_global_open(file, mode='r', encoding=None, **kwargs):
        """全局智能UTF-8编码处理"""
        # 如果是二进制模式，不设置编码
        if 'b' in mode:
            return original_open(file, mode=mode, **kwargs)
        
        # 如果是文本模式且没有指定编码，使用UTF-8
        if 'r' in mode or 'w' in mode or 'a' in mode:
            if encoding is None:
                # 特殊处理可能是二进制的文件
                if isinstance(file, (str, bytes)):
                    file_str = str(file)
                    # 跳过这些可能是二进制的文件
                    if any(ext in file_str for ext in ['.pkl', '.bin', '.dat', '.so', '.dll', '.exe']):
                        return original_open(file, mode=mode, **kwargs)
                
                encoding = 'utf-8'
        
        return original_open(file, mode=mode, encoding=encoding, **kwargs)
    
    # 3. 全局替换open函数
    builtins.open = smart_global_open
    
    # 4. 修复pandas的read_csv编码问题（这是Epitran/panphon的关键问题）
    try:
        import pandas as pd
        
        # 保存原始的read_csv函数
        if not hasattr(pd.read_csv, '_original_func'):
            original_read_csv = pd.read_csv
            
            def utf8_read_csv(*args, **kwargs):
                """UTF-8优先的read_csv函数"""
                # 如果没有指定encoding，尝试UTF-8
                if 'encoding' not in kwargs:
                    try:
                        # 首先尝试UTF-8
                        return original_read_csv(*args, encoding='utf-8', **kwargs)
                    except UnicodeDecodeError:
                        try:
                            # UTF-8失败，尝试GBK
                            return original_read_csv(*args, encoding='gbk', **kwargs)
                        except UnicodeDecodeError:
                            # GBK也失败，尝试latin-1作为最后手段
                            return original_read_csv(*args, encoding='latin-1', **kwargs)
                else:
                    # 已经指定了encoding，直接调用原函数
                    return original_read_csv(*args, **kwargs)
            
            # 标记原始函数，避免重复包装
            utf8_read_csv._original_func = original_read_csv  # type: ignore
            pd.read_csv = utf8_read_csv
            
        print("[Global Encoding] ✅ 已设置全局UTF-8编码处理（包括pandas修复）")
    except ImportError:
        print("[Global Encoding] ✅ 已设置全局UTF-8编码处理（pandas未安装）")

# 设置UTF-8编码环境（解决G2P编码问题） 
def setup_encoding():
    """向后兼容的编码设置函数"""
    setup_global_encoding()

# 在导入其他模块之前设置编码
setup_global_encoding()

# 添加CUDA库路径（如果需要）
if sys.platform == "win32":
    cuda_path = r"C:\Program Files\NVIDIA\CUDNN\v9.1\bin\12.4"
    if os.path.exists(cuda_path):
        os.add_dll_directory(cuda_path)

# 运行主控制台
if __name__ == "__main__":
    from app.views.main_console import main
    main()
