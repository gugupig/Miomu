#!/usr/bin/env python3
"""
Miomu - 剧本对齐系统主入口
"""
import os
import sys

# 添加CUDA库路径（如果需要）
if sys.platform == "win32":
    cuda_path = r"C:\Program Files\NVIDIA\CUDNN\v9.1\bin\12.4"
    if os.path.exists(cuda_path):
        os.add_dll_directory(cuda_path)

# 运行主控制台
if __name__ == "__main__":
    from app.views.main_console import main
    main()
