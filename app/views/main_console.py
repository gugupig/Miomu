import sys
import os
import logging
import json
from typing import Optional, List
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

print("导入Qt模块...")
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QFileDialog, QStatusBar, QLabel, QMessageBox,
    QApplication, QProgressBar, QSplitter, QTextEdit, QTableView,
    QAbstractItemView, QMenu, QInputDialog, QDialog, QComboBox
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QTimer, QObject, QEvent
from PySide6.QtGui import QFont, QBrush, QColor, QKeySequence, QShortcut

print("导入UI文件...")
# 导入生成的UI文件
from app.ui.ui_main_console_full import Ui_MainWindow
from app.ui.ui_character_color_dialog import Ui_CharacterColorDialog
from app.ui.ui_style_manager_dialog import Ui_StyleManagerDialog
from app.ui.ui_character_filter_dialog import Ui_CharacterFilterDialog
print("✅ UI文件导入成功")

# 导入自定义委托
from app.views.character_delegate import CharacterDelegate

print("导入应用模块...")

from app.data.script_data import ScriptData
from app.core.player import SubtitlePlayer
from app.core.audio.audio_hub import AudioHub
from app.core.stt.whisper_engine import WhisperEngine
from app.core.stt.vosk_engine import VoskEngine
from app.core.aligner.Aligner import Aligner
from app.core.g2p.phonemizer_g2p import PhonemizerG2P
from app.core.g2p.g2p_manager import G2PManager, G2PEngineType
from app.core.engine_worker import EngineWorkerThread
from app.models.models import Cue
from app.models.script_table_model import ScriptTableModel
from app.views.subtitle_window import SubtitleWindow
from app.views.debug_window import DebugLogWindow
from app.views.playcontrol import PlayControlWindow
from app.views.character_color_dialog import CharacterColorDialog
from app.views.character_filter_dialog import CharacterFilterDialog
from app.ui.character_color_dialog import CharacterColorDialog as UICharacterColorDialog
from app.ui.style_manager_dialog import StyleManagerDialog
from app.ui.character_filter_dialog import CharacterFilterDialog as UICharacterFilterDialog
from app.utils.logging_handler import QtLogHandler
from app.utils.character_color_manager import CharacterColorManager


class LoadScriptThread(QThread):
    """专门用于加载和预处理剧本的后台线程"""
    progress_updated = Signal(int, str)  # 进度百分比, 状态消息
    script_loaded = Signal(object)  # ScriptData对象
    error_occurred = Signal(str)  # 错误消息
    
    def __init__(self, file_path: str, g2p_manager=None, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.script_data = None
        self.g2p_manager = g2p_manager
        
    def run(self):
        """在后台线程中执行加载和预处理"""
        try:
            self.progress_updated.emit(10, "正在初始化G2P转换器...")
            
            # 使用传入的G2P管理器或创建新的管理器
            if self.g2p_manager is not None:
                g2p_converter = self.g2p_manager.get_current_engine()
                engine_info = self.g2p_manager.get_current_engine_info()
                self.progress_updated.emit(20, f"使用 {engine_info['name']}")
            else:
                # 备用方案：创建新的G2P管理器
                from app.core.g2p.g2p_manager import G2PManager
                g2p_manager = G2PManager()
                g2p_converter = g2p_manager.get_best_available_engine()
                engine_info = g2p_manager.get_current_engine_info()
                self.progress_updated.emit(20, f"使用 {engine_info['name']}")
            
            self.progress_updated.emit(30, "正在使用增强版加载器...")
            
            # 创建ScriptData实例
            script_data = ScriptData()
            
            # 使用增强版加载器
            success = self._load_script_enhanced(script_data, self.file_path, g2p_converter)
            
            if success and script_data.cues:
                self.progress_updated.emit(100, f"成功加载 {len(script_data.cues)} 条台词")
                self.script_loaded.emit(script_data)
            else:
                self.error_occurred.emit("剧本加载失败或文件为空")
                
        except Exception as e:
            self.error_occurred.emit(f"加载剧本时出错: {str(e)}")
            
    def _load_script_enhanced(self, script_data: ScriptData, filepath: str, g2p_converter) -> bool:
        """使用增强版加载器"""
        try:
            from app.data.enhanced_script_loader import EnhancedScriptLoader
            
            # 创建增强版加载器
            loader = EnhancedScriptLoader(g2p_converter)
            
            self.progress_updated.emit(40, "检查meta词条...")
            
            # 加载剧本
            document, report = loader.load_script(filepath)
            
            self.progress_updated.emit(70, "验证数据格式...")
            
            # 更新ScriptData对象
            script_data.document = document
            script_data.cues = document.cues
            script_data.filepath = filepath
            script_data.load_report = report
            
            self.progress_updated.emit(90, "处理音素数据...")
            
            return True
            
        except Exception as e:
            # 如果增强版加载器失败，回退到基础加载器
            self.progress_updated.emit(50, f"增强版加载失败，使用基础加载器: {str(e)[:50]}...")
            return self._load_script_with_progress(script_data, filepath, g2p_converter)
            
    def _load_script_with_progress(self, script_data: ScriptData, filepath: str, g2p_converter) -> bool:
        """带进度反馈的加载函数"""
        import json
        
        script_data.filepath = filepath
        
        try:
            # 读取JSON文件
            with open(filepath, 'r', encoding='utf-8') as f:
                raw_cues = json.load(f).get("cues", [])
        except Exception as e:
            self.error_occurred.emit(f"读取文件失败: {e}")
            return False
            
        if not raw_cues:
            return False
            
        self.progress_updated.emit(40, f"找到 {len(raw_cues)} 条台词，开始G2P预处理...")
        
        # G2P预处理 - 批量处理
        all_lines = [r.get("line", "") for r in raw_cues]
        
        self.progress_updated.emit(50, "正在进行G2P转换...")
        all_phonemes = g2p_converter.batch_convert(all_lines)
        
        self.progress_updated.emit(80, "正在创建Cue对象...")
        
        # 创建Cue对象列表
        script_data.cues = []
        for i, (r, phoneme_str) in enumerate(zip(raw_cues, all_phonemes)):
            try:
                script_data.cues.append(Cue(
                    id=int(r["id"]),
                    character=r.get("character"),  # 支持 None
                    line=r["line"],
                    phonemes=phoneme_str,
                    character_cue_index=r.get("character_cue_index", -1),
                    translation=r.get("translation", {}),  # 支持字典格式
                    notes=r.get("notes", ""),
                    style=r.get("style", "default")
                ))
                
                # 更新进度
                if i % 10 == 0:  # 每10个更新一次进度
                    progress = 80 + (i / len(raw_cues)) * 15
                    self.progress_updated.emit(int(progress), f"处理中... {i+1}/{len(raw_cues)}")
                    
            except KeyError as e:
                logging.warning(f"字段缺失 {e} 在记录中: {r}")
                
        return True


class DynamicUIManager:
    """动态UI组件管理器 - 统一管理所有动态创建的UI元素"""
    
    def __init__(self, parent_window):
        self.parent = parent_window
        self.dynamic_components = {}  # 存储所有动态创建的组件
        self._missing_components = []  # 记录缺失的组件列表
        
    def register_component(self, name: str, component, description: str = ""):
        """注册动态组件"""
        self.dynamic_components[name] = {
            'component': component,
            'description': description,
            'created_dynamically': True
        }
        print(f"✅ 注册动态组件: {name} - {description}")
        
    def get_component(self, name: str):
        """获取组件"""
        if name in self.dynamic_components:
            return self.dynamic_components[name]['component']
        return None
        
    def setup_all_missing_components(self):
        """统一设置所有缺失的组件"""
        print("🔧 开始设置动态UI组件...")
        
        # 1. 设置G2P组件
        self._setup_g2p_components()
        
        # 2. 设置按钮组件
        self._setup_button_components()
        
        # 3. 设置状态栏组件
        self._setup_statusbar_components()
        
        # 4. 连接信号
        self._connect_dynamic_signals()
        
        print(f"✅ 动态UI组件设置完成，共创建 {len(self.dynamic_components)} 个组件")
        
    def _setup_g2p_components(self):
        """设置G2P相关组件"""
        print("  📝 设置G2P组件...")
        
        # 检查UI文件是否已包含G2P组件
        ui_has_g2p = (hasattr(self.parent, 'ui') and 
                     hasattr(self.parent.ui, 'g2pEngineCombo') and 
                     hasattr(self.parent.ui, 'g2pLanguageCombo'))
        
        if ui_has_g2p:
            # 使用UI文件中的组件
            self.parent.g2p_engine_combo = self.parent.ui.g2pEngineCombo
            self.parent.g2p_language_combo = self.parent.ui.g2pLanguageCombo
            self.parent.g2p_status_label = getattr(self.parent.ui, 'g2pStatusLabel', None)
            print("    ✅ 使用UI文件中的G2P组件")
        else:
            # 动态创建G2P组件
            g2p_engine_combo = QComboBox()
            g2p_engine_combo.setMinimumWidth(120)
            g2p_engine_combo.setToolTip("选择G2P转换引擎")
            
            g2p_language_combo = QComboBox()
            g2p_language_combo.setMinimumWidth(80)
            g2p_language_combo.setToolTip("选择目标语言")
            
            g2p_status_label = QLabel("就绪")
            g2p_status_label.setStyleSheet("color: green; font-weight: bold;")
            g2p_status_label.setToolTip("G2P引擎状态")
            
            # 注册到父窗口
            self.parent.g2p_engine_combo = g2p_engine_combo
            self.parent.g2p_language_combo = g2p_language_combo
            self.parent.g2p_status_label = g2p_status_label
            
            # 注册到管理器
            self.register_component("g2p_engine_combo", g2p_engine_combo, "G2P引擎选择器")
            self.register_component("g2p_language_combo", g2p_language_combo, "G2P语言选择器")
            self.register_component("g2p_status_label", g2p_status_label, "G2P状态标签")
            
            # 将组件添加到UI
            self._add_g2p_components_to_ui()
            
    def _add_g2p_components_to_ui(self):
        """将G2P组件添加到UI布局中"""
        try:
            if hasattr(self.parent, 'status_bar') and self.parent.status_bar:
                # 创建G2P组件容器
                g2p_widget = QWidget()
                g2p_layout = QHBoxLayout(g2p_widget)
                g2p_layout.setContentsMargins(5, 0, 5, 0)
                
                g2p_layout.addWidget(QLabel("G2P:"))
                g2p_layout.addWidget(self.parent.g2p_engine_combo)
                g2p_layout.addWidget(self.parent.g2p_language_combo)
                g2p_layout.addWidget(self.parent.g2p_status_label)
                
                # 添加到状态栏的永久区域
                self.parent.status_bar.addPermanentWidget(g2p_widget)
                self.register_component("g2p_widget", g2p_widget, "G2P组件容器")
                
                print("    ✅ G2P组件已添加到状态栏")
            else:
                print("    ⚠️ 无法添加G2P组件 - 状态栏不可用")
        except Exception as e:
            print(f"    ❌ 添加G2P组件失败: {e}")
            
    def _setup_button_components(self):
        """设置按钮组件"""
        print("  🔘 设置按钮组件...")
        
        # 定义所有可能需要的按钮及其属性
        button_definitions = [
            # 编辑模式按钮
            ('load_script_btn', '加载剧本', 'load_script', "从文件加载剧本"),
            ('save_script_btn', '保存剧本', 'save_script', "保存当前剧本到文件"),
            ('add_cue_btn', '添加台词', 'add_cue', "添加新的台词条目"),
            ('delete_cue_btn', '删除台词', 'delete_cue', "删除选中的台词"),
            ('duplicate_cue_btn', '复制台词', 'duplicate_cue', "复制选中的台词"),
            ('refresh_phonemes_btn', '刷新音素', 'refresh_phonemes', "重新生成所有音素"),
            ('add_language_btn', '添加语言', 'add_language_column', "添加新的语言列"),
            ('remove_language_btn', '移除语言', 'remove_language_column', "移除语言列"),
            ('manage_styles_btn', '管理样式', 'manage_styles', "管理文本样式"),
            
            # 剧场模式按钮
            ('load_script_theater_btn', '加载剧本', 'load_script', "在剧场模式加载剧本"),
            ('filter_by_character_btn', '按角色筛选', 'filter_by_character', "按角色筛选台词"),
            ('manage_character_colors_btn', '管理角色颜色', 'manage_character_colors', "管理角色颜色设置"),
            
            # 播放控制按钮
            ('start_btn', '播放控制', 'show_playcontrol_window', "打开播放控制窗口"),
            
            # 窗口控制按钮
            ('show_subtitle_btn', '显示字幕窗口', 'show_subtitle_window', "显示字幕显示窗口"),
            ('show_debug_btn', '调试窗口', 'show_debug_window', "显示调试信息窗口"),
        ]
        
        created_count = 0
        for btn_name, btn_text, method_name, tooltip in button_definitions:
            if not hasattr(self.parent, btn_name) or not getattr(self.parent, btn_name):
                # 动态创建按钮
                btn = QPushButton(btn_text)
                btn.setEnabled(False)  # 默认禁用，等待数据加载后启用
                btn.setToolTip(tooltip)
                
                # 设置按钮到父窗口
                setattr(self.parent, btn_name, btn)
                
                # 注册到管理器
                self.register_component(btn_name, btn, f"按钮: {btn_text}")
                created_count += 1
                
        print(f"    ✅ 动态创建了 {created_count} 个按钮")
        
    def _setup_statusbar_components(self):
        """设置状态栏组件"""
        print("  📊 设置状态栏组件...")
        
        # 状态标签
        if not hasattr(self.parent, 'status_label') or not self.parent.status_label:
            status_label = QLabel("就绪")
            status_label.setStyleSheet("color: #007ACC; font-weight: bold;")
            self.parent.status_label = status_label
            self.register_component("status_label", status_label, "主状态标签")
            
            if hasattr(self.parent, 'status_bar'):
                self.parent.status_bar.addWidget(status_label)
                
        # 对齐状态标签
        if not hasattr(self.parent, 'alignment_status') or not self.parent.alignment_status:
            alignment_status = QLabel("对齐器: 停止")
            alignment_status.setStyleSheet("color: #666; font-weight: normal;")
            self.parent.alignment_status = alignment_status
            self.register_component("alignment_status", alignment_status, "对齐状态标签")
            
            if hasattr(self.parent, 'status_bar'):
                self.parent.status_bar.addPermanentWidget(alignment_status)
                
        # 进度条（如果UI文件中没有）
        if not hasattr(self.parent, 'progress_bar') or not self.parent.progress_bar:
            progress_bar = QProgressBar()
            progress_bar.setVisible(False)  # 默认隐藏
            progress_bar.setMaximumWidth(200)
            self.parent.progress_bar = progress_bar
            self.register_component("progress_bar", progress_bar, "进度条")
            
            if hasattr(self.parent, 'status_bar'):
                self.parent.status_bar.addWidget(progress_bar)
                
        print("    ✅ 状态栏组件设置完成")
        
    def _connect_dynamic_signals(self):
        """连接动态创建组件的信号"""
        print("  🔗 连接动态组件信号...")
        
        # 按钮信号连接映射
        button_signal_mapping = {
            'load_script_btn': 'load_script',
            'save_script_btn': 'save_script',
            'add_cue_btn': 'add_cue',
            'delete_cue_btn': 'delete_cue',
            'duplicate_cue_btn': 'duplicate_cue',
            'refresh_phonemes_btn': 'refresh_phonemes',
            'add_language_btn': 'add_language_column',
            'remove_language_btn': 'remove_language_column',
            'manage_styles_btn': 'manage_styles',
            'load_script_theater_btn': 'load_script',
            'filter_by_character_btn': 'filter_by_character',
            'manage_character_colors_btn': 'manage_character_colors',
            'start_btn': 'show_playcontrol_window',
            'pause_btn': 'pause_alignment',
            'stop_btn': 'stop_alignment',
            'prev_btn': 'prev_cue',
            'next_btn': 'next_cue',
            'show_subtitle_btn': 'show_subtitle_window',
            'show_debug_btn': 'show_debug_window',
        }
        
        connected_count = 0
        for btn_name, method_name in button_signal_mapping.items():
            if (hasattr(self.parent, btn_name) and 
                hasattr(self.parent, method_name)):
                try:
                    btn = getattr(self.parent, btn_name)
                    method = getattr(self.parent, method_name)
                    
                    # 先断开可能存在的连接，避免重复连接
                    try:
                        btn.clicked.disconnect()
                    except:
                        pass  # 如果没有连接会抛异常，忽略
                        
                    btn.clicked.connect(method)
                    connected_count += 1
                except Exception as e:
                    print(f"    ⚠️ 信号连接失败: {btn_name} -> {method_name}: {e}")
                    
        # G2P组件信号连接
        if hasattr(self.parent, 'g2p_engine_combo') and hasattr(self.parent, 'on_g2p_engine_changed'):
            try:
                self.parent.g2p_engine_combo.currentTextChanged.disconnect()
            except:
                pass
            self.parent.g2p_engine_combo.currentTextChanged.connect(self.parent.on_g2p_engine_changed)
            connected_count += 1
            
        if hasattr(self.parent, 'g2p_language_combo') and hasattr(self.parent, 'on_g2p_language_changed'):
            try:
                self.parent.g2p_language_combo.currentTextChanged.disconnect()
            except:
                pass
            self.parent.g2p_language_combo.currentTextChanged.connect(self.parent.on_g2p_language_changed)
            connected_count += 1
            
        print(f"    ✅ 成功连接 {connected_count} 个组件信号")
        
    def connect_all_signals(self):
        """统一连接所有动态创建组件的信号 - 对外接口"""
        self._connect_dynamic_signals()
        
    def print_component_summary(self):
        """打印组件摘要信息"""
        print("\n📋 动态UI组件摘要:")
        print("=" * 50)
        
        categories = {
            'G2P组件': ['g2p_engine_combo', 'g2p_language_combo', 'g2p_status_label', 'g2p_widget'],
            '按钮组件': [name for name in self.dynamic_components.keys() if 'btn' in name],
            '状态栏组件': ['status_label', 'alignment_status', 'progress_bar'],
            '其他组件': []
        }
        
        for category, component_names in categories.items():
            if component_names:
                print(f"\n{category}:")
                for name in component_names:
                    if name in self.dynamic_components:
                        comp_info = self.dynamic_components[name]
                        print(f"  ✅ {name}: {comp_info['description']}")
                        
        print(f"\n总计: {len(self.dynamic_components)} 个动态组件")
        print("=" * 50)


class MainConsoleWindow(QMainWindow):
    """主控制台窗口"""
    
    def __init__(self):
        super().__init__()
        self.script_data = ScriptData()
        
        # G2P管理器
        self.g2p_manager = G2PManager()
        
        # 角色颜色管理器
        self.character_color_manager = CharacterColorManager()
        
        # 动态UI管理器 - 统一管理所有动态创建的UI组件
        self.dynamic_ui_manager = DynamicUIManager(self)
        
        self.script_model = ScriptTableModel(character_color_manager=self.character_color_manager)  # 编辑模式的数据模型
        self.theater_model = ScriptTableModel(character_color_manager=self.character_color_manager)  # 剧场模式的数据模型
        
        # 角色委托
        self.character_delegate = CharacterDelegate(self)
        
        self.player: Optional[SubtitlePlayer] = None
        self.subtitle_window: Optional[SubtitleWindow] = None
        self.debug_window: Optional[DebugLogWindow] = None
        self.playcontrol_window: Optional['PlayControlWindow'] = None  # 播放控制窗口
        self.worker_thread = EngineWorkerThread(g2p_manager=self.g2p_manager)
        self.load_thread: Optional[LoadScriptThread] = None  # 加载线程
        
        # 设置日志处理
        self.setup_logging()
        
        # 初始化UI（必须有UI文件骨架）
        self.init_ui_from_file()
            
        self.setup_signals()
        
        # 状态
        self._loading_script = False  # 防止重复加载剧本
        
    def setup_logging(self):
        """设置日志处理"""
        self.log_handler = QtLogHandler()
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.DEBUG)
        
    def init_ui_from_file(self):
        """从UI文件初始化界面 - 使用UI文件 + 动态组件补充的混合模式"""
        print("🎨 使用UI文件初始化界面...")
        
        try:
            self.ui = Ui_MainWindow()  # type: ignore
            self.ui.setupUi(self)
            print("  ✅ UI文件加载成功")
        except Exception as e:
            print(f"  ❌ UI文件加载失败: {e}")
            raise Exception(f"UI文件加载失败，无法继续: {e}")
        
        # 连接UI元素到类属性以保持兼容性
        self._map_ui_file_elements()
        
        # 使用动态UI管理器设置缺失的组件
        self.dynamic_ui_manager.setup_all_missing_components()
        
        # 设置表格模型和属性
        self._setup_table_models_and_properties()
        
        # 打印组件摘要
        self.dynamic_ui_manager.print_component_summary()
        
    def _map_ui_file_elements(self):
        """映射UI文件元素到类属性"""
        print("  🔗 映射UI文件元素...")
        
        # 基础窗口元素
        self.tab_widget = self.ui.tabWidget
        
        # 编辑模式标签页元素
        self.edit_tab = self.ui.editTab
        self.script_table = self.ui.scriptView
        self.script_view = self.script_table  # 别名，保持兼容性
        
        # 尝试映射UI文件中的按钮（如果存在）
        ui_button_mapping = {
            'load_script_btn': 'loadScriptButton',
            'save_script_btn': 'saveScriptButton',
            'add_cue_btn': 'addCueButton',
            'delete_cue_btn': 'deleteCueButton',
            'duplicate_cue_btn': 'duplicateCueButton',
            'refresh_phonemes_btn': 'refreshPhonemesButton',
            'add_language_btn': 'addLanguageButton',
            'remove_language_btn': 'removeLanguageButton',
            'manage_styles_btn': 'manageStylesButton',
            'load_script_theater_btn': 'loadScriptTheaterButton',
            'filter_by_character_btn': 'filterByCharacterButton',
            'manage_character_colors_btn': 'manageCharacterColorsButton',
            'start_btn': 'startButton',
            'pause_btn': 'pauseButton',
            'stop_btn': 'stopButton',
            'show_subtitle_btn': 'showSubtitleButton',
            'show_debug_btn': 'showDebugButton',
            'language_combo': 'languageComboBox',
        }
        
        for attr_name, ui_name in ui_button_mapping.items():
            if hasattr(self.ui, ui_name):
                setattr(self, attr_name, getattr(self.ui, ui_name))
                print(f"    ✅ 映射按钮: {attr_name} -> {ui_name}")
            else:
                # 标记为需要动态创建
                setattr(self, attr_name, None)
                print(f"    ⚪ 标记待创建: {attr_name}")
        
        # 剧场模式标签页元素
        self.theater_tab = self.ui.theaterTab
        self.theater_table = self.ui.theaterTable
        self.theater_view = self.theater_table  # 别名，保持兼容性
        self.play_btn = getattr(self, 'start_btn', None)  # 使用别名
        
        # 其他UI元素
        self.progress_bar = getattr(self.ui, 'progressBar', None)
        self.progress_label = getattr(self.ui, 'progressLabel', None)
        self.status_bar = self.ui.statusbar
        self.log_display = getattr(self.ui, 'logTextEdit', None)
        
        # 设置语言下拉菜单
        self.language_combo = getattr(self.ui, 'languageComboBox', None)
        
        # 如果是多选组件，连接信号
        if self.language_combo and hasattr(self.language_combo, 'selectionChanged'):
            self.language_combo.selectionChanged.connect(self.on_language_selection_changed)

        print("  ✅ UI元素映射完成")
        
    def _setup_table_models_and_properties(self):
        """设置表格模型和属性"""
        print("  📊 设置表格模型...")
        
        # 设置表格模型
        if hasattr(self, 'script_table') and self.script_table:
            self.script_table.setModel(self.script_model)
            
        if hasattr(self, 'theater_table') and self.theater_table:
            self.theater_table.setModel(self.theater_model)
        
        # 设置表格属性
        self.setup_table_properties()
        
        print("  ✅ 表格设置完成")
        
    def setup_g2p_components(self):
        """设置G2P组件（如果UI文件没有包含的话）"""
        # 检查UI文件是否已经包含了G2P组件
        if hasattr(self.ui, 'g2pEngineCombo') and hasattr(self.ui, 'g2pLanguageCombo'):
            # 使用UI文件中的组件
            self.g2p_engine_combo = self.ui.g2pEngineCombo
            self.g2p_language_combo = self.ui.g2pLanguageCombo
            self.g2p_status_label = getattr(self.ui, 'g2pStatusLabel', None)
        else:
            # UI文件中没有G2P组件，创建新的
            self.g2p_engine_combo = QComboBox()
            self.g2p_engine_combo.setMinimumWidth(120)
            
            self.g2p_language_combo = QComboBox()
            self.g2p_language_combo.setMinimumWidth(80)
            
            self.g2p_status_label = None  # 先设为None
            
            # 尝试将G2P组件添加到状态栏或工具栏
            self.add_g2p_components_to_ui()
            
        # 确保状态标签存在
        if not self.g2p_status_label:
            self.g2p_status_label = QLabel("就绪")
            self.g2p_status_label.setStyleSheet("color: green; font-weight: bold;")
            
    def add_g2p_components_to_ui(self):
        """将G2P组件添加到UI中"""
        try:
            # 创建状态标签（如果还没有的话）
            if not self.g2p_status_label:
                self.g2p_status_label = QLabel("就绪")
                self.g2p_status_label.setStyleSheet("color: green; font-weight: bold;")
            
            # 尝试在状态栏中添加G2P组件
            if hasattr(self, 'status_bar') and self.status_bar:
                # 创建一个widget来容纳G2P组件
                g2p_widget = QWidget()
                g2p_layout = QHBoxLayout(g2p_widget)
                g2p_layout.setContentsMargins(5, 0, 5, 0)
                
                g2p_layout.addWidget(QLabel("G2P:"))
                g2p_layout.addWidget(self.g2p_engine_combo)
                g2p_layout.addWidget(self.g2p_language_combo)
                g2p_layout.addWidget(self.g2p_status_label)
                
                # 添加到状态栏
                self.status_bar.addPermanentWidget(g2p_widget)
                
                print("✅ G2P组件已添加到状态栏")
            else:
                print("⚠️ 无法添加G2P组件到UI - 状态栏不可用")
        except Exception as e:
            print(f"❌ 添加G2P组件到UI失败: {e}")

    def setup_table_properties(self):
        """设置表格属性"""
        # 编辑模式表格设置
        if hasattr(self, 'script_table'):
            self.script_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.script_table.setAlternatingRowColors(True)
            header = self.script_table.horizontalHeader()
            if header:
                header.setStretchLastSection(True)
                header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            
            # 为角色列（第1列）设置下拉菜单委托
            if hasattr(self, 'character_delegate'):
                self.script_table.setItemDelegateForColumn(1, self.character_delegate)
                print("✅ 已为编辑模式角色列设置下拉菜单委托")
        
        # 剧场模式表格设置
        if hasattr(self, 'theater_table'):
            self.theater_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            # 禁用交替行颜色，以免干扰自定义高亮
            self.theater_table.setAlternatingRowColors(False)
            # 清除任何可能干扰自定义颜色的样式表
            self.theater_table.setStyleSheet("")
            header = self.theater_table.horizontalHeader()
            if header:
                header.setStretchLastSection(True)
                header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            
            # 禁用编辑与单击选中（仅用于剧场模式）
            try:
                self.theater_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
                self.theater_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
            except Exception:
                pass

            # 连接双击事件到字幕切换
            self.theater_table.doubleClicked.connect(self.on_theater_item_double_clicked)

            # 安装事件过滤器：拦截鼠标单击与方向键
            # 定义并绑定一次，避免被垃圾回收
            class _TheaterTableEventFilter(QObject):
                def __init__(self, parent, on_up, on_down):
                    super().__init__(parent)
                    self._on_up = on_up
                    self._on_down = on_down

                def eventFilter(self, obj, event):
                    et = event.type()
                    if et == QEvent.Type.MouseButtonPress or et == QEvent.Type.MouseButtonRelease:
                        # 禁用单击/释放造成的选中
                        return True
                    if et == QEvent.Type.MouseButtonDblClick:
                        # 允许双击继续传递（用于跳转行），编辑已被禁用
                        return False
                    if et == QEvent.Type.KeyPress:
                        key = event.key()
                        if key == Qt.Key.Key_Up:
                            if callable(self._on_up):
                                self._on_up()
                            return True
                        if key == Qt.Key.Key_Down:
                            if callable(self._on_down):
                                self._on_down()
                            return True
                    return False

            # 保存为实例属性，防止被回收
            self._theater_event_filter = _TheaterTableEventFilter(self, self.prev_subtitle, self.next_subtitle)
            try:
                self.theater_table.installEventFilter(self._theater_event_filter)
            except Exception:
                pass
        
    def setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+O 打开文件
        open_shortcut = QShortcut(QKeySequence.StandardKey.Open, self)
        open_shortcut.activated.connect(self.load_script)
        
        # F5 刷新
        refresh_shortcut = QShortcut(QKeySequence.StandardKey.Refresh, self)
        refresh_shortcut.activated.connect(self.refresh_display)
        
        # 字幕控制快捷键
        # 上箭头 - 上一条台词
        prev_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Up), self)
        prev_shortcut.activated.connect(self.prev_subtitle)
        
        # 下箭头 - 下一条台词
        next_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Down), self)
        next_shortcut.activated.connect(self.next_subtitle)
        
    def setup_signals(self):
        """设置信号连接"""
        # 工作线程信号
        self.worker_thread.status_changed.connect(self.update_status)
        self.worker_thread.error_occurred.connect(self.show_error)
        
        # 日志信号
        self.log_handler.emitter.message_written.connect(self.add_log_message)
        
        # 数据模型信号
        self.script_model.dataModified.connect(self.on_script_data_modified)
        self.script_model.validationError.connect(self.on_validation_error)
        
        # 使用动态UI管理器连接所有信号
        self.dynamic_ui_manager.connect_all_signals()
            
        # 设置G2P UI
        self.setup_g2p_ui()
            
    @Slot()
    def load_script(self):
        """加载剧本文件"""
        # 防止重复调用
        if hasattr(self, '_loading_script') and self._loading_script:
            return
            
        # 如果已有加载线程在运行，先停止它
        if self.load_thread and self.load_thread.isRunning():
            self.load_thread.quit()
            self.load_thread.wait()
            
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择剧本文件",
            "",
            "JSON 文件 (*.json);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        # 设置加载标志
        self._loading_script = True
        
        # 显示进度条
        if hasattr(self, 'progress_bar') and self.progress_bar:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)  # 确定进度
            self.progress_bar.setValue(0)
        
        # 禁用加载按钮，防止重复点击
        if hasattr(self, 'load_script_btn') and self.load_script_btn:
            self.load_script_btn.setEnabled(False)
        if hasattr(self, 'load_script_theater_btn') and self.load_script_theater_btn:
            self.load_script_theater_btn.setEnabled(False)
            
        self.update_status("正在加载剧本...")
        
        # 创建并启动加载线程
        self.load_thread = LoadScriptThread(file_path, self.g2p_manager, self)
        self.load_thread.progress_updated.connect(self.on_load_progress)
        self.load_thread.script_loaded.connect(self.on_script_loaded)
        self.load_thread.error_occurred.connect(self.on_load_error)
        self.load_thread.finished.connect(self.on_load_finished)
        
        self.load_thread.start()
        
    @Slot(int, str)
    def on_load_progress(self, progress: int, message: str):
        """处理加载进度更新"""
        if hasattr(self, 'progress_bar') and self.progress_bar:
            self.progress_bar.setValue(progress)
        self.update_status(message)
        
    @Slot(object)
    def on_script_loaded(self, script_data: ScriptData):
        """处理剧本加载完成"""
        try:
            # 更新本地script_data
            self.script_data = script_data
            
            # 更新编辑模式数据模型
            self.script_model.set_cues(self.script_data.cues)
            
            # 检查并设置翻译列
            self._setup_translation_columns()
            
            # 同步剧场模式数据模型
            self.sync_theater_model()
            
            # 创建播放器
            self.player = SubtitlePlayer(self.script_data.cues)
            # 注意：播放器的信号连接已移至播放控制窗口
            # 默认选中并显示第一行
            if self.script_data.cues:
                self.player.go(0, "Initial selection")
                # 高亮剧场模式第一行并滚动到可见
                try:
                    self.update_theater_highlight(0)
                except Exception:
                    pass
                # 同步到字幕屏幕（如果播放控制窗口已打开）
                self.sync_subtitle_to_playcontrol()
            
            # 启用相关按钮（安全检查）
            if hasattr(self, 'start_btn') and self.start_btn:
                self.start_btn.setEnabled(True)
            if hasattr(self, 'show_subtitle_btn') and self.show_subtitle_btn:
                self.show_subtitle_btn.setEnabled(False)  # 功能已迁移，永久禁用
                self.show_subtitle_btn.setText("已迁移到播放控制")
                self.show_subtitle_btn.setToolTip("字幕窗口功能已迁移到播放控制窗口中")
            if hasattr(self, 'save_script_btn') and self.save_script_btn:
                self.save_script_btn.setEnabled(True)
            if hasattr(self, 'add_cue_btn') and self.add_cue_btn:
                self.add_cue_btn.setEnabled(True)
            if hasattr(self, 'delete_cue_btn') and self.delete_cue_btn:
                self.delete_cue_btn.setEnabled(True)
            if hasattr(self, 'duplicate_cue_btn') and self.duplicate_cue_btn:
                self.duplicate_cue_btn.setEnabled(True)
            if hasattr(self, 'refresh_phonemes_btn') and self.refresh_phonemes_btn:
                self.refresh_phonemes_btn.setEnabled(True)
            if hasattr(self, 'add_language_btn') and self.add_language_btn:
                self.add_language_btn.setEnabled(True)
            if hasattr(self, 'remove_language_btn') and self.remove_language_btn:
                self.remove_language_btn.setEnabled(True)
            if hasattr(self, 'manage_styles_btn') and self.manage_styles_btn:
                self.manage_styles_btn.setEnabled(True)
            
            # 更新剧场模式按钮
            self._update_theater_buttons()
            
            # 导入角色到颜色管理器
            new_count = self.character_color_manager.import_characters_from_cues(self.script_data.cues)
            if new_count > 0:
                self.update_status(f"已加载 {len(self.script_data.cues)} 条台词，发现 {new_count} 个新角色")
            else:
                self.update_status(f"已加载 {len(self.script_data.cues)} 条台词")
            logging.info(f"成功加载剧本: {self.script_data.filepath}")
            
            # 更新角色委托中的角色列表
            self._update_character_delegate()
            
        except Exception as e:
            self.show_error(f"处理加载结果时出错: {str(e)}")
            logging.error(f"处理加载结果失败: {e}")
    
    def _setup_translation_columns(self):
        """根据meta信息设置翻译列"""
        try:
            # 检查是否有document和meta信息
            if not hasattr(self.script_data, 'document') or not self.script_data.document:
                logging.info("无document信息，跳过翻译列设置")
                return
                
            document = self.script_data.document
            if not document.meta or not document.meta.language:
                logging.info("无meta语言信息，跳过翻译列设置")
                return
            
            languages = document.meta.language
            logging.info(f"检测到语言: {languages}")
            
            # 如果只有一种语言（原语言），不显示翻译列
            if len(languages) <= 1:
                logging.info("只有一种语言，不显示翻译列")
                return
            
            # 从第二个语言开始是翻译语言
            translation_languages = languages[1:]
            logging.info(f"翻译语言: {translation_languages}")
            
            # 为每种翻译语言创建列
            for lang_code in translation_languages:
                # 获取语言显示名称
                lang_name = self._get_language_display_name(lang_code)
                
                # 检查是否已存在该翻译列，避免重复添加
                if lang_name in self.script_model.translation_columns:
                    logging.info(f"翻译列已存在，跳过: {lang_name} ({lang_code})")
                    continue
                
                # 提取该语言的翻译数据，并确保每个台词都有该语言的key
                translations = []
                for cue in self.script_data.cues:
                    # 确保台词有translation字典
                    if not hasattr(cue, 'translation') or cue.translation is None:
                        cue.translation = {}
                    
                    # 如果该语言的key不存在，自动添加并设置为空字符串
                    if lang_code not in cue.translation:
                        cue.translation[lang_code] = ""
                        logging.debug(f"为台词 {cue.id} 自动添加翻译语言 {lang_code} 的空值")
                    
                    translation = cue.translation[lang_code]
                    translations.append(translation)
                
                # 添加翻译列
                success = self.script_model.add_language_column(lang_name, lang_code, translations)
                if success:
                    logging.info(f"已添加翻译列: {lang_name} ({lang_code})")
                else:
                    logging.warning(f"添加翻译列失败: {lang_name} ({lang_code})")
            
            # 确保所有台词的翻译字典完整性
            self.script_model.ensure_translation_completeness()
            
        except Exception as e:
            logging.error(f"设置翻译列失败: {e}")
            
        # 更新多选语言下拉菜单
        self._update_language_combo()
            
    def _update_language_combo(self):
        """更新多选语言下拉菜单的选项"""
        try:
            # 检查languageComboBox是否存在
            if not hasattr(self, 'language_combo') or not self.language_combo:
                return
                
            language_combo = self.language_combo
            
            # 检查是否是多选组件
            is_multi_select = hasattr(language_combo, 'add_item') and hasattr(language_combo, 'setSelectedValues')
            
            # 检查是否有翻译语言
            has_translations = (hasattr(self.script_model, 'translation_columns') and 
                              self.script_model.translation_columns)
            
            if is_multi_select:
                # 清空现有选项
                language_combo.clear()
                
                if not has_translations:
                    language_combo.setEnabled(False)
                    language_combo.setPlaceholderText("暂无翻译语言")
                    return
                    
                # 添加翻译语言选项（排除源语言）
                translation_languages = self.script_model.translation_columns
                for display_name, lang_code in translation_languages.items():
                    language_combo.add_item(display_name, lang_code)
                    
                # 载入剧本后不自动选择任何语言，让用户手动选择
                language_combo.setSelectedValues([])  # 不选择任何语言
                language_combo.setEnabled(True)
                language_combo.setPlaceholderText("选择投屏语言...")
                
                logging.info(f"更新多选语言下拉菜单: {list(translation_languages.keys())}")
            else:
                # 标准下拉菜单的处理
                language_combo.clear()
                if has_translations:
                    language_combo.addItem("选择投屏语言...")
                    for display_name in self.script_model.translation_columns.keys():
                        language_combo.addItem(display_name)
                    language_combo.setEnabled(True)
                else:
                    language_combo.addItem("暂无翻译语言")
                    language_combo.setEnabled(False)
                    
                logging.info("更新标准语言下拉菜单")
            
        except Exception as e:
            logging.error(f"更新语言下拉菜单失败: {e}")
            
    def on_language_selection_changed(self, selected_lang_codes):
        """处理语言选择变化"""
        try:
            if not selected_lang_codes:
                # 如果没有选择任何语言，不显示任何翻译列
                self.theater_model.set_visible_languages(set())
            else:
                # 设置可见的语言列
                self.theater_model.set_visible_languages(set(selected_lang_codes))
                
            logging.info(f"剧场模式语言显示已更新: {selected_lang_codes}")
            
        except Exception as e:
            logging.error(f"处理语言选择变化失败: {e}")
            
    def _get_language_display_name(self, lang_code: str) -> str:
        """获取语言代码对应的显示名称"""
        language_names = {
            'en': '英语',
            'zh': '中文', 
            'fr': '法语',
            'de': '德语',
            'es': '西班牙语',
            'it': '意大利语',
            'ja': '日语',
            'ko': '韩语',
            'ru': '俄语',
            'pt': '葡萄牙语',
            'ar': '阿拉伯语',
            'hi': '印地语',
            'th': '泰语',
            'vi': '越南语'
        }
        
        # 处理带地区码的语言，如 fr-FR, en-US
        base_code = lang_code.split('-')[0].lower()
        return language_names.get(base_code, lang_code.upper())
            
    @Slot(str)
    def on_load_error(self, error_message: str):
        """处理加载错误"""
        self.show_error(error_message)
        logging.error(f"剧本加载失败: {error_message}")
        
    @Slot()
    def on_load_finished(self):
        """加载线程完成时的清理工作"""
        if hasattr(self, 'progress_bar') and self.progress_bar:
            self.progress_bar.setVisible(False)
        
        # 重新启用加载按钮
        if hasattr(self, 'load_script_btn') and self.load_script_btn:
            self.load_script_btn.setEnabled(True)
        if hasattr(self, 'load_script_theater_btn') and self.load_script_theater_btn:
            self.load_script_theater_btn.setEnabled(True)
        
        # 清除加载标志
        self._loading_script = False
        
        # 清理线程引用
        if self.load_thread:
            self.load_thread.deleteLater()
            self.load_thread = None
            
    def sync_theater_model(self):
        """自动同步剧场模式的数据模型与编辑模式"""
        if not self.script_data or not self.script_data.cues:
            return
            
        # 复制编辑模式的数据到剧场模式
        self.theater_model.set_cues(self.script_data.cues)
        
        # 同步翻译列
        if hasattr(self.script_model, 'translation_columns'):
            self.theater_model.translation_columns = self.script_model.translation_columns.copy()
        
        # 如果编辑模式有额外的列，也同步到剧场模式（为兼容性保留）
        if hasattr(self.script_model, 'extra_columns'):
            self.theater_model.extra_columns = self.script_model.extra_columns.copy()
        
        # 自动导入新角色到颜色管理器
        if hasattr(self, 'character_color_manager'):
            new_count = self.character_color_manager.import_characters_from_cues(self.script_data.cues)
            if new_count > 0:
                print(f"🎨 自动发现 {new_count} 个新角色，已分配颜色")
        
        # 调整剧场模式的列宽
        self.adjust_theater_column_widths()
        
        # 更新剧场模式按钮状态
        self._update_theater_buttons()
        
        # 更新语言选择下拉菜单
        self._update_language_combo()
        
        # 更新角色委托
        self._update_character_delegate()
        
        print("🔄 自动同步编辑模式数据到剧场模式完成")
        
    def adjust_theater_column_widths(self):
        """调整剧场模式的列宽"""
        header = self.theater_view.horizontalHeader()
        column_count = self.theater_model.columnCount()
        
        if column_count > 0:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        if column_count > 1:
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 角色
        if column_count > 2:
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)            # 主要台词
        
    def adjust_theater_column_widths(self):
        """调整剧场模式的列宽"""
        header = self.theater_view.horizontalHeader()
        column_count = self.theater_model.columnCount()
        
        if column_count > 0:
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        if column_count > 1:
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 角色
        if column_count > 2:
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)            # 主要台词
        
        # 其他语言列设置为自适应内容
        for col in range(3, column_count):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
                    
    @Slot()
    def on_script_item_double_clicked(self, item):
        """编辑模式表格项双击事件"""
        row = item.row()
        if 0 <= row < len(self.script_data.cues):
            cue = self.script_data.cues[row]
            # 这里可以添加编辑对话框
            logging.info(f"编辑台词: {cue.id} - {cue.line}")
            
    @Slot()
    def on_theater_item_clicked(self, index):
        """剧场模式表格项点击事件"""
        row = index.row()
        if self.player and 0 <= row < len(self.script_data.cues):
            cue = self.script_data.cues[row]
            self.player.go_by_cue_obj(cue)
            logging.info(f"手动跳转到台词: {cue.id}")
            
    @Slot()
    def show_subtitle_window(self):
        """显示字幕窗口 - 已禁用，功能已迁移到PlayControl"""
        QMessageBox.information(
            self, 
            "功能迁移", 
            "字幕窗口功能已迁移到播放控制窗口中。\n\n请使用以下方式显示字幕：\n"
            "1. 点击'播放控制'按钮打开播放控制窗口\n"
            "2. 在播放控制窗口中使用字幕相关功能"
        )
        return
        
    @Slot()
    def show_debug_window(self):
        """显示调试窗口"""
        if self.debug_window is None:
            self.debug_window = DebugLogWindow(self)
            self.log_handler.emitter.message_written.connect(
                self.debug_window.add_log_message
            )
            
        self.debug_window.show()
        self.debug_window.raise_()
        self.debug_window.activateWindow()
        
    @Slot()
    def show_playcontrol_window(self):
        """显示播放控制窗口"""
        if not self.script_data or not self.script_data.cues:
            self.show_error("请先加载剧本")
            return
            
        if self.playcontrol_window is None:
            self.playcontrol_window = PlayControlWindow(
                script_data=self.script_data,
                g2p_manager=self.g2p_manager,
                parent=self
            )
        else:
            # 如果窗口已存在，更新剧本数据
            self.playcontrol_window.set_script_data(self.script_data)
            
        self.playcontrol_window.show()
        self.playcontrol_window.raise_()
        self.playcontrol_window.activateWindow()
        
    @Slot()
    def refresh_display(self):
        """刷新显示"""
        if self.script_data.cues:
            # 编辑模式使用数据模型，会自动刷新
            self.script_model.set_cues(self.script_data.cues)
            # 剧场模式也使用数据模型，同步刷新
            self.sync_theater_model()
            self.update_status("显示已刷新")
            
    @Slot(str)
    def update_status(self, message: str):
        """更新状态栏"""
        # 确保状态标签存在
        if hasattr(self, 'status_label') and self.status_label:
            self.status_label.setText(message)
        elif hasattr(self, 'status_bar') and self.status_bar:
            # 如果没有状态标签，直接使用状态栏显示消息
            self.status_bar.showMessage(message, 3000)  # 显示3秒
        else:
            # 最后的备用方案，输出到日志
            print(f"Status: {message}")
            if hasattr(self, 'log_display') and self.log_display:
                self.log_display.append(f"[STATUS] {message}")
                
    @Slot(str)
    def show_error(self, message: str):
        """显示错误消息"""
        QMessageBox.critical(self, "错误", message)
        logging.error(message)
        
    @Slot(str, int)
    def add_log_message(self, message: str, level: int):
        """添加日志消息到实时显示"""
        if level >= logging.INFO:  # 只显示INFO及以上级别
            if hasattr(self, 'log_display') and self.log_display:
                self.log_display.append(message)
                # 自动滚动到底部
                scrollbar = self.log_display.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
            
    # === 编辑模式新增方法 ===
    
    @Slot()
    def save_script(self):
        """保存剧本 - 弹出文件对话框选择保存路径"""
        if not self.script_data.cues:
            self.show_error("没有可保存的剧本数据")
            return
        
        # 从模型同步数据到script_data
        self.script_data.cues = self.script_model.get_cues()
        
        # 检查是否有角色名为空的台词
        empty_character_rows = []
        for i, cue in enumerate(self.script_data.cues):
            if not cue.character or not cue.character.strip():
                empty_character_rows.append(i + 1)  # 行号从1开始
                
        if empty_character_rows:
            # 如果有空角色名，显示错误信息
            if len(empty_character_rows) == 1:
                error_msg = f"第 {empty_character_rows[0]} 行的角色名为空，请填写后再保存。"
            elif len(empty_character_rows) <= 5:
                rows_str = "、".join(map(str, empty_character_rows))
                error_msg = f"第 {rows_str} 行的角色名为空，请填写后再保存。"
            else:
                rows_str = "、".join(map(str, empty_character_rows[:5]))
                error_msg = f"第 {rows_str} 等 {len(empty_character_rows)} 行的角色名为空，请填写后再保存。"
                
            QMessageBox.warning(
                self,
                "保存失败",
                error_msg + "\n\n提示：您可以双击角色列的单元格来编辑角色名。"
            )
            
            # 定位到第一个有问题的行
            if hasattr(self, 'script_table') and self.script_table:
                first_empty_row = empty_character_rows[0] - 1  # 转回0基索引
                self.script_table.selectRow(first_empty_row)
                self.script_table.scrollTo(self.script_model.index(first_empty_row, 1))  # 滚动到角色列
                
            return
        
        # 弹出文件保存对话框
        from PySide6.QtWidgets import QFileDialog
        from pathlib import Path
        
        # 设置默认保存路径和文件名
        current_file = self.script_data.filepath
        if current_file:
            # 如果有当前文件路径，使用相同目录和文件名
            default_path = current_file
        else:
            # 如果没有当前文件，使用scripts目录
            scripts_dir = Path("scripts")
            scripts_dir.mkdir(exist_ok=True)
            default_path = str(scripts_dir / "saved_script.json")
        
        # 显示保存对话框
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存剧本文件",
            default_path,
            "JSON 文件 (*.json);;所有文件 (*.*)"
        )
        
        if not file_path:
            # 用户取消了保存
            return
        
        # 确保文件扩展名为.json
        if not file_path.lower().endswith('.json'):
            file_path += '.json'
        
        try:
            # 重新计算序号以确保数据一致性
            self._reindex_all_cues()
            
            # 再次同步数据
            self.script_data.cues = self.script_model.get_cues()
            
            # 保存到指定文件
            success = self.script_data.save_to_file(file_path)
            
            if success:
                self.script_model.mark_saved()
                self.update_status(f"剧本已保存到: {file_path}")
                logging.info(f"剧本已保存到: {file_path}")
                
                # 如果保存到了新路径，询问是否要将此文件设为当前工作文件
                if file_path != current_file:
                    from PySide6.QtWidgets import QMessageBox
                    reply = QMessageBox.question(
                        self,
                        "设置工作文件",
                        f"剧本已保存到新位置：\n{file_path}\n\n是否要将此文件设为当前工作文件？",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.Yes
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        self.script_data.filepath = file_path
                        logging.info(f"工作文件路径已更新为: {file_path}")
            else:
                self.show_error("保存剧本失败")
                
        except Exception as e:
            self.show_error(f"保存剧本失败: {str(e)}")
            logging.error(f"保存剧本失败: {e}")
            
    @Slot()
    def add_cue(self):
        """添加新台词 - 在当前选中行下方插入空行"""
        try:
            # 获取当前选中的行
            current_row = -1
            if hasattr(self, 'script_table') and self.script_table:
                selection = self.script_table.selectionModel()
                if selection and selection.hasSelection():
                    selected_indexes = selection.selectedRows()
                    if selected_indexes:
                        current_row = selected_indexes[0].row()
            
            # 确定插入位置
            insert_index = current_row + 1 if current_row >= 0 else len(self.script_data.cues)
            
            # 调用模型的添加方法，插入空台词
            success = self.script_model.add_cue_at_position(
                character="",  # 空角色名，需要用户填写
                line="",       # 空台词内容，需要用户填写
                index=insert_index
            )
            
            if success:
                # 重新计算所有ID和角色序号
                self._reindex_all_cues()
                
                # 选中新插入的行
                if hasattr(self, 'script_table') and self.script_table:
                    new_index = self.script_model.index(insert_index, 0)
                    self.script_table.selectRow(insert_index)
                    self.script_table.scrollTo(new_index)
                
                self.update_status(f"已在第 {insert_index + 1} 行插入新台词，请填写角色和内容")
                logging.info(f"在位置 {insert_index} 插入新的空台词")
            else:
                self.show_error("添加台词失败")
                
        except Exception as e:
            self.show_error(f"添加台词时出错: {str(e)}")
            logging.error(f"添加台词失败: {e}")
            
    @Slot()
    def delete_cue(self):
        """删除选中的台词"""
        # 检查是否有数据
        if not self.script_data.cues:
            self.show_error("没有可删除的台词数据")
            return
            
        # 检查是否有选中的行
        if not hasattr(self, 'script_table') or not self.script_table:
            self.show_error("表格组件不可用")
            return
            
        selection = self.script_table.selectionModel()
        if not selection or not selection.hasSelection():
            self.show_error("请先选择要删除的台词")
            return
            
        # 获取选中的行
        selected_rows = []
        selected_cues_info = []  # 用于显示确认信息
        
        for index in selection.selectedRows():
            row = index.row()
            selected_rows.append(row)
            
            # 获取台词信息用于确认对话框
            if 0 <= row < len(self.script_data.cues):
                cue = self.script_data.cues[row]
                cue_info = f"第{row+1}行: {cue.character or '(无角色)'} - {cue.line[:20]}{'...' if len(cue.line) > 20 else ''}"
                selected_cues_info.append(cue_info)
            
        if not selected_rows:
            return
            
        # 构建确认删除的详细信息
        if len(selected_rows) == 1:
            confirm_message = f"确定要删除以下台词吗？\n\n{selected_cues_info[0]}"
        else:
            if len(selected_cues_info) <= 5:
                cues_text = "\n".join(selected_cues_info)
            else:
                cues_text = "\n".join(selected_cues_info[:5]) + f"\n... 以及其他 {len(selected_cues_info) - 5} 条台词"
            confirm_message = f"确定要删除以下 {len(selected_rows)} 条台词吗？\n\n{cues_text}"
            
        # 确认删除
        reply = QMessageBox.question(
            self, 
            "确认删除",
            confirm_message + "\n\n注意：删除后将自动重新计算所有台词的序号。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No  # 默认选择"否"，更安全
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        try:
            # 记录删除前的总数
            original_count = len(self.script_data.cues)
            
            # 从后往前删除，避免索引问题
            selected_rows.sort(reverse=True)
            deleted_count = 0
            deleted_characters = set()  # 记录被删除台词的角色
            
            for row in selected_rows:
                if 0 <= row < len(self.script_data.cues):
                    # 记录被删除台词的角色信息
                    cue = self.script_data.cues[row]
                    if cue.character:
                        deleted_characters.add(cue.character)
                    
                    # 删除台词
                    if self.script_model.remove_cue(row):
                        deleted_count += 1
                        
            if deleted_count > 0:
                # 重新计算所有ID和角色序号
                self._reindex_all_cues()
                
                # 智能选择删除后的行
                self._smart_select_after_deletion(selected_rows, original_count)
                
                # 更新角色委托（因为可能删除了某些角色的所有台词）
                self._update_character_delegate()
                
                # 构建状态消息
                status_msg = f"已删除 {deleted_count} 条台词"
                if deleted_characters:
                    char_list = "、".join(sorted(deleted_characters))
                    if len(char_list) > 30:
                        char_list = char_list[:30] + "..."
                    status_msg += f"（涉及角色: {char_list}）"
                
                self.update_status(status_msg)
                logging.info(f"删除了 {deleted_count} 条台词，涉及角色: {deleted_characters}")
            else:
                self.show_error("删除操作失败，没有台词被删除")
                
        except Exception as e:
            self.show_error(f"删除台词时出错: {str(e)}")
            logging.error(f"删除台词失败: {e}")
            
    def _smart_select_after_deletion(self, deleted_rows: list, original_count: int):
        """删除后的智能选择逻辑"""
        try:
            if not hasattr(self, 'script_table') or not self.script_table:
                return
                
            current_count = len(self.script_data.cues)
            if current_count == 0:
                # 如果删除后没有台词了，不需要选择
                return
                
            # 找到最小的删除行号
            min_deleted_row = min(deleted_rows)
            
            # 选择逻辑：
            # 1. 如果删除的是最后几行，选择新的最后一行
            # 2. 否则选择删除位置的下一行（现在已经上移了）
            if min_deleted_row >= current_count:
                # 删除的是最后几行，选择新的最后一行
                new_selection_row = current_count - 1
            else:
                # 选择删除位置的当前行（原来的下一行已经上移到这个位置）
                new_selection_row = min_deleted_row
                
            # 确保选择行在有效范围内
            new_selection_row = max(0, min(new_selection_row, current_count - 1))
            
            # 选中新行
            self.script_table.selectRow(new_selection_row)
            
            # 滚动到选中行
            new_index = self.script_model.index(new_selection_row, 0)
            self.script_table.scrollTo(new_index)
            
            logging.debug(f"删除后智能选择第 {new_selection_row + 1} 行")
            
        except Exception as e:
            logging.error(f"删除后智能选择失败: {e}")
            
    @Slot()
    def duplicate_cue(self):
        """复制选中的台词"""
        selection = self.script_view.selectionModel()
        if not selection or not selection.hasSelection():
            self.show_error("请先选择要复制的台词")
            return
            
        selected_indexes = selection.selectedRows()
        if not selected_indexes:
            return
            
        # 只复制第一个选中的台词
        row = selected_indexes[0].row()
        success = self.script_model.duplicate_cue(row)
        
        if success:
            self.update_status("已复制台词")
        else:
            self.show_error("复制台词失败")
            
    @Slot()
    def refresh_phonemes(self):
        """刷新所有台词的音素"""
        if not self.script_data.cues:
            return
            
        try:
            # 使用G2P管理器获取当前引擎
            g2p_converter = self.g2p_manager.get_current_engine()
                
            # 刷新音素
            self.script_model.refresh_phonemes(g2p_converter)
            self.update_status("音素已刷新")
            
        except Exception as e:
            self.show_error(f"刷新音素失败: {str(e)}")
            logging.error(f"刷新音素失败: {e}")
            
    @Slot()
    def show_edit_context_menu(self, position):
        """显示编辑模式右键菜单"""
        index = self.script_view.indexAt(position)
        
        menu = QMenu(self)
        
        if index.isValid():
            # 有选中项时的菜单
            add_action = menu.addAction("添加台词")
            add_action.triggered.connect(self.add_cue)
            
            delete_action = menu.addAction("删除台词")
            delete_action.triggered.connect(self.delete_cue)
            
            duplicate_action = menu.addAction("复制台词")
            duplicate_action.triggered.connect(self.duplicate_cue)
            
            menu.addSeparator()
            
            # 批量操作菜单
            batch_menu = menu.addMenu("批量操作")
            
            refresh_phonemes_action = batch_menu.addAction("刷新音素")
            refresh_phonemes_action.triggered.connect(self.refresh_phonemes)
            
            # 批量修改角色名称
            batch_character_action = batch_menu.addAction("批量修改角色")
            batch_character_action.triggered.connect(self.batch_modify_character)
            
        else:
            # 空白区域菜单
            add_action = menu.addAction("添加台词")
            add_action.triggered.connect(self.add_cue)
            
        menu.exec_(self.script_view.mapToGlobal(position))
        
    @Slot()
    def batch_modify_character(self):
        """批量修改角色名称"""
        old_character, ok = QInputDialog.getText(self, "批量修改", "要替换的角色名称:")
        if not ok or not old_character.strip():
            return
            
        new_character, ok = QInputDialog.getText(self, "批量修改", "新的角色名称:")
        if not ok or not new_character.strip():
            return
            
        count = self.script_model.batch_update_character(old_character.strip(), new_character.strip())
        if count > 0:
            self.update_status(f"已更新 {count} 条台词的角色名称")
        else:
            self.update_status("没有找到匹配的角色名称")
            
    @Slot()
    def on_script_selection_changed(self):
        """编辑模式选择变化"""
        selection = self.script_view.selectionModel()
        has_selection = selection and selection.hasSelection()
        
        # 根据选择状态启用/禁用按钮
        self.delete_cue_btn.setEnabled(has_selection)
        self.duplicate_cue_btn.setEnabled(has_selection)
        
    @Slot()
    def on_script_data_modified(self):
        """数据模型修改时的响应"""
        # 更新窗口标题显示修改状态
        title = "Miomu - 剧本对齐控制台"
        if self.script_model.is_modified():
            title += " *"
        self.setWindowTitle(title)
        
        # 同步数据到script_data（用于剧场模式）
        self.script_data.cues = self.script_model.get_cues()
        
        # 实时同步到剧场模式
        self.sync_theater_model()
        
    @Slot(str, int, int)
    def on_validation_error(self, message: str, row: int, column: int):
        """处理数据验证错误"""
        self.show_error(f"数据验证错误 (行{row+1}, 列{column+1}): {message}")
        
        # 定位到错误位置
        error_index = self.script_model.index(row, column)
        self.script_view.setCurrentIndex(error_index)
        self.script_view.scrollTo(error_index)
        
    # === 多语言支持方法 ===
    
    @Slot()
    def add_language_column(self):
        """添加语言列 - 从epitran支持的语言列表中选择"""
        
        # 检查是否有剧本数据
        if not self.script_data.cues:
            QMessageBox.information(self, "提示", "请先加载剧本")
            return
        
        # 获取epitran支持的语言列表
        try:
            from app.core.g2p.g2p_manager import G2PEngineType
            epitran_languages = self.g2p_manager.get_engine_languages(G2PEngineType.EPITRAN)
        except Exception as e:
            logging.error(f"获取epitran语言列表失败: {e}")
            QMessageBox.warning(self, "错误", "无法获取支持的语言列表")
            return
        
        # 检查是否已存在
        if hasattr(self.script_model, 'get_language_columns'):
            existing_languages = self.script_model.get_language_columns()
        else:
            existing_languages = []
        
        # 过滤掉已存在的语言
        available_languages = []
        available_codes = {}
        for display_name, lang_code in epitran_languages.items():
            if display_name not in existing_languages:
                available_languages.append(display_name)
                available_codes[display_name] = lang_code
        
        if not available_languages:
            QMessageBox.information(self, "提示", "所有支持的语言都已添加")
            return
        
        # 显示语言选择对话框
        language_name, ok = QInputDialog.getItem(
            self, "添加翻译语言", 
            "请选择要添加的翻译语言:",
            available_languages, 0, False
        )
        
        if not ok or not language_name:
            return
        
        lang_code = available_codes[language_name]
        
        try:
            # 1. 更新meta中的语言列表
            if hasattr(self.script_data, 'document') and self.script_data.document and self.script_data.document.meta:
                meta = self.script_data.document.meta
                if not meta.language:
                    meta.language = []
                
                # 检查语言代码是否已存在于meta中
                if lang_code not in meta.language:
                    meta.language.append(lang_code)
                    logging.info(f"已将语言 {lang_code} 添加到meta.language")
                else:
                    logging.info(f"语言 {lang_code} 已存在于meta.language中")
            
            # 2. 为每条台词的translation添加对应的key
            for cue in self.script_data.cues:
                # 确保台词有translation字典
                if not hasattr(cue, 'translation') or cue.translation is None:
                    cue.translation = {}
                
                # 添加新语言的空值
                if lang_code not in cue.translation:
                    cue.translation[lang_code] = ""
                    logging.debug(f"为台词 {cue.id} 添加语言 {lang_code} 的空值")
            
            # 3. 添加到编辑模式表格
            if hasattr(self.script_model, 'add_language_column'):
                # 准备翻译数据（都是空字符串）
                translations = [""] * len(self.script_data.cues)
                
                success = self.script_model.add_language_column(language_name, lang_code, translations)
                
                if success:
                    # 4. 同步到剧场模式
                    self.sync_theater_model()
                    
                    # 5. 标记数据已修改
                    self.script_model._modified = True
                    self.script_model.dataModified.emit()
                    
                    # 6. 更新状态
                    self.update_status(f"已添加翻译语言: {language_name} ({lang_code})")
                    logging.info(f"成功添加翻译语言: {language_name} ({lang_code})")
                    
                    # 7. 确保翻译数据完整性
                    self.script_model.ensure_translation_completeness()
                    
                else:
                    QMessageBox.warning(self, "错误", "添加语言列失败")
            else:
                QMessageBox.information(self, "提示", "当前版本的ScriptTableModel不支持多语言功能")
                
        except Exception as e:
            error_msg = f"添加翻译语言失败: {str(e)}"
            logging.error(error_msg)
            QMessageBox.critical(self, "错误", error_msg)
            
    @Slot()
    def remove_language_column(self):
        """移除语言列"""
        if not hasattr(self.script_model, 'get_language_columns'):
            QMessageBox.information(self, "提示", "当前版本的ScriptTableModel不支持多语言功能")
            return
            
        available_languages = self.script_model.get_language_columns()
        
        if not available_languages:
            QMessageBox.information(self, "提示", "没有可移除的语言列")
            return
            
        language_name, ok = QInputDialog.getItem(
            self, "移除语言", "选择要移除的语言:", 
            available_languages, 0, False
        )
        
        if not ok:
            return
            
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除语言列 '{language_name}' 吗？\n这将删除所有该语言的翻译数据。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # 从编辑模式移除
        if hasattr(self.script_model, 'remove_language_column'):
            success = self.script_model.remove_language_column(language_name)
            
            if success:
                # 同步到剧场模式
                self.sync_theater_model()
                self.update_status(f"已移除语言列: {language_name}")
            else:
                QMessageBox.warning(self, "错误", "移除语言列失败")
    
    # === 新增功能方法 ===
    
    @Slot()
    def manage_styles(self):
        """管理样式"""
        QMessageBox.information(self, "功能开发中", "样式管理功能正在开发中，敬请期待！")
    
    @Slot()
    def filter_by_character(self):
        """按角色筛选台词"""
        if not self.script_data.cues:
            QMessageBox.information(self, "提示", "没有数据可筛选")
            return
        
        # 获取所有角色
        all_characters = self.theater_model.get_all_characters()
        if not all_characters:
            QMessageBox.information(self, "提示", "没有找到任何角色")
            return
        
        # 获取当前筛选状态
        current_filter = getattr(self.theater_model, '_filtered_characters', None)
        selected_characters = current_filter if current_filter is not None else all_characters
        
        # 打开筛选对话框
        dialog = CharacterFilterDialog(all_characters, selected_characters, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected = dialog.get_selected_characters()
            
            if len(selected) == len(all_characters):
                # 全选状态，清除筛选
                self.theater_model.clear_character_filter()
                self.update_status("已清除角色筛选")
            else:
                # 应用筛选
                self.theater_model.set_character_filter(selected)
                self.update_status(f"已筛选显示 {len(selected)} 个角色的台词")
    
    @Slot()
    def manage_character_colors(self):
        """管理角色颜色"""
        dialog = CharacterColorDialog(self.character_color_manager, self)
        dialog.colors_updated.connect(self._on_character_colors_updated)
        dialog.exec()
    
    @Slot()
    def _on_character_colors_updated(self):
        """角色颜色更新时的处理"""
        self.update_status("角色颜色配置已更新")
    
    def _update_theater_buttons(self):
        """更新剧场模式按钮状态"""
        has_data = bool(self.script_data and self.script_data.cues)
        
        # 安全地更新按钮状态，检查按钮是否存在
        if hasattr(self, 'filter_by_character_btn') and self.filter_by_character_btn:
            self.filter_by_character_btn.setEnabled(has_data)
            
        if hasattr(self, 'manage_character_colors_btn') and self.manage_character_colors_btn:
            self.manage_character_colors_btn.setEnabled(has_data)
            
        if hasattr(self, 'language_combo') and self.language_combo:
            self.language_combo.setEnabled(has_data)
            
        if hasattr(self, 'start_btn') and self.start_btn:
            self.start_btn.setEnabled(has_data)  # 现在只需要检查是否有数据
            
        if hasattr(self, 'show_subtitle_btn') and self.show_subtitle_btn:
            self.show_subtitle_btn.setEnabled(False)  # 功能已迁移，永久禁用
            self.show_subtitle_btn.setText("已迁移到播放控制")
            self.show_subtitle_btn.setToolTip("字幕窗口功能已迁移到播放控制窗口中")
            
    @Slot()
    def show_character_color_dialog(self):
        """显示角色颜色管理对话框"""
        if USE_UI_FILE:
            try:
                dialog = UICharacterColorDialog(self.character_color_manager, self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    # 刷新表格显示
                    if hasattr(self.script_model, 'layoutChanged'):
                        self.script_model.layoutChanged.emit()
                    if hasattr(self.theater_model, 'layoutChanged'):
                        self.theater_model.layoutChanged.emit()
            except Exception as e:
                logging.error(f"显示角色颜色对话框时出错: {e}")
                QMessageBox.warning(self, "错误", f"无法打开角色颜色对话框: {e}")
        else:
            # 回退到简单对话框
            from PySide6.QtWidgets import QColorDialog
            color = QColorDialog.getColor(parent=self)
            if color.isValid():
                logging.info(f"选择了颜色: {color.name()}")
    
    @Slot()
    def show_style_manager_dialog(self):
        """显示样式管理对话框"""
        if USE_UI_FILE:
            try:
                dialog = StyleManagerDialog(self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    logging.info("样式管理完成")
            except Exception as e:
                logging.error(f"显示样式管理对话框时出错: {e}")
                QMessageBox.information(self, "样式管理", "样式管理功能暂不可用")
        else:
            QMessageBox.information(self, "样式管理", "样式管理功能需要UI文件支持")
    
    @Slot()
    def show_character_filter_dialog(self):
        """显示角色过滤对话框"""
        if USE_UI_FILE:
            try:
                # 获取所有角色
                all_characters = set()
                if hasattr(self.script_data, 'cues'):
                    for cue in self.script_data.cues:
                        if hasattr(cue, 'character') and cue.character:
                            all_characters.add(cue.character)
                
                dialog = UICharacterFilterDialog(all_characters, set(), self)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    logging.info("角色过滤设置完成")
            except Exception as e:
                logging.error(f"显示角色过滤对话框时出错: {e}")
                QMessageBox.information(self, "角色过滤", "角色过滤功能暂不可用")
        else:
            QMessageBox.information(self, "角色过滤", "角色过滤功能需要UI文件支持")
    
    # ==================== 字幕控制功能 ====================
    
    @Slot()
    def prev_subtitle(self):
        """上一条字幕"""
        if self.player and self.player.current_index > 0:
            self.player.prev()
            self.sync_subtitle_to_playcontrol()
            logging.info(f"切换到上一条字幕: {self.player.current_index}")
    
    @Slot()
    def next_subtitle(self):
        """下一条字幕"""
        if self.player and self.player.current_index < self.player.total_cues - 1:
            self.player.next()
            self.sync_subtitle_to_playcontrol()
            logging.info(f"切换到下一条字幕: {self.player.current_index}")
    
    def sync_subtitle_to_playcontrol(self):
        """同步字幕切换到PlayControl的字幕窗口"""
        # 无论是否有PlayControl窗口，都更新剧场模式高亮
        if self.player:
            self.update_table_selection(self.player.current_index)
        
        # 如果有PlayControl窗口，也同步到那里
        if self.playcontrol_window and self.player and self.player.current_cue:
            # 使用PlayControl的统一字幕切换接口
            if hasattr(self.playcontrol_window, 'unified_subtitle_switch'):
                self.playcontrol_window.unified_subtitle_switch(self.player.current_cue)
    
    @Slot()
    def on_theater_item_double_clicked(self, index):
        """剧场模式表格项双击事件 - 跳转到指定字幕"""
        row = index.row()
        if self.player and 0 <= row < len(self.script_data.cues):
            cue = self.script_data.cues[row]
            self.player.go_by_cue_obj(cue)
            self.sync_subtitle_to_playcontrol()
            logging.info(f"双击跳转到台词: {cue.id} (第{row+1}行)")
    
    def update_table_selection(self, index: int):
        """更新表格选中状态"""
        # 更新剧场模式表格（使用高亮而非选中）
        if hasattr(self, 'theater_table') and self.theater_table and hasattr(self, 'theater_model') and self.theater_model:
            try:
                self.update_theater_highlight(index)
            except Exception:
                pass
        
        # 更新编辑模式表格
        if hasattr(self, 'script_table') and self.script_table:
            selection_model = self.script_table.selectionModel()
            if selection_model:
                model = self.script_table.model()
                if model and 0 <= index < model.rowCount():
                    model_index = model.index(index, 0)
                    selection_model.select(model_index, selection_model.SelectionFlag.ClearAndSelect | selection_model.SelectionFlag.Rows)
                    self.script_table.scrollTo(model_index)

    def update_theater_highlight(self, actual_row: int):
        """高亮剧场模式中的指定实际行，并滚动到可见位置"""
        if not hasattr(self, 'theater_model') or not self.theater_model:
            return
        if actual_row < 0:
            return
        # 清除旧高亮并设置新高亮
        self.theater_model.clear_highlighting()
        self.theater_model.highlight_row(actual_row)
        # 计算可见行索引并滚动
        try:
            visible_row = self.theater_model.get_visible_row(actual_row)
            if visible_row < 0:
                visible_row = actual_row
            if hasattr(self, 'theater_table') and self.theater_table:
                model_index = self.theater_model.index(visible_row, 0)
                self.theater_table.scrollTo(model_index)
        except Exception:
            pass
            
    def _update_character_delegate(self):
        """更新角色委托中的角色列表"""
        try:
            if not hasattr(self, 'character_delegate') or not self.character_delegate:
                return
                
            # 从当前剧本数据中提取所有角色
            characters = set()
            if self.script_data and self.script_data.cues:
                for cue in self.script_data.cues:
                    if cue.character and cue.character.strip():
                        characters.add(cue.character.strip())
            
            # 更新委托的角色列表
            character_list = sorted(list(characters))
            self.character_delegate.set_character_list(character_list)
            
            logging.info(f"角色委托已更新，包含 {len(character_list)} 个角色: {character_list}")
            
        except Exception as e:
            logging.error(f"更新角色委托失败: {e}")
            
    def _reindex_all_cues(self):
        """重新计算所有台词的ID和角色序号"""
        try:
            cues = self.script_model.get_cues()
            if not cues:
                return
                
            # 重新分配总体序号ID
            for i, cue in enumerate(cues):
                cue.id = i + 1
                
            # 重新计算角色序号
            character_counters = {}  # 记录每个角色的台词计数
            
            for cue in cues:
                character = cue.character
                if character and character.strip():
                    # 如果角色名不为空，更新角色序号
                    if character not in character_counters:
                        character_counters[character] = 0
                    character_counters[character] += 1
                    cue.character_cue_index = character_counters[character]
                else:
                    # 如果角色名为空，设置为-1
                    cue.character_cue_index = -1
                    
            # 通知模型数据已更改
            self.script_model.layoutChanged.emit()
            self.script_model._modified = True
            self.script_model.dataModified.emit()
            
            # 同步到剧场模式
            self.sync_theater_model()
            
            logging.info(f"重新编号完成: {len(cues)} 条台词，{len(character_counters)} 个角色")
            
        except Exception as e:
            logging.error(f"重新编号失败: {e}")
            
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止加载线程（如果正在运行）
        if self.load_thread and self.load_thread.isRunning():
            self.load_thread.quit()
            self.load_thread.wait()
            
        # 保存角色颜色配置
        self.character_color_manager.save_config()
            
        # 关闭子窗口
        if self.subtitle_window:
            self.subtitle_window.close()
        if self.debug_window:
            self.debug_window.close()
        if self.playcontrol_window:
            self.playcontrol_window.close()
            
        event.accept()

    # === G2P引擎管理方法 ===
    
    def setup_g2p_ui(self):
        """设置G2P引擎选择UI"""
        try:
            # 获取可用引擎
            available_engines = self.g2p_manager.get_available_engines()
            
            # 清空并填充引擎下拉框
            self.g2p_engine_combo.clear()
            for engine_type, config in available_engines:
                self.g2p_engine_combo.addItem(config["name"], engine_type)
            
            # 设置默认选择（Epitran优先）
            for i in range(self.g2p_engine_combo.count()):
                engine_type = self.g2p_engine_combo.itemData(i)
                if engine_type == G2PEngineType.EPITRAN:
                    self.g2p_engine_combo.setCurrentIndex(i)
                    break
            
            # 更新语言选择
            self.update_g2p_language_combo()
            
            # 更新状态
            self.update_g2p_status()
            
        except Exception as e:
            logging.error(f"设置G2P UI失败: {e}")
            if hasattr(self, 'g2p_status_label') and self.g2p_status_label:
                self.g2p_status_label.setText("错误")
                self.g2p_status_label.setStyleSheet("color: red; font-weight: bold;")
    
    def update_g2p_language_combo(self):
        """更新G2P语言选择下拉框"""
        try:
            current_engine_type = self.g2p_engine_combo.currentData()
            if current_engine_type is None:
                return
                
            # 获取当前引擎支持的语言
            languages = self.g2p_manager.get_engine_languages(current_engine_type)
            
            # 清空并填充语言下拉框
            self.g2p_language_combo.clear()
            for lang_name, lang_code in languages.items():
                self.g2p_language_combo.addItem(lang_name, lang_code)
            
            # 设置默认语言（法语优先）
            for i in range(self.g2p_language_combo.count()):
                if "法语" in self.g2p_language_combo.itemText(i):
                    self.g2p_language_combo.setCurrentIndex(i)
                    break
                    
        except Exception as e:
            logging.error(f"更新G2P语言选择失败: {e}")
    
    def update_g2p_status(self):
        """更新G2P状态显示"""
        try:
            if not hasattr(self, 'g2p_status_label') or not self.g2p_status_label:
                return
                
            engine_info = self.g2p_manager.get_current_engine_info()
            status_text = f"{engine_info['name']} ({engine_info['language']})"
            self.g2p_status_label.setText(status_text)
            self.g2p_status_label.setStyleSheet("color: green; font-weight: bold;")
        except Exception as e:
            logging.error(f"更新G2P状态失败: {e}")
            if hasattr(self, 'g2p_status_label') and self.g2p_status_label:
                self.g2p_status_label.setText("错误")
                self.g2p_status_label.setStyleSheet("color: red; font-weight: bold;")
    
    @Slot(str)
    def on_g2p_engine_changed(self, engine_name: str):
        """G2P引擎选择变化事件"""
        try:
            engine_type = self.g2p_engine_combo.currentData()
            if engine_type is None:
                return
            
            # 更新语言选择
            self.update_g2p_language_combo()
            
            # 获取默认语言
            config = self.g2p_manager.engine_configs[engine_type]
            default_language = config["default_language"]
            
            # 切换引擎
            self.g2p_manager.switch_engine(engine_type, default_language)
            
            # 更新状态
            self.update_g2p_status()
            
            logging.info(f"G2P引擎已切换到: {engine_name}")
            
        except Exception as e:
            logging.error(f"切换G2P引擎失败: {e}")
            if hasattr(self, 'g2p_status_label') and self.g2p_status_label:
                self.g2p_status_label.setText("切换失败")
                self.g2p_status_label.setStyleSheet("color: red; font-weight: bold;")
    
    @Slot(str)
    def on_g2p_language_changed(self, language_name: str):
        """G2P语言选择变化事件"""
        try:
            language_code = self.g2p_language_combo.currentData()
            engine_type = self.g2p_engine_combo.currentData()
            
            if language_code is None or engine_type is None:
                return
            
            # 切换语言
            self.g2p_manager.switch_engine(engine_type, language_code)
            
            # 更新状态
            self.update_g2p_status()
            
            logging.info(f"G2P语言已切换到: {language_name} ({language_code})")
            
        except Exception as e:
            logging.error(f"切换G2P语言失败: {e}")
            if hasattr(self, 'g2p_status_label') and self.g2p_status_label:
                self.g2p_status_label.setText("语言切换失败")
                self.g2p_status_label.setStyleSheet("color: red; font-weight: bold;")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("Miomu")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Miomu Project")
    
    # 创建主窗口
    window = MainConsoleWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()