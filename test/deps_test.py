import sys
sys.path.insert(0, r'f:\Miomu\Miomu')

print("开始导入模块...")

try:
    from app.data.script_data import ScriptData
    print("✅ ScriptData 导入成功")
    
    from app.utils.character_color_manager import CharacterColorManager  
    print("✅ CharacterColorManager 导入成功")
    
    from app.models.script_table_model import ScriptTableModel
    print("✅ ScriptTableModel 导入成功")
    
    from app.core.player import SubtitlePlayer
    print("✅ SubtitlePlayer 导入成功")
    
    from app.views.subtitle_window import SubtitleWindow
    print("✅ SubtitleWindow 导入成功")
    
    from app.views.debug_window import DebugLogWindow
    print("✅ DebugLogWindow 导入成功")
    
    print("所有依赖模块导入成功!")
    
except Exception as e:
    print(f"❌ 导入错误: {e}")
    import traceback
    traceback.print_exc()
