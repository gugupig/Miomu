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
from PySide6.QtCore import Qt, Signal, Slot, QThread, QTimer
from PySide6.QtGui import QFont, QBrush, QColor, QKeySequence, QShortcut

print("导入UI文件...")
# 导入生成的UI文件
try:
    from app.ui.ui_main_console_full import Ui_MainWindow
    from app.ui.ui_character_color_dialog import Ui_CharacterColorDialog
    from app.ui.ui_style_manager_dialog import Ui_StyleManagerDialog
    from app.ui.ui_character_filter_dialog import Ui_CharacterFilterDialog
    USE_UI_FILE = True
    print("✅ UI文件导入成功")
except ImportError:
    USE_UI_FILE = False
    logging.warning("UI文件未找到，使用代码创建界面")

print("导入应用模块...")

from app.data.script_data import ScriptData
from app.core.player import SubtitlePlayer
from app.core.audio.audio_hub import AudioHub
from app.core.stt.whisper_engine import WhisperEngine
from app.core.stt.vosk_engine import VoskEngine
from app.core.aligner.Aligner import Aligner
from app.core.g2p.phonemizer_g2p import PhonemizerG2P
from app.core.g2p.g2p_manager import G2PManager, G2PEngineType
from app.models.models import Cue
from app.models.script_table_model import ScriptTableModel
from app.views.subtitle_window import SubtitleWindow
from app.views.debug_window import DebugLogWindow
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
            
            self.progress_updated.emit(30, "正在读取剧本文件...")
            
            # 创建ScriptData实例
            script_data = ScriptData()
            
            # 自定义加载逻辑，支持进度回调
            success = self._load_script_with_progress(script_data, self.file_path, g2p_converter)
            
            if success and script_data.cues:
                self.progress_updated.emit(100, f"成功加载 {len(script_data.cues)} 条台词")
                self.script_loaded.emit(script_data)
            else:
                self.error_occurred.emit("剧本加载失败或文件为空")
                
        except Exception as e:
            self.error_occurred.emit(f"加载剧本时出错: {str(e)}")
            
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


class EngineWorkerThread(QThread):
    """后台引擎工作线程"""
    status_changed = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, g2p_manager=None, parent=None):
        super().__init__(parent)
        self.audio_hub: Optional[AudioHub] = None
        self.stt_engine = None
        self.aligner: Optional[Aligner] = None
        self.running = False
        self.g2p_manager = g2p_manager
        
    def setup_engines(self, script_data: ScriptData, player: SubtitlePlayer):
        """设置引擎"""
        try:
            # 使用传入的G2P管理器或创建新的管理器
            if self.g2p_manager is not None:
                g2p_converter = self.g2p_manager.get_current_engine()
                engine_info = self.g2p_manager.get_current_engine_info()
                self.status_changed.emit(f"使用 {engine_info['name']}")
            else:
                # 备用方案：创建新的G2P管理器
                from app.core.g2p.g2p_manager import G2PManager
                g2p_manager = G2PManager()
                g2p_converter = g2p_manager.get_best_available_engine()
                engine_info = g2p_manager.get_current_engine_info()
                self.status_changed.emit(f"使用 {engine_info['name']}")
            
            # 创建音频采集器
            self.audio_hub = AudioHub(
                channels=1, 
                samplerate=16000, 
                frames_per_block=1600,
                silence_thresh=0.03
            )
            
            # 创建STT引擎 - 优先使用Whisper
            try:
                self.stt_engine = WhisperEngine(
                    model_size="small",
                    device="cpu",  # 根据需要改为"cuda"
                    language="zh"
                )
                self.status_changed.emit("使用 Whisper 引擎")
            except Exception as e:
                logging.warning(f"Whisper引擎初始化失败，尝试Vosk: {e}")
                try:
                    self.stt_engine = VoskEngine(
                        model_dir="app/models/stt/vosk/vosk-model-cn-0.22",
                        lang='zh'
                    )
                    self.status_changed.emit("使用 Vosk 引擎")
                except Exception as e2:
                    raise Exception(f"所有STT引擎都无法初始化: {e2}")
            
            # 创建对齐器
            self.aligner = Aligner(
                player=player,
                stt_engine=self.stt_engine,
                cues=script_data.cues,
                g2p_converter=g2p_converter,
                trigger_on='beginning'
            )
            
            # 连接信号 - 直接连接，利用新的统一接口
            if self.stt_engine and self.audio_hub:
                self.audio_hub.blockReady.connect(self.stt_engine.feed)
            
            self.status_changed.emit("引擎设置完成")
            
        except Exception as e:
            self.error_occurred.emit(f"引擎设置失败: {str(e)}")
            
    def start_engines(self):
        """启动引擎"""
        try:
            if self.stt_engine:
                self.stt_engine.start()
                self.status_changed.emit("STT引擎已启动")
                
            if self.audio_hub:
                self.audio_hub.start()
                self.status_changed.emit("音频采集已启动")
                
            self.running = True
            self.status_changed.emit("所有引擎已启动")
            
        except Exception as e:
            self.error_occurred.emit(f"引擎启动失败: {str(e)}")
            
    def stop_engines(self):
        """停止引擎"""
        try:
            self.running = False
            
            if self.audio_hub:
                self.audio_hub.stop()
                
            if self.stt_engine:
                self.stt_engine.stop()
                
            self.status_changed.emit("所有引擎已停止")
            
        except Exception as e:
            self.error_occurred.emit(f"引擎停止失败: {str(e)}")


class MainConsoleWindow(QMainWindow):
    """主控制台窗口"""
    
    def __init__(self):
        super().__init__()
        self.script_data = ScriptData()
        
        # G2P管理器
        self.g2p_manager = G2PManager()
        
        # 角色颜色管理器
        self.character_color_manager = CharacterColorManager()
        
        self.script_model = ScriptTableModel(character_color_manager=self.character_color_manager)  # 编辑模式的数据模型
        self.theater_model = ScriptTableModel(character_color_manager=self.character_color_manager)  # 剧场模式的数据模型
        self.player: Optional[SubtitlePlayer] = None
        self.subtitle_window: Optional[SubtitleWindow] = None
        self.debug_window: Optional[DebugLogWindow] = None
        self.worker_thread = EngineWorkerThread(g2p_manager=self.g2p_manager)
        self.load_thread: Optional[LoadScriptThread] = None  # 加载线程
        
        # 设置日志处理
        self.setup_logging()
        
        # 根据是否有UI文件决定初始化方式
        if USE_UI_FILE:
            self.init_ui_from_file()
        else:
            self.init_ui()
            
        self.setup_signals()
        
        # 状态
        self.is_running = False
        self.current_cue_index = -1
        
    def setup_logging(self):
        """设置日志处理"""
        self.log_handler = QtLogHandler()
        logging.getLogger().addHandler(self.log_handler)
        logging.getLogger().setLevel(logging.DEBUG)
        
    def init_ui_from_file(self):
        """从UI文件初始化界面"""
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # 连接UI元素到类属性以保持兼容性
        self.tab_widget = self.ui.tabWidget
        
        # 编辑模式标签页元素
        self.edit_tab = self.ui.editTab
        self.script_table = self.ui.scriptView
        self.script_view = self.script_table  # 别名，保持兼容性
        self.load_script_btn = self.ui.loadScriptButton
        self.save_script_btn = self.ui.saveScriptButton
        self.align_btn = getattr(self.ui, 'alignButton', None)  # 如果UI中没有，使用None
        self.progress_bar = self.ui.progressBar
        self.progress_label = getattr(self.ui, 'progressLabel', None)
        
        # 剧场模式标签页元素
        self.theater_tab = self.ui.theaterTab
        self.theater_table = self.ui.theaterTable
        self.theater_view = self.theater_table  # 别名，保持兼容性
        self.play_btn = self.ui.startButton
        self.start_btn = self.play_btn  # 别名，保持兼容性
        self.pause_btn = self.ui.pauseButton
        self.stop_btn = self.ui.stopButton
        self.prev_btn = getattr(self.ui, 'prevButton', None)
        self.next_btn = getattr(self.ui, 'nextButton', None)
        self.show_subtitle_btn = self.ui.showSubtitleButton
        self.show_debug_btn = self.ui.showDebugButton
        
        # 角色管理元素
        self.character_color_btn = self.ui.manageCharacterColorsButton
        self.style_manager_btn = self.ui.manageStylesButton
        self.character_filter_btn = self.ui.filterByCharacterButton
        
        # 状态栏和日志
        self.status_bar = self.ui.statusbar
        self.log_display = self.ui.logTextEdit
        
        # 创建G2P组件（如果UI文件没有包含的话）
        self.setup_g2p_components()
        
        # 创建缺失的按钮组件（如果UI文件没有包含的话）
        self.setup_missing_buttons()
        
        # 创建状态栏子组件（如果UI文件没有包含的话）
        self.setup_status_bar()
        
        # 设置表格模型
        self.script_table.setModel(self.script_model)
        self.theater_table.setModel(self.theater_model)
        
        # 设置表格属性
        self.setup_table_properties()
        
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

    def setup_missing_buttons(self):
        """设置缺失的按钮组件（如果UI文件没有包含的话）"""
        # 编辑模式相关按钮
        missing_buttons = [
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
            ('load_script_theater_btn', '加载剧本'),
        ]
        
        for btn_name, btn_text in missing_buttons:
            if not hasattr(self, btn_name) or not getattr(self, btn_name):
                btn = QPushButton(btn_text)
                btn.setEnabled(False)  # 默认禁用
                setattr(self, btn_name, btn)
                print(f"✅ 动态创建按钮: {btn_name}")
        
        # 为动态创建的按钮连接信号（如果方法存在的话）
        self.connect_missing_button_signals()
        
    def connect_missing_button_signals(self):
        """为缺失的按钮连接信号"""
        button_method_mapping = {
            'load_script_btn': 'load_script',
            'save_script_btn': 'save_script',
            'show_subtitle_btn': 'show_subtitle_window',
            'show_debug_btn': 'show_debug_window',
            'add_cue_btn': 'add_cue',
            'delete_cue_btn': 'delete_cue', 
            'duplicate_cue_btn': 'duplicate_cue',
            'refresh_phonemes_btn': 'refresh_phonemes',
            'add_language_btn': 'add_language_column',
            'remove_language_btn': 'remove_language_column',
            'manage_styles_btn': 'manage_styles',
            'load_script_theater_btn': 'load_script',
        }
        
        for btn_name, method_name in button_method_mapping.items():
            if hasattr(self, btn_name) and hasattr(self, method_name):
                btn = getattr(self, btn_name)
                method = getattr(self, method_name)
                try:
                    btn.clicked.connect(method)
                    print(f"✅ 连接信号: {btn_name} -> {method_name}")
                except Exception as e:
                    print(f"⚠️ 信号连接失败: {btn_name} -> {method_name}: {e}")

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
        
        # 剧场模式表格设置
        if hasattr(self, 'theater_table'):
            self.theater_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.theater_table.setAlternatingRowColors(True)
            header = self.theater_table.horizontalHeader()
            if header:
                header.setStretchLastSection(True)
                header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("Miomu - 剧本对齐控制台")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央组件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页组件
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 编辑模式标签页
        self.create_edit_tab()
        
        # 剧场模式标签页
        self.create_theater_tab()
        
        # 创建状态栏
        self.create_status_bar()
        
        # 设置快捷键
        self.setup_shortcuts()
        
    def create_edit_tab(self):
        """创建编辑模式标签页"""
        edit_widget = QWidget()
        edit_layout = QVBoxLayout(edit_widget)
        
        # 顶部工具栏
        toolbar_layout = QHBoxLayout()
        
        self.load_script_btn = QPushButton("加载剧本")
        self.load_script_btn.clicked.connect(self.load_script)
        toolbar_layout.addWidget(self.load_script_btn)
        
        self.save_script_btn = QPushButton("保存剧本")
        self.save_script_btn.setEnabled(False)
        self.save_script_btn.clicked.connect(self.save_script)
        toolbar_layout.addWidget(self.save_script_btn)
        
        # 编辑操作按钮
        self.add_cue_btn = QPushButton("添加台词")
        self.add_cue_btn.setEnabled(False)
        self.add_cue_btn.clicked.connect(self.add_cue)
        toolbar_layout.addWidget(self.add_cue_btn)
        
        self.delete_cue_btn = QPushButton("删除台词")
        self.delete_cue_btn.setEnabled(False)
        self.delete_cue_btn.clicked.connect(self.delete_cue)
        toolbar_layout.addWidget(self.delete_cue_btn)
        
        self.duplicate_cue_btn = QPushButton("复制台词")
        self.duplicate_cue_btn.setEnabled(False)
        self.duplicate_cue_btn.clicked.connect(self.duplicate_cue)
        toolbar_layout.addWidget(self.duplicate_cue_btn)
        
        # 批量操作按钮
        self.refresh_phonemes_btn = QPushButton("刷新音素")
        self.refresh_phonemes_btn.setEnabled(False)
        self.refresh_phonemes_btn.clicked.connect(self.refresh_phonemes)
        toolbar_layout.addWidget(self.refresh_phonemes_btn)
        
        # 多语言管理按钮
        self.add_language_btn = QPushButton("添加语言")
        self.add_language_btn.setEnabled(False)
        self.add_language_btn.clicked.connect(self.add_language_column)
        toolbar_layout.addWidget(self.add_language_btn)
        
        self.remove_language_btn = QPushButton("移除语言")
        self.remove_language_btn.setEnabled(False)
        self.remove_language_btn.clicked.connect(self.remove_language_column)
        toolbar_layout.addWidget(self.remove_language_btn)
        
        # 样式管理按钮
        self.manage_styles_btn = QPushButton("管理样式")
        self.manage_styles_btn.setEnabled(False)
        self.manage_styles_btn.clicked.connect(self.manage_styles)
        toolbar_layout.addWidget(self.manage_styles_btn)
        
        # G2P引擎选择组件
        toolbar_layout.addWidget(QLabel(" | "))  # 分隔符
        
        toolbar_layout.addWidget(QLabel("G2P引擎:"))
        self.g2p_engine_combo = QComboBox()
        self.g2p_engine_combo.setMinimumWidth(120)
        self.g2p_engine_combo.currentTextChanged.connect(self.on_g2p_engine_changed)
        toolbar_layout.addWidget(self.g2p_engine_combo)
        
        self.g2p_language_combo = QComboBox()
        self.g2p_language_combo.setMinimumWidth(80)
        self.g2p_language_combo.currentTextChanged.connect(self.on_g2p_language_changed)
        toolbar_layout.addWidget(self.g2p_language_combo)
        
        self.g2p_status_label = QLabel("就绪")
        self.g2p_status_label.setStyleSheet("color: green; font-weight: bold;")
        toolbar_layout.addWidget(self.g2p_status_label)
        
        toolbar_layout.addStretch()
        
        edit_layout.addLayout(toolbar_layout)
        
        # 剧本表格视图（使用 QTableView + Model）
        self.script_view = QTableView()
        self.script_view.setModel(self.script_model)
        
        # 设置表格属性
        self.script_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.script_view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.script_view.setAlternatingRowColors(True)
        self.script_view.setSortingEnabled(True)
        self.script_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # 设置列宽
        header = self.script_view.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID列
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 角色列
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)            # 台词列
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 音素列
        
        # 连接信号
        self.script_view.doubleClicked.connect(self.on_script_item_double_clicked)
        self.script_view.customContextMenuRequested.connect(self.show_edit_context_menu)
        selection_model = self.script_view.selectionModel()
        if selection_model:
            selection_model.selectionChanged.connect(self.on_script_selection_changed)
        
        edit_layout.addWidget(self.script_view)
        
        self.tab_widget.addTab(edit_widget, "编辑模式")
        
    def create_theater_tab(self):
        """创建剧场模式标签页"""
        theater_widget = QWidget()
        theater_layout = QVBoxLayout(theater_widget)
        
        # 上方工具栏
        theater_toolbar = QHBoxLayout()
        
        self.load_script_theater_btn = QPushButton("加载剧本")
        self.load_script_theater_btn.clicked.connect(self.load_script)
        theater_toolbar.addWidget(self.load_script_theater_btn)
        
        self.filter_by_character_btn = QPushButton("按角色筛选")
        self.filter_by_character_btn.setEnabled(False)
        self.filter_by_character_btn.clicked.connect(self.filter_by_character)
        theater_toolbar.addWidget(self.filter_by_character_btn)
        
        # 语言选择下拉框（预留）
        from PySide6.QtWidgets import QComboBox
        self.language_combo = QComboBox()
        self.language_combo.setEnabled(False)
        self.language_combo.addItem("原始语言")
        theater_toolbar.addWidget(self.language_combo)
        
        self.manage_character_colors_btn = QPushButton("管理角色颜色")
        self.manage_character_colors_btn.setEnabled(False)
        self.manage_character_colors_btn.clicked.connect(self.manage_character_colors)
        theater_toolbar.addWidget(self.manage_character_colors_btn)
        
        theater_toolbar.addStretch()
        
        theater_layout.addLayout(theater_toolbar)
        
        # 控制面板
        control_panel = QHBoxLayout()
        
        self.start_btn = QPushButton("开始对齐")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_alignment)
        control_panel.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("暂停")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_alignment)
        control_panel.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_alignment)
        control_panel.addWidget(self.stop_btn)
        
        control_panel.addStretch()
        
        self.show_subtitle_btn = QPushButton("显示字幕窗口")
        self.show_subtitle_btn.setEnabled(False)
        self.show_subtitle_btn.clicked.connect(self.show_subtitle_window)
        control_panel.addWidget(self.show_subtitle_btn)
        
        self.show_debug_btn = QPushButton("调试窗口")
        self.show_debug_btn.clicked.connect(self.show_debug_window)
        control_panel.addWidget(self.show_debug_btn)
        
        theater_layout.addLayout(control_panel)
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 剧场模式现在也使用 QTableView + Model 来实现动态列同步
        self.theater_view = QTableView()
        self.theater_view.setModel(self.theater_model)
        
        # 设置剧场模式表格属性（只读）
        self.theater_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.theater_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.theater_view.setAlternatingRowColors(True)
        self.theater_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)  # 禁用编辑
        
        # 设置列宽自适应
        theater_header = self.theater_view.horizontalHeader()
        theater_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # ID
        theater_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 角色
        theater_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)            # 主要台词
        # 其他列会根据内容自动调整
        
        # 连接点击事件
        self.theater_view.clicked.connect(self.on_theater_item_clicked)
        
        # 设置字体大小
        font = QFont()
        font.setPointSize(12)
        self.theater_view.setFont(font)
        
        splitter.addWidget(self.theater_view)
        
        # 实时日志显示
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setMaximumHeight(200)
        font = QFont("Consolas", 9)
        self.log_display.setFont(font)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #555;
            }
        """)
        
        splitter.addWidget(self.log_display)
        splitter.setSizes([600, 200])
        
        theater_layout.addWidget(splitter)
        
        self.tab_widget.addTab(theater_widget, "剧场模式")
        
    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 状态标签
        self.status_label = QLabel("就绪")
        self.status_bar.addWidget(self.status_label)
        
        # 对齐状态指示器
        self.alignment_status = QLabel("对齐器: 停止")
        self.status_bar.addPermanentWidget(self.alignment_status)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
    def setup_status_bar(self):
        """设置状态栏子组件（UI文件集成时使用）"""
        # 检查是否已有状态栏子组件，如果没有则创建
        if not hasattr(self, 'status_label') or self.status_label is None:
            # 状态标签
            self.status_label = QLabel("就绪")
            self.status_bar.addWidget(self.status_label)
        
        if not hasattr(self, 'alignment_status') or self.alignment_status is None:
            # 对齐状态指示器
            self.alignment_status = QLabel("对齐器: 停止")
            self.status_bar.addPermanentWidget(self.alignment_status)
        
        if not hasattr(self, 'progress_bar') or self.progress_bar is None:
            # 进度条
            self.progress_bar = QProgressBar()
            self.progress_bar.setVisible(False)
            self.status_bar.addPermanentWidget(self.progress_bar)
        
    def setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+O 打开文件
        open_shortcut = QShortcut(QKeySequence.StandardKey.Open, self)
        open_shortcut.activated.connect(self.load_script)
        
        # 空格键播放/暂停
        space_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Space), self)
        space_shortcut.activated.connect(self.toggle_alignment)
        
        # F5 刷新
        refresh_shortcut = QShortcut(QKeySequence.StandardKey.Refresh, self)
        refresh_shortcut.activated.connect(self.refresh_display)
        
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
        
        # UI按钮信号连接
        if USE_UI_FILE:
            self.setup_ui_signals()
            
        # 设置G2P UI
        self.setup_g2p_ui()
            
    def setup_ui_signals(self):
        """设置UI文件中的信号连接"""
        # 编辑模式按钮
        if hasattr(self, 'load_script_btn') and self.load_script_btn:
            self.load_script_btn.clicked.connect(self.load_script)
        if hasattr(self, 'save_script_btn') and self.save_script_btn:
            self.save_script_btn.clicked.connect(self.save_script)
        
        # 剧场模式按钮
        if hasattr(self, 'play_btn') and self.play_btn:
            self.play_btn.clicked.connect(self.start_alignment)
        if hasattr(self, 'pause_btn') and self.pause_btn:
            self.pause_btn.clicked.connect(self.pause_alignment)
        if hasattr(self, 'stop_btn') and self.stop_btn:
            self.stop_btn.clicked.connect(self.stop_alignment)
        if hasattr(self, 'show_subtitle_btn') and self.show_subtitle_btn:
            self.show_subtitle_btn.clicked.connect(self.show_subtitle_window)
        if hasattr(self, 'show_debug_btn') and self.show_debug_btn:
            self.show_debug_btn.clicked.connect(self.show_debug_window)
            
        # 角色管理按钮
        if hasattr(self, 'character_color_btn') and self.character_color_btn:
            self.character_color_btn.clicked.connect(self.show_character_color_dialog)
        if hasattr(self, 'style_manager_btn') and self.style_manager_btn:
            self.style_manager_btn.clicked.connect(self.show_style_manager_dialog)
        if hasattr(self, 'character_filter_btn') and self.character_filter_btn:
            self.character_filter_btn.clicked.connect(self.show_character_filter_dialog)
        
    @Slot()
    def load_script(self):
        """加载剧本文件"""
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
            
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 100)  # 确定进度
        self.progress_bar.setValue(0)
        
        # 禁用加载按钮，防止重复点击
        self.load_script_btn.setEnabled(False)
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
            
            # 同步剧场模式数据模型
            self.sync_theater_model()
            
            # 创建播放器
            self.player = SubtitlePlayer(self.script_data.cues)
            self.player.cueChanged.connect(self.on_cue_changed)
            
            # 启用相关按钮
            self.start_btn.setEnabled(True)
            self.show_subtitle_btn.setEnabled(True)
            self.save_script_btn.setEnabled(True)
            self.add_cue_btn.setEnabled(True)
            self.delete_cue_btn.setEnabled(True)
            self.duplicate_cue_btn.setEnabled(True)
            self.refresh_phonemes_btn.setEnabled(True)
            self.add_language_btn.setEnabled(True)
            self.remove_language_btn.setEnabled(True)
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
            
        except Exception as e:
            self.show_error(f"处理加载结果时出错: {str(e)}")
            logging.error(f"处理加载结果失败: {e}")
            
    @Slot(str)
    def on_load_error(self, error_message: str):
        """处理加载错误"""
        self.show_error(error_message)
        logging.error(f"剧本加载失败: {error_message}")
        
    @Slot()
    def on_load_finished(self):
        """加载线程完成时的清理工作"""
        self.progress_bar.setVisible(False)
        self.load_script_btn.setEnabled(True)
        
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
        
        # 如果编辑模式有额外的列，也同步到剧场模式
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
        
        # 其他语言列设置为自适应内容
        for col in range(3, column_count):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
            
    @Slot()
    def start_alignment(self):
        """开始对齐"""
        if not self.player or not self.script_data.cues:
            self.show_error("请先加载剧本")
            return
            
        try:
            self.update_status("正在启动引擎...")
            
            # 设置并启动后台引擎
            self.worker_thread.setup_engines(self.script_data, self.player)
            self.worker_thread.start_engines()
            
            # 连接对齐器信号
            if self.worker_thread.aligner:
                self.worker_thread.aligner.cueMatched.connect(self.on_cue_matched)
                self.worker_thread.aligner.alignmentUncertain.connect(self.on_alignment_uncertain)
            
            self.is_running = True
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.update_alignment_status("对齐器: 运行中", "green")
            
            logging.info("对齐系统已启动")
            
        except Exception as e:
            self.show_error(f"启动对齐失败: {str(e)}")
            
    @Slot()
    def stop_alignment(self):
        """停止对齐"""
        try:
            self.worker_thread.stop_engines()
            
            self.is_running = False
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.update_alignment_status("对齐器: 停止", "red")
            
            # 清除高亮
            self.clear_table_highlighting()
            
            self.update_status("对齐已停止")
            logging.info("对齐系统已停止")
            
        except Exception as e:
            self.show_error(f"停止对齐失败: {str(e)}")
            
    @Slot()
    def toggle_alignment(self):
        """切换对齐状态"""
        if self.is_running:
            self.stop_alignment()
        else:
            self.start_alignment()
            
    @Slot(Cue)
    def on_cue_changed(self, cue: Cue):
        """响应播放器台词变化"""
        self.current_cue_index = cue.id - 1
        self.highlight_current_cue()
        self.update_status(f"当前台词: {cue.id} - {cue.character or '(舞台提示)'}")
        
    @Slot(Cue)
    def on_cue_matched(self, cue: Cue):
        """响应对齐器匹配信号"""
        if self.player:
            self.player.go_by_cue_obj(cue)
            
    @Slot(bool)
    def on_alignment_uncertain(self, uncertain: bool):
        """响应对齐器不确定状态"""
        if uncertain:
            self.update_alignment_status("对齐器: 不确定", "orange")
        else:
            self.update_alignment_status("对齐器: 运行中", "green")
            
    def highlight_current_cue(self):
        """高亮当前台词行"""
        if self.current_cue_index < 0:
            return
            
        # 清除之前的高亮
        self.clear_table_highlighting()
        
        # 在剧场模式表格中高亮当前行
        if self.current_cue_index < self.theater_model.rowCount():
            # 使用模型的高亮功能
            self.theater_model.highlight_row(self.current_cue_index)
                    
            # 滚动到当前行
            current_index = self.theater_model.index(self.current_cue_index, 0)
            self.theater_view.scrollTo(current_index, QTableView.ScrollHint.PositionAtCenter)
            
    def clear_table_highlighting(self):
        """清除表格高亮"""
        # 使用模型的清除高亮功能
        if hasattr(self.theater_model, 'clear_highlighting'):
            self.theater_model.clear_highlighting()
                    
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
        """显示字幕窗口"""
        if not self.player:
            self.show_error("请先加载剧本")
            return
            
        if self.subtitle_window is None:
            self.subtitle_window = SubtitleWindow(self.player)
            
        self.subtitle_window.show()
        self.subtitle_window.raise_()
        self.subtitle_window.activateWindow()
        
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
                
    def update_alignment_status(self, message: str, color: str = "black"):
        """更新对齐器状态显示"""
        if hasattr(self, 'alignment_status') and self.alignment_status:
            self.alignment_status.setText(message)
            self.alignment_status.setStyleSheet(f"color: {color};")
        else:
            # 备用方案：显示在状态栏或日志中
            full_message = f"[ALIGN] {message}"
            self.update_status(full_message)
        
    @Slot(str)
    def show_error(self, message: str):
        """显示错误消息"""
        QMessageBox.critical(self, "错误", message)
        logging.error(message)
        
    @Slot(str, int)
    def add_log_message(self, message: str, level: int):
        """添加日志消息到实时显示"""
        if level >= logging.INFO:  # 只显示INFO及以上级别
            self.log_display.append(message)
            # 自动滚动到底部
            scrollbar = self.log_display.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    # === 编辑模式新增方法 ===
    
    @Slot()
    def save_script(self):
        """保存剧本"""
        if not self.script_data.cues:
            self.show_error("没有可保存的剧本数据")
            return
            
        try:
            # 从模型同步数据到script_data
            self.script_data.cues = self.script_model.get_cues()
            
            # 保存到文件
            self.script_data.save_to_file()
            self.script_model.mark_saved()
            
            self.update_status("剧本已保存")
            logging.info(f"剧本已保存到: {self.script_data.filepath}")
            
        except Exception as e:
            self.show_error(f"保存剧本失败: {str(e)}")
            logging.error(f"保存剧本失败: {e}")
            
    @Slot()
    def add_cue(self):
        """添加新台词"""
        character, ok = QInputDialog.getText(self, "添加台词", "角色名称:")
        if not ok or not character.strip():
            return
            
        line, ok = QInputDialog.getText(self, "添加台词", "台词内容:")
        if not ok or not line.strip():
            return
            
        success = self.script_model.add_cue(character.strip(), line.strip())
        if success:
            self.update_status("已添加新台词")
        else:
            self.show_error("添加台词失败")
            
    @Slot()
    def delete_cue(self):
        """删除选中的台词"""
        selection = self.script_view.selectionModel()
        if not selection or not selection.hasSelection():
            self.show_error("请先选择要删除的台词")
            return
            
        selected_rows = []
        for index in selection.selectedRows():
            selected_rows.append(index.row())
            
        if not selected_rows:
            return
            
        # 确认删除
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除选中的 {len(selected_rows)} 条台词吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        # 从后往前删除，避免索引问题
        selected_rows.sort(reverse=True)
        deleted_count = 0
        
        for row in selected_rows:
            if self.script_model.remove_cue(row):
                deleted_count += 1
                
        self.update_status(f"已删除 {deleted_count} 条台词")
        
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
        """添加语言列"""
        language_name, ok = QInputDialog.getText(
            self, "添加语言", "请输入语言名称:"
        )
        
        if not ok or not language_name.strip():
            return
            
        language_name = language_name.strip()
        
        # 检查是否已存在
        if hasattr(self.script_model, 'get_language_columns'):
            if language_name in self.script_model.get_language_columns():
                QMessageBox.warning(self, "警告", f"语言 '{language_name}' 已存在")
                return
            
        # 添加到编辑模式
        if hasattr(self.script_model, 'add_language_column'):
            success = self.script_model.add_language_column(language_name)
            
            if success:
                # 同步到剧场模式
                self.sync_theater_model()
                self.update_status(f"已添加语言列: {language_name}")
            else:
                QMessageBox.warning(self, "错误", "添加语言列失败")
        else:
            QMessageBox.information(self, "提示", "当前版本的ScriptTableModel不支持多语言功能")
            
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
    
    @Slot()
    def pause_alignment(self):
        """暂停对齐"""
        if self.is_running:
            # 暂停功能的简单实现 - 先停止，用户可以手动重新开始
            self.stop_alignment()
            self.update_status("对齐已停止（暂停功能开发中）")
    
    def _update_theater_buttons(self):
        """更新剧场模式按钮状态"""
        has_data = bool(self.script_data.cues)
        self.filter_by_character_btn.setEnabled(has_data)
        self.manage_character_colors_btn.setEnabled(has_data)
        self.language_combo.setEnabled(has_data)
        self.start_btn.setEnabled(has_data and not self.is_running)
        self.show_subtitle_btn.setEnabled(has_data)
            
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
            
    def closeEvent(self, event):
        """窗口关闭事件"""
        if self.is_running:
            reply = QMessageBox.question(
                self,
                "确认退出",
                "对齐系统正在运行，确定要退出吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
                
            self.stop_alignment()
            
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