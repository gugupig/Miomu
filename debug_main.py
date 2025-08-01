#!/usr/bin/env python3
"""
调试版主入口
"""
import os
import sys

print(f"Python版本: {sys.version}")
print(f"当前工作目录: {os.getcwd()}")

# 添加CUDA库路径（如果需要）
if sys.platform == "win32":
    cuda_path = r"C:\Program Files\NVIDIA\CUDNN\v9.1\bin\12.4"
    if os.path.exists(cuda_path):
        os.add_dll_directory(cuda_path)
        print(f"添加CUDA路径: {cuda_path}")

print("开始导入主控制台...")

# 运行主控制台
if __name__ == "__main__":
    try:
        from app.views.main_console import main
        print("✅ 成功导入main函数")
        print("启动应用...")
        main()
    except KeyboardInterrupt:
        print("用户中断")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
