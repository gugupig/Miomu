import sys
sys.path.insert(0, r'f:\Miomu\Miomu')

print("导入基础Qt模块...")
from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtCore import Qt, Signal, Slot, QThread, QTimer
print("✅ Qt模块导入成功")

print("导入应用模块...")
from app.data.script_data import ScriptData
print("✅ ScriptData")

from app.utils.character_color_manager import CharacterColorManager
print("✅ CharacterColorManager")

from app.models.script_table_model import ScriptTableModel
print("✅ ScriptTableModel")

from app.core.player import SubtitlePlayer
print("✅ SubtitlePlayer")

print("导入UI文件...")
try:
    from app.ui.ui_main_console_full import Ui_MainWindow
    print("✅ UI文件导入成功")
except Exception as e:
    print(f"❌ UI文件导入失败: {e}")

print("导入完成，现在测试main_console导入...")
from app.views.main_console import MainConsoleWindow
print("✅ MainConsoleWindow导入成功!")
