import sys
import logging
from typing import Optional, List
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QFileDialog, QStatusBar, QLabel, QMessageBox,
    QApplication, QProgressBar, QSplitter, QTextEdit, QTableView,
    QAbstractItemView, QMenu, QInputDialog
)
from PySide6.QtCore import Qt, Signal, Slot, QThread, QTimer
from PySide6.QtGui import QFont, QBrush, QColor, QKeySequence, QShortcut

from app.data.script_data import ScriptData
from app.core.player import SubtitlePlayer
from app.core.audio.audio_hub import AudioHub
from app.core.stt.whisper_engine import WhisperEngine
from app.core.stt.vosk_engine import VoskEngine
from app.core.aligner.Aligner import Aligner
from app.core.g2p.phonemizer_g2p import PhonemizerG2P
from app.models.models import Cue
from app.models.script_table_model import ScriptTableModel
from app.views.subtitle_window import SubtitleWindow
from app.views.debug_window import DebugLogWindow
from app.utils.logging_handler import QtLogHandler


class LoadScriptThread(QThread):
    """专门用于加载和预处理剧本的后台线程"""
    progress_updated = Signal(int, str)  # 进度百分比, 状态消息
    script_loaded = Signal(object)  # ScriptData对象
    error_occurred = Signal(str)  # 错误消息
    
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.script_data = None
        
    def run(self):
        """在后台线程中执行加载和预处理"""
        try:
            self.progress_updated.emit(10, "正在初始化G2P转换器...")
            
            # 创建G2P转换器
            try:
                from app.core.g2p.phonemizer_g2p import PhonemizerG2P
                g2p_converter = PhonemizerG2P(language='fr-fr')
                self.progress_updated.emit(20, "使用 Phonemizer G2P")
            except ImportError:
                from app.core.g2p.simple_g2p import SimpleG2P
                g2p_converter = SimpleG2P(language='zh')
                self.progress_updated.emit(20, "使用简单 G2P")
            
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
                    character=r["character"],
                    line=r["line"],
                    phonemes=phoneme_str
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
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_hub: Optional[AudioHub] = None
        self.stt_engine = None
        self.aligner: Optional[Aligner] = None
        self.running = False
        
    def setup_engines(self, script_data: ScriptData, player: SubtitlePlayer):
        """设置引擎"""
        try:
            # 创建G2P转换器
            try:
                from app.core.g2p.phonemizer_g2p import PhonemizerG2P
                g2p_converter = PhonemizerG2P(language='fr-fr')
                self.status_changed.emit("使用 Phonemizer G2P")
            except ImportError:
                from app.core.g2p.simple_g2p import SimpleG2P
                g2p_converter = SimpleG2P(language='zh')
                self.status_changed.emit("使用简单 G2P")
            
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
        self.script_model = ScriptTableModel()  # 编辑模式的数据模型
        self.player: Optional[SubtitlePlayer] = None
        self.subtitle_window: Optional[SubtitleWindow] = None
        self.debug_window: Optional[DebugLogWindow] = None
        self.worker_thread = EngineWorkerThread()
        self.load_thread: Optional[LoadScriptThread] = None  # 加载线程
        
        # 设置日志处理
        self.setup_logging()
        
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
        
        # 控制面板
        control_panel = QHBoxLayout()
        
        self.start_btn = QPushButton("开始对齐")
        self.start_btn.setEnabled(False)
        self.start_btn.clicked.connect(self.start_alignment)
        control_panel.addWidget(self.start_btn)
        
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
        
        # 剧本显示表格（剧场模式）
        self.theater_table = QTableWidget()
        self.theater_table.setColumnCount(3)
        self.theater_table.setHorizontalHeaderLabels(["ID", "角色", "台词"])
        
        # 设置表格属性
        theater_header = self.theater_table.horizontalHeader()
        theater_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        theater_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        theater_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        
        self.theater_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.theater_table.setAlternatingRowColors(True)
        self.theater_table.itemClicked.connect(self.on_theater_item_clicked)
        
        # 设置字体大小
        font = QFont()
        font.setPointSize(12)
        self.theater_table.setFont(font)
        
        splitter.addWidget(self.theater_table)
        
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
        self.load_thread = LoadScriptThread(file_path, self)
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
            
            # 更新数据模型
            self.script_model.set_cues(self.script_data.cues)
            
            # 创建播放器
            self.player = SubtitlePlayer(self.script_data.cues)
            self.player.cueChanged.connect(self.on_cue_changed)
            
            # 更新剧场模式表格显示
            self.populate_theater_table()
            
            # 启用相关按钮
            self.start_btn.setEnabled(True)
            self.show_subtitle_btn.setEnabled(True)
            self.save_script_btn.setEnabled(True)
            self.add_cue_btn.setEnabled(True)
            self.delete_cue_btn.setEnabled(True)
            self.duplicate_cue_btn.setEnabled(True)
            self.refresh_phonemes_btn.setEnabled(True)
            
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
            
    def populate_theater_table(self):
        """填充剧场模式的剧本表格"""
        if not self.script_data.cues:
            return
            
        self.theater_table.setRowCount(len(self.script_data.cues))
        
        for row, cue in enumerate(self.script_data.cues):
            # ID
            id_item = QTableWidgetItem(str(cue.id))
            id_item.setFlags(id_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.theater_table.setItem(row, 0, id_item)
            
            # 角色
            character_item = QTableWidgetItem(cue.character)
            character_item.setFlags(character_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.theater_table.setItem(row, 1, character_item)
            
            # 台词
            line_item = QTableWidgetItem(cue.line)
            line_item.setFlags(line_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.theater_table.setItem(row, 2, line_item)
            
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
            self.alignment_status.setText("对齐器: 运行中")
            self.alignment_status.setStyleSheet("color: green;")
            
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
            self.alignment_status.setText("对齐器: 停止")
            self.alignment_status.setStyleSheet("color: red;")
            
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
        self.update_status(f"当前台词: {cue.id} - {cue.character}")
        
    @Slot(Cue)
    def on_cue_matched(self, cue: Cue):
        """响应对齐器匹配信号"""
        if self.player:
            self.player.go_by_cue_obj(cue)
            
    @Slot(bool)
    def on_alignment_uncertain(self, uncertain: bool):
        """响应对齐器不确定状态"""
        if uncertain:
            self.alignment_status.setText("对齐器: 不确定")
            self.alignment_status.setStyleSheet("color: orange;")
        else:
            self.alignment_status.setText("对齐器: 运行中")
            self.alignment_status.setStyleSheet("color: green;")
            
    def highlight_current_cue(self):
        """高亮当前台词行"""
        if self.current_cue_index < 0:
            return
            
        # 清除之前的高亮
        self.clear_table_highlighting()
        
        # 在剧场模式表格中高亮当前行
        if self.current_cue_index < self.theater_table.rowCount():
            for col in range(self.theater_table.columnCount()):
                item = self.theater_table.item(self.current_cue_index, col)
                if item:
                    item.setBackground(QBrush(QColor(100, 200, 100, 100)))
                    
            # 滚动到当前行
            current_item = self.theater_table.item(self.current_cue_index, 0)
            if current_item:
                self.theater_table.scrollToItem(
                    current_item,
                    QTableWidget.ScrollHint.PositionAtCenter
                )
            
    def clear_table_highlighting(self):
        """清除表格高亮"""
        for row in range(self.theater_table.rowCount()):
            for col in range(self.theater_table.columnCount()):
                item = self.theater_table.item(row, col)
                if item:
                    item.setBackground(QBrush())
                    
    @Slot()
    def on_script_item_double_clicked(self, item):
        """编辑模式表格项双击事件"""
        row = item.row()
        if 0 <= row < len(self.script_data.cues):
            cue = self.script_data.cues[row]
            # 这里可以添加编辑对话框
            logging.info(f"编辑台词: {cue.id} - {cue.line}")
            
    @Slot()
    def on_theater_item_clicked(self, item):
        """剧场模式表格项点击事件"""
        row = item.row()
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
            # 剧场模式使用传统表格，需要手动刷新
            self.populate_theater_table()
            self.update_status("显示已刷新")
            
    @Slot(str)
    def update_status(self, message: str):
        """更新状态栏"""
        self.status_label.setText(message)
        
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
            # 创建G2P转换器
            try:
                from app.core.g2p.phonemizer_g2p import PhonemizerG2P
                g2p_converter = PhonemizerG2P(language='fr-fr')
            except ImportError:
                from app.core.g2p.simple_g2p import SimpleG2P
                g2p_converter = SimpleG2P(language='zh')
                
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
        
        # 更新剧场模式表格
        self.populate_theater_table()
        
    @Slot(str, int, int)
    def on_validation_error(self, message: str, row: int, column: int):
        """处理数据验证错误"""
        self.show_error(f"数据验证错误 (行{row+1}, 列{column+1}): {message}")
        
        # 定位到错误位置
        error_index = self.script_model.index(row, column)
        self.script_view.setCurrentIndex(error_index)
        self.script_view.scrollTo(error_index)
            
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
            
        # 关闭子窗口
        if self.subtitle_window:
            self.subtitle_window.close()
        if self.debug_window:
            self.debug_window.close()
            
        event.accept()


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