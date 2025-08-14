"""
播放控制窗口 - 重构版
管理对齐系统的初始化和运行
"""
import logging
from typing import Optional, List, Dict
from PySide6.QtWidgets import QWidget, QMessageBox
from PySide6.QtCore import Slot

from app.ui.ui_playcontrol import Ui_MainWindow
from app.data.script_data import ScriptData
from app.core.player import SubtitlePlayer
from app.models.models import Cue
from app.core.g2p.g2p_manager import G2PManager
from app.core.alignment_manager import AlignmentManager
from app.core.subtitle_window_manager import SubtitleWindowManager
from app.views.subtitle_window import SubtitleWindow


class PlayControlWindow(QWidget):
    """播放控制窗口 - 管理对齐系统"""
    
    def __init__(self, script_data: Optional[ScriptData] = None, g2p_manager: Optional[G2PManager] = None, parent=None):
        super().__init__(parent)
        
        # 初始化UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        # 数据和管理器
        self.script_data = script_data
        self.g2p_manager = g2p_manager
        
        # 新的对齐管理器
        self.alignment_manager = AlignmentManager(self)
        
        # 播放器（保留用于兼容性）
        self.player: Optional[SubtitlePlayer] = None
        
        # 字幕窗口管理器
        self.subtitle_window_manager: Optional[SubtitleWindowManager] = None
        
        # 独立字幕窗口
        self.standalone_subtitle_window: Optional[SubtitleWindow] = None
        
        # 角色分配相关
        self.character_list: List[str] = []  # 剧本中的角色列表
        self.screen_character_assignments: Dict[int, Optional[str]] = {1: None, 2: None, 3: None}  # 屏幕角色分配
        
        # 状态
        self.current_cue_index = -1
        self.components_ready_count = 0
        # 每个屏幕的语言选择（primary/secondary 都可由下拉选择，默认primary为源语言）
        self.screen_language_selection: Dict[int, Dict[str, Optional[str]]] = {
            1: {"primary": None, "secondary": None},
            2: {"primary": None, "secondary": None},
            3: {"primary": None, "secondary": None},
        }
        # 每个屏幕的隐藏角色名状态
        self.screen_hide_charname: Dict[int, bool] = {
            1: False,
            2: False,
            3: False,
        }
        # 每个屏幕的位置偏移量 (相对于默认位置)
        self.screen_position_offsets: Dict[int, Dict[str, int]] = {
            1: {"x": 0, "y": 0},
            2: {"x": 0, "y": 0},
            3: {"x": 0, "y": 0},
        }
        # 已连接信号的语言下拉框，避免重复连接
        self._connected_lang_combos: set[str] = set()        # 设置窗口
        self.setWindowTitle("播放控制台")
        self.resize(1024, 768)
        
        from PySide6.QtCore import Qt
        self.setWindowFlags(Qt.WindowType.Window)
        
        # 初始化
        self.setup_components()
        self.setup_signals()
        self.update_button_states()
        
        # 更新UI文本
        self.ui.startAligner.setText("开始对齐")
        self.ui.initialNreset.setText("初始化/重置")
        
        # 初始状态：startAligner禁用
        self.ui.startAligner.setEnabled(False)
        
        # 初始化屏幕UI状态
        self.setup_screen_ui_states()
        
        # 初始化字体控件
        self.setup_font_controls()
        
        # 如果有脚本数据，初始化角色列表和comboBox
        if self.script_data:
            self.load_character_list()
            self.setup_character_combo_boxes()
            # 载入语言列表到各subtab的语言下拉框
            self.setup_language_combo_boxes()
        
        logging.info("PlayControl窗口初始化完成")
    
    def setup_components(self):
        """初始化组件"""
        if self.script_data and self.script_data.cues:
            # 创建播放器（保留用于兼容性）
            self.player = SubtitlePlayer(self.script_data.cues)
            
            # 创建字幕窗口管理器
            self.subtitle_window_manager = SubtitleWindowManager(self.player)
            
            # 连接字幕窗口管理器信号
            self.subtitle_window_manager.windowCreated.connect(self.on_window_created)
            self.subtitle_window_manager.windowDestroyed.connect(
                lambda window_id: self.on_window_destroyed(window_id)
            )
            self.subtitle_window_manager.windowShown.connect(
                lambda window_id: self.on_window_shown(window_id)
            )
            self.subtitle_window_manager.windowHidden.connect(
                lambda window_id: self.on_window_hidden(window_id)
            )
        
    def setup_signals(self):
        """设置信号连接"""
        # 按钮信号 - 新的功能分配
        self.ui.initialNreset.clicked.connect(self.initialize_alignment_system)
        self.ui.startAligner.clicked.connect(self.start_alignment)
        self.ui.showAllscrenns.clicked.connect(self.show_all_screens)
        self.ui.hideSubtitle.clicked.connect(self.hide_subtitle)
        
        # 独立字幕窗口按钮（如果存在）
        # if hasattr(self.ui, 'showSubtitleWindow'):
        #     self.ui.showSubtitleWindow.clicked.connect(self.show_standalone_subtitle_window)
        
        # 播放器信号（保留用于兼容性）
        if self.player:
            # 连接统一字幕切换功能
            self.player.cueChanged.connect(self.unified_subtitle_switch)
            
        # 对齐管理器信号
        self.alignment_manager.component_standby.connect(self.on_component_standby)
        self.alignment_manager.all_components_ready.connect(self.on_all_components_ready)
        self.alignment_manager.component_error.connect(self.on_component_error)
        self.alignment_manager.status_changed.connect(self.update_status)
        self.alignment_manager.alignment_started.connect(self.on_alignment_started)
        self.alignment_manager.alignment_stopped.connect(self.on_alignment_stopped)
        
        # 屏幕激活相关信号
        self.setup_screen_signals()
        
        # 字体控件信号
        self.setup_font_signals()
        
        # 位置调整按钮信号
        self.setup_position_signals()
    
    def setup_font_controls(self):
        """初始化字体控件的选项"""
        # 字体列表 - 系统常用字体
        fonts = [
            "Arial", "微软雅黑", "SimSun", "SimHei", "宋体", "黑体", 
            "Times New Roman", "Helvetica", "Calibri", "Source Sans Pro",
            "Noto Sans", "华文细黑", "华文黑体", "苹方", "PingFang SC"
        ]
        
        # 字体大小选项
        sizes = ["12", "14", "16", "18", "20", "24", "28", "32", "36", "48", "64", "72"]
        
        # 字体颜色选项
        font_colors = [
            "白色", "黑色", "红色", "绿色", "蓝色", "黄色", 
            "青色", "洋红色", "橙色", "紫色", "灰色"
        ]
        
        # 背景颜色选项
        bg_colors = [
            "透明", "白色", "黑色", "灰色", "深灰色", 
            "红色", "绿色", "蓝色", "黄色"
        ]
        
        # 为所有subtab设置字体控件选项
        for screen in [1, 2, 3]:
            for subtab in [1, 2]:
                # 字体选择
                font_combo = getattr(self.ui, f'comboBox_font_{screen}_{subtab}', None)
                if font_combo:
                    font_combo.clear()
                    font_combo.addItems(fonts)
                    font_combo.setCurrentText("微软雅黑")  # 默认字体
                
                # 字体大小
                size_combo = getattr(self.ui, f'comboBox_size_{screen}_{subtab}', None)
                if size_combo:
                    size_combo.clear()
                    size_combo.addItems(sizes)
                    size_combo.setCurrentText("24")  # 默认大小
                
                # 字体颜色
                font_color_combo = getattr(self.ui, f'comboBox_font_color_{screen}_{subtab}', None)
                if font_color_combo:
                    font_color_combo.clear()
                    font_color_combo.addItems(font_colors)
                    font_color_combo.setCurrentText("白色")  # 默认颜色
                
                # 背景颜色
                bg_color_combo = getattr(self.ui, f'comboBox_bg_color_{screen}_{subtab}', None)
                if not bg_color_combo:
                    # 处理第一个subtab中背景颜色控件名称不一致的问题
                    if screen == 1 and subtab == 1:
                        bg_color_combo = getattr(self.ui, 'comboBox_bg_color', None)
                if bg_color_combo:
                    bg_color_combo.clear()
                    bg_color_combo.addItems(bg_colors)
                    bg_color_combo.setCurrentText("透明")  # 默认背景
    
    def setup_font_signals(self):
        """设置字体控件的信号连接"""
        for screen in [1, 2, 3]:
            for subtab in [1, 2]:
                # 字体选择信号
                font_combo = getattr(self.ui, f'comboBox_font_{screen}_{subtab}', None)
                if font_combo:
                    font_combo.currentTextChanged.connect(
                        lambda text, s=screen, st=subtab: self.on_font_changed(s, st, text)
                    )
                
                # 字体大小信号
                size_combo = getattr(self.ui, f'comboBox_size_{screen}_{subtab}', None)
                if size_combo:
                    size_combo.currentTextChanged.connect(
                        lambda text, s=screen, st=subtab: self.on_font_size_changed(s, st, text)
                    )
                
                # 字体颜色信号
                font_color_combo = getattr(self.ui, f'comboBox_font_color_{screen}_{subtab}', None)
                if font_color_combo:
                    font_color_combo.currentTextChanged.connect(
                        lambda text, s=screen, st=subtab: self.on_font_color_changed(s, st, text)
                    )
                
                # 背景颜色信号
                bg_color_combo = getattr(self.ui, f'comboBox_bg_color_{screen}_{subtab}', None)
                if not bg_color_combo and screen == 1 and subtab == 1:
                    bg_color_combo = getattr(self.ui, 'comboBox_bg_color', None)
                if bg_color_combo:
                    bg_color_combo.currentTextChanged.connect(
                        lambda text, s=screen, st=subtab: self.on_bg_color_changed(s, st, text)
                    )
    
    def setup_position_signals(self):
        """设置位置调整按钮的信号连接"""
        # 位置调整步长 (像素)
        self.position_step = 10
        
        for screen in [1, 2, 3]:
            for subtab in [1, 2]:
                # 获取按钮名称的变化 - 第一个subtab中有些按钮命名不一致
                if screen == 1 and subtab == 2:
                    # 屏幕1的第二个subtab使用特殊命名
                    up_button = getattr(self.ui, f'toolButton_up_2', None)  # 注意：不是 toolButton_up_1_2
                    down_button = getattr(self.ui, f'toolButton_down_{screen}_{subtab}', None)
                    left_button = getattr(self.ui, f'toolButton_left_{screen}_{subtab}', None)
                    right_button = getattr(self.ui, f'toolButton_right_{screen}_{subtab}', None)
                    center_button = getattr(self.ui, f'toolButton_center_{screen}_{subtab}', None)
                else:
                    # 标准命名
                    up_button = getattr(self.ui, f'toolButton_up_{screen}_{subtab}', None)
                    down_button = getattr(self.ui, f'toolButton_down_{screen}_{subtab}', None)
                    left_button = getattr(self.ui, f'toolButton_left_{screen}_{subtab}', None)
                    right_button = getattr(self.ui, f'toolButton_right_{screen}_{subtab}', None)
                    center_button = getattr(self.ui, f'toolButton_center_{screen}_{subtab}', None)
                
                # 连接信号
                if up_button:
                    up_button.clicked.connect(
                        lambda checked, s=screen, st=subtab: self.adjust_subtitle_position(s, st, 'up')
                    )
                if down_button:
                    down_button.clicked.connect(
                        lambda checked, s=screen, st=subtab: self.adjust_subtitle_position(s, st, 'down')
                    )
                if left_button:
                    left_button.clicked.connect(
                        lambda checked, s=screen, st=subtab: self.adjust_subtitle_position(s, st, 'left')
                    )
                if right_button:
                    right_button.clicked.connect(
                        lambda checked, s=screen, st=subtab: self.adjust_subtitle_position(s, st, 'right')
                    )
                if center_button:
                    center_button.clicked.connect(
                        lambda checked, s=screen, st=subtab: self.reset_subtitle_position(s, st)
                    )
    
    def setup_screen_signals(self):
        """设置屏幕相关的信号连接"""
        # 屏幕激活信号
        if hasattr(self.ui, 'activate_screen_2'):
            self.ui.activate_screen_2.toggled.connect(self.on_screen_2_toggled)
        if hasattr(self.ui, 'activate_screen_3'):
            self.ui.activate_screen_3.toggled.connect(self.on_screen_3_toggled)
        
        # 第二语言激活信号
        if hasattr(self.ui, 'activate_2nd_lang_1'):
            self.ui.activate_2nd_lang_1.toggled.connect(self.on_2nd_lang_1_toggled)
        if hasattr(self.ui, 'activate_2nd_lang_2'):
            self.ui.activate_2nd_lang_2.toggled.connect(self.on_2nd_lang_2_toggled)
        if hasattr(self.ui, 'activate_2nd_lang_3'):
            self.ui.activate_2nd_lang_3.toggled.connect(self.on_2nd_lang_3_toggled)
        
        # 隐藏角色名信号
        if hasattr(self.ui, 'hideCharname_1'):
            self.ui.hideCharname_1.toggled.connect(self.on_hide_charname_1_toggled)
        if hasattr(self.ui, 'hideCharname_2'):
            self.ui.hideCharname_2.toggled.connect(self.on_hide_charname_2_toggled)
        if hasattr(self.ui, 'hideCharname_3'):
            self.ui.hideCharname_3.toggled.connect(self.on_hide_charname_3_toggled)
        
        # 字幕窗口显示按钮信号
        if hasattr(self.ui, 'pushButton_showscreen_1'):
            self.ui.pushButton_showscreen_1.clicked.connect(lambda: self.toggle_subtitle_window(1))
        if hasattr(self.ui, 'pushButton_showscreen_2'):
            self.ui.pushButton_showscreen_2.clicked.connect(lambda: self.toggle_subtitle_window(2))
        if hasattr(self.ui, 'pushButton_showscreen_3'):
            self.ui.pushButton_showscreen_3.clicked.connect(lambda: self.toggle_subtitle_window(3))
    
    def setup_screen_ui_states(self):
        """初始化屏幕UI状态"""
        # 屏幕1：默认激活且禁用
        if hasattr(self.ui, 'activate_screen_1'):
            self.ui.activate_screen_1.setChecked(True)
            self.ui.activate_screen_1.setEnabled(False)
        
        # 屏幕2和3：默认未激活
        if hasattr(self.ui, 'activate_screen_2'):
            self.ui.activate_screen_2.setChecked(False)
            self.update_screen_2_state(False)
        
        if hasattr(self.ui, 'activate_screen_3'):
            self.ui.activate_screen_3.setChecked(False)
            self.update_screen_3_state(False)
        
        # 第二语言标签页：默认禁用
        self.update_2nd_lang_tab_state(1, False)
        self.update_2nd_lang_tab_state(2, False)
        self.update_2nd_lang_tab_state(3, False)
        
        # 初始化屏幕按钮文本
        self.initialize_screen_button_texts()
    
    def initialize_screen_button_texts(self):
        """初始化屏幕按钮的文本"""
        # 设置所有屏幕按钮的初始文本为"显示屏幕 X"
        for window_id in [1, 2, 3]:
            self.update_screen_button_text(window_id, False)
        
        # 设置显示所有窗口按钮的初始文本
        if hasattr(self.ui, 'showAllscrenns'):
            self.ui.showAllscrenns.setText("显示所有窗口")
    
    def on_window_destroyed(self, window_id: int):
        """窗口销毁时的回调"""
        self.update_status(f"字幕窗口 {window_id} 已销毁")
        self.update_screen_button_text(window_id, False)
        
        # 检查是否需要更新"显示所有窗口"按钮
        self.check_and_update_show_all_button()
    
    def on_window_shown(self, window_id: int):
        """窗口显示时的回调"""
        self.update_status(f"字幕窗口 {window_id} 已显示")
        self.update_screen_button_text(window_id, True)
        # 应用当前语言选择到窗口
        self._apply_language_selection_to_window(window_id)
    
    def on_window_hidden(self, window_id: int):
        """窗口隐藏时的回调"""
        self.update_status(f"字幕窗口 {window_id} 已隐藏")
        self.update_screen_button_text(window_id, False)
        
        # 检查是否需要更新"显示所有窗口"按钮
        self.check_and_update_show_all_button()

    def on_window_created(self, window_id: int):
        """字幕窗口创建后，应用语言设置"""
        self.update_status(f"字幕窗口 {window_id} 已创建")
        # 初始化语言设置
        self._apply_language_selection_to_window(window_id)
    
    def check_and_update_show_all_button(self):
        """检查并更新显示所有窗口按钮的状态"""
        if not self.subtitle_window_manager or not hasattr(self.ui, 'showAllscrenns'):
            return
        
        # 检查是否有任何窗口可见
        any_visible = any(
            self.subtitle_window_manager.is_window_visible(window_id) 
            for window_id in [1, 2, 3]
            if self.subtitle_window_manager.get_window(window_id)
        )
        
        if any_visible:
            self.ui.showAllscrenns.setText("隐藏所有窗口")
        else:
            self.ui.showAllscrenns.setText("显示所有窗口")
    
    def set_script_data(self, script_data: ScriptData):
        """设置剧本数据"""
        self.script_data = script_data
        self.setup_components()
        self.update_button_states()
        # 刷新角色与语言相关下拉框
        self.load_character_list()
        self.setup_character_combo_boxes()
        self.setup_language_combo_boxes()
    
    @Slot()
    def initialize_alignment_system(self):
        """初始化对齐系统 - initialNreset按钮的新功能"""
        if not self.script_data or not self.script_data.cues:
            self.show_error("请先加载剧本数据")
            return
        
        self.update_status("="*50)
        self.update_status("正在初始化对齐系统...")
        self.components_ready_count = 0
        
        # 使用AlignmentManager初始化组件
        success = self.alignment_manager.initialize_components(
            script_data=self.script_data,
            stt_engine_type="vosk"  # 默认使用Vosk引擎
        )
        
        if not success:
            self.show_error("对齐系统初始化失败")
            return
        
        # 更新按钮状态 - startAligner仍然禁用，等待所有组件就绪
        self.update_button_states()
        logging.info("对齐系统初始化请求已发送")
    
    @Slot(str)
    def on_component_standby(self, component_name: str):
        """组件就绪信号处理"""
        self.components_ready_count += 1
        self.update_status(f"✅ {component_name} 已就绪 ({self.components_ready_count}/4)")
        logging.info(f"组件 {component_name} 已就绪")
    
    @Slot()
    def on_all_components_ready(self):
        """所有组件就绪时的处理"""
        self.update_status("🎉 所有组件已就绪，可以开始对齐！")
        self.update_status("="*50)
        self.update_button_states()  # 这将启用startAligner按钮
        logging.info("所有对齐组件已就绪")
    
    @Slot(str, str)
    def on_component_error(self, component_name: str, error_msg: str):
        """组件错误处理"""
        self.show_error(f"{component_name} 错误: {error_msg}")
        self.update_button_states()
    
    @Slot()
    def on_alignment_started(self):
        """对齐开始时的处理"""
        self.update_status("🎤 对齐系统已启动，音频闸口已打开")
        self.ui.startAligner.setText("停止对齐")
        self.update_button_states()
        logging.info("对齐系统已启动")
    
    @Slot()
    def on_alignment_stopped(self):
        """对齐停止时的处理"""
        self.update_status("⏹️ 对齐系统已停止，音频闸口已关闭")
        self.ui.startAligner.setText("开始对齐")
        self.update_button_states()
        logging.info("对齐系统已停止")
    
    @Slot()
    def start_alignment(self):
        """开始/停止对齐 - startAligner按钮功能"""
        if self.alignment_manager.is_running:
            # 当前在运行，执行停止
            success = self.alignment_manager.stop_alignment()
            if not success:
                self.show_error("停止对齐失败")
        else:
            # 当前未运行，执行开始
            if not self.alignment_manager.are_all_components_ready():
                self.show_error("组件未就绪，请先点击'初始化/重置'按钮")
                return
            
            success = self.alignment_manager.start_alignment()
            if not success:
                self.show_error("启动对齐失败")
    
    @Slot()
    def show_all_screens(self):
        """显示/隐藏所有屏幕 - 智能切换功能"""
        if not self.subtitle_window_manager:
            self.update_status("字幕窗口管理器未初始化")
            return
        
        # 检查当前状态 - 是否有窗口显示
        current_button_text = self.ui.showAllscrenns.text()
        
        if "隐藏" in current_button_text:
            # 当前是显示状态，执行隐藏操作
            self.subtitle_window_manager.hide_all_windows()
            self.ui.showAllscrenns.setText("显示所有窗口")
            self.update_status("已隐藏所有字幕窗口")
            
            # 更新各个屏幕按钮状态
            self.update_screen_button_text(1, False)
            self.update_screen_button_text(2, False)
            self.update_screen_button_text(3, False)
        else:
            # 当前是隐藏状态，执行显示操作
            # 检查并创建1,2,3号窗口
            for window_id in [1, 2, 3]:
                if not self.subtitle_window_manager.get_window(window_id):
                    # 窗口不存在，创建它
                    if self.subtitle_window_manager.create_window(window_id):
                        print(f"[PlayControl] Created window {window_id}")
                    else:
                        print(f"[PlayControl] Failed to create window {window_id}")
                        continue
                
                # 显示窗口
                if self.subtitle_window_manager.show_window(window_id):
                    print(f"[PlayControl] Showed window {window_id}")
                    self.update_screen_button_text(window_id, True)
            
            self.ui.showAllscrenns.setText("隐藏所有窗口")
            self.update_status("已显示所有字幕窗口（1,2,3）")
    
    def toggle_subtitle_window(self, window_id: int):
        """切换指定窗口的显示/隐藏状态"""
        if not self.subtitle_window_manager:
            self.update_status("字幕窗口管理器未初始化")
            return
        
        window = self.subtitle_window_manager.get_window(window_id)
        
        if window and self.subtitle_window_manager.is_window_visible(window_id):
            # 窗口存在且可见，隐藏它
            if self.subtitle_window_manager.hide_window(window_id):
                self.update_screen_button_text(window_id, False)
                self.update_status(f"已隐藏字幕窗口 {window_id}")
        else:
            # 窗口不存在或不可见，创建并显示
            if not window:
                if not self.subtitle_window_manager.create_window(window_id):
                    self.update_status(f"创建字幕窗口 {window_id} 失败")
                    return
            
            if self.subtitle_window_manager.show_window(window_id):
                self.update_screen_button_text(window_id, True)
                self.update_status(f"已显示字幕窗口 {window_id}")
    
    def update_screen_button_text(self, window_id: int, is_visible: bool):
        """更新屏幕按钮的文本"""
        button_name = f"pushButton_showscreen_{window_id}"
        
        if hasattr(self.ui, button_name):
            button = getattr(self.ui, button_name)
            if is_visible:
                button.setText(f"隐藏屏幕 {window_id}")
            else:
                button.setText(f"显示屏幕 {window_id}")
    
    @Slot()
    def hide_subtitle(self):
        """隐藏字幕"""
        if self.subtitle_window_manager:
            self.subtitle_window_manager.hide_all_windows()
            self.update_status("已隐藏所有字幕窗口")
        else:
            self.update_status("字幕窗口管理器未初始化")
    
    @Slot()
    def show_standalone_subtitle_window(self):
        """显示独立字幕窗口"""
        if not self.script_data or not self.script_data.cues:
            self.show_error("请先加载剧本")
            return
            
        if self.standalone_subtitle_window is None:
            # 创建带播放器的字幕窗口
            if not self.player:
                self.player = SubtitlePlayer(self.script_data.cues)
            self.standalone_subtitle_window = SubtitleWindow(self.player)
            
        self.standalone_subtitle_window.show()
        self.standalone_subtitle_window.raise_()
        self.standalone_subtitle_window.activateWindow()
        self.update_status("独立字幕窗口已显示")
    
    @Slot()
    def on_cue_changed(self, cue: Cue):
        """当前cue变化时的处理"""
        self.current_cue_index = cue.id if cue else -1
        character = cue.character if cue else "无"
        line = cue.line[:50] + "..." if cue and len(cue.line) > 50 else cue.line if cue else ""
        self.update_status(f"当前cue: [{character}] {line}")
    
    def update_button_states(self):
        """更新按钮状态"""
        has_data = self.script_data is not None and bool(self.script_data.cues)
        
        # initialNreset按钮 - 只要有数据就可以点击
        self.ui.initialNreset.setEnabled(has_data)
        
        # startAligner按钮逻辑
        is_ready = self.alignment_manager.are_all_components_ready()
        is_running = self.alignment_manager.is_running
        
        if is_running:
            # 运行中时，按钮可点击用于停止
            self.ui.startAligner.setEnabled(True)
            self.ui.startAligner.setText("停止对齐")
        elif is_ready:
            # 就绪但未运行时，按钮可点击用于开始
            self.ui.startAligner.setEnabled(True)
            self.ui.startAligner.setText("开始对齐")
        else:
            # 未就绪时，按钮禁用
            self.ui.startAligner.setEnabled(False)
            self.ui.startAligner.setText("开始对齐 (未就绪)")
        
        # 其他按钮状态
        self.ui.showAllscrenns.setEnabled(has_data)
        self.ui.hideSubtitle.setEnabled(has_data)
    
    def update_status(self, message: str):
        """更新状态显示"""
        if hasattr(self.ui, 'textBrowser_status'):
            current_text = self.ui.textBrowser_status.toPlainText()
            timestamp = logging.Formatter().formatTime(logging.LogRecord(
                "", 0, "", 0, "", (), None), "%H:%M:%S")
            new_line = f"[{timestamp}] {message}"
            
            # 限制显示行数，保留最新的100行
            lines = current_text.split('\\n') if current_text else []
            lines.append(new_line)
            if len(lines) > 100:
                lines = lines[-100:]
            
            self.ui.textBrowser_status.setPlainText('\\n'.join(lines))
            # 滚动到底部
            cursor = self.ui.textBrowser_status.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.ui.textBrowser_status.setTextCursor(cursor)
        
        logging.info(f"PlayControl: {message}")

    # ==================== 语言列表功能 ====================

    def setup_language_combo_boxes(self):
        """
        为每个 subtab 的 comboBox_lang_*_* 载入剧本文件中的语言列表。
        语言列表获取方式参考 main_console.py：优先从 document.meta.language，
        如不存在则从文档/台词翻译中汇总。
        """
        try:
            languages = self._get_script_languages()  # [(display_name, code), ...]
            if not languages:
                return

            # 所有语言下拉框对象名称
            combo_names = [
                'comboBox_lang_1_1', 'comboBox_lang_1_2',
                'comboBox_lang_2_1', 'comboBox_lang_2_2',
                'comboBox_lang_3_1', 'comboBox_lang_3_2'
            ]

            # 源语言代码（作为默认primary选择）
            source_code = self._get_source_language_code()

            for name in combo_names:
                combo = getattr(self.ui, name, None)
                if not combo:
                    continue
                # 填充前清空
                try:
                    combo.blockSignals(True)
                except Exception:
                    pass
                combo.clear()
                for display, code in languages:
                    combo.addItem(display, code)
                # 默认选择：主语言tab选源语言；第二语言tab选第一个非源语言
                if combo.count() > 0:
                    try:
                        # 判断是哪个屏和第几个tab
                        # 名称格式：comboBox_lang_{screen}_{tab}
                        parts = name.split('_')
                        screen_id = int(parts[2])
                        tab_idx = int(parts[3])  # 1或2
                        if tab_idx == 1:
                            # 主语言：默认选择源语言，但允许用户后续更改
                            if source_code:
                                # 找到源语言对应索引
                                idx = next((i for i in range(combo.count()) if combo.itemData(i) == source_code), 0)
                                combo.setCurrentIndex(idx)
                                # 记录
                                self.screen_language_selection[screen_id]["primary"] = source_code
                            else:
                                combo.setCurrentIndex(0)
                                self.screen_language_selection[screen_id]["primary"] = combo.currentData()
                        else:
                            # 第二语言：选择第一个非源语言
                            idx = 0
                            if source_code:
                                for i in range(combo.count()):
                                    if combo.itemData(i) != source_code:
                                        idx = i
                                        break
                            combo.setCurrentIndex(idx)
                            self.screen_language_selection[screen_id]["secondary"] = combo.itemData(idx)
                    except Exception:
                        combo.setCurrentIndex(0)
                try:
                    combo.blockSignals(False)
                except Exception:
                    pass

            # 连接主/第二语言下拉框信号
            self._connect_primary_language_combo_signals()
            self._connect_language_combo_signals()
        except Exception as e:
            logging.error(f"设置语言下拉框失败: {e}")

    def _get_script_languages(self):
        """
        返回脚本中的语言列表，形式为 [(display_name, code), ...]
        参考 main_console._get_language_display_name 的映射生成友好名称。
        """
        if not self.script_data:
            return []

        lang_codes = []
        try:
            # 优先从增强文档的 meta.language 获取
            doc = getattr(self.script_data, 'document', None)
            meta = getattr(doc, 'meta', None) if doc else None
            meta_langs = getattr(meta, 'language', None) if meta else None
            if meta_langs:
                lang_codes = list(meta_langs)

            # 兜底：从文档聚合所有可用语言
            if (not lang_codes) and doc and hasattr(doc, 'get_all_languages'):
                try:
                    lang_codes = doc.get_all_languages()
                except Exception:
                    lang_codes = []

            # 最后兜底：扫描每条台词的 translation keys
            if not lang_codes:
                codes_set = set()
                for cue in getattr(self.script_data, 'cues', []) or []:
                    if getattr(cue, 'translation', None):
                        codes_set.update(cue.translation.keys())
                lang_codes = sorted(list(codes_set))
        except Exception:
            lang_codes = []

        # 去重并保持顺序
        seen = set()
        ordered_codes = []
        for code in lang_codes:
            c = (code or '').strip()
            if c and c not in seen:
                seen.add(c)
                ordered_codes.append(c)

        return [(self._get_language_display_name(code), code) for code in ordered_codes]

    def _get_language_display_name(self, lang_code: str) -> str:
        """与 main_console 中逻辑一致：将语言代码映射为友好名称。"""
        language_names = {
            'en': '英语', 'zh': '中文', 'fr': '法语', 'de': '德语', 'es': '西班牙语',
            'it': '意大利语', 'ja': '日语', 'ko': '韩语', 'ru': '俄语', 'pt': '葡萄牙语',
            'ar': '阿拉伯语', 'hi': '印地语', 'th': '泰语', 'vi': '越南语'
        }
        base_code = (lang_code or '').split('-')[0].lower()
        # 优先显示带地区码的原样代码，名称用基础映射或代码大写
        return language_names.get(base_code, (lang_code or '').upper())

    def _get_source_language_code(self) -> Optional[str]:
        """返回源语言代码：优先 document.meta.language[0]，否则取列表第一项。"""
        doc = getattr(self.script_data, 'document', None) if self.script_data else None
        if doc and getattr(doc, 'meta', None) and getattr(doc.meta, 'language', None):
            langs = doc.meta.language
            if isinstance(langs, list) and langs:
                return (langs[0] or '').strip() or None
        # 退化：从已填充的下拉或聚合列表中取第一个
        langs = self._get_script_languages()
        if langs:
            return langs[0][1]
        return None

    def _connect_language_combo_signals(self):
        """连接第二语言选择变更信号，只连接一次。"""
        mapping = {
            1: getattr(self.ui, 'comboBox_lang_1_2', None),
            2: getattr(self.ui, 'comboBox_lang_2_2', None),
            3: getattr(self.ui, 'comboBox_lang_3_2', None),
        }
        for screen_id, combo in mapping.items():
            if not combo:
                continue
            key = f"{combo.objectName()}"
            if key in self._connected_lang_combos:
                continue
            combo.currentIndexChanged.connect(
                lambda _idx, sid=screen_id, c=combo: self.on_second_language_changed(sid, c)
            )
            self._connected_lang_combos.add(key)

    def _connect_primary_language_combo_signals(self):
        """连接主语言选择变更信号，只连接一次。"""
        mapping = {
            1: getattr(self.ui, 'comboBox_lang_1_1', None),
            2: getattr(self.ui, 'comboBox_lang_2_1', None),
            3: getattr(self.ui, 'comboBox_lang_3_1', None),
        }
        for screen_id, combo in mapping.items():
            if not combo:
                continue
            key = f"{combo.objectName()}"
            if key in self._connected_lang_combos:
                continue
            combo.currentIndexChanged.connect(
                lambda _idx, sid=screen_id, c=combo: self.on_primary_language_changed(sid, c)
            )
            self._connected_lang_combos.add(key)

    def on_second_language_changed(self, screen_id: int, combo):
        """第二语言选择变化。"""
        code = None
        try:
            code = combo.currentData()
        except Exception:
            try:
                code = combo.currentText()
            except Exception:
                code = None
        self.screen_language_selection.setdefault(screen_id, {}).update({"secondary": code})
        # 应用到窗口并刷新显示
        self._apply_language_selection_to_window(screen_id)
        self.update_subtitle_display_for_screen(screen_id)

    def on_primary_language_changed(self, screen_id: int, combo):
        """主语言选择变化。"""
        code = None
        try:
            code = combo.currentData()
        except Exception:
            try:
                code = combo.currentText()
            except Exception:
                code = None
        self.screen_language_selection.setdefault(screen_id, {}).update({"primary": code})
        # 应用到窗口并刷新显示
        self._apply_language_selection_to_window(screen_id)
        self.update_subtitle_display_for_screen(screen_id)

    def _apply_language_selection_to_window(self, screen_id: int):
        """将当前屏幕的语言选择应用到窗口对象。"""
        if not self.subtitle_window_manager:
            return
        window = self.subtitle_window_manager.get_window(screen_id)
        if not window:
            return
        # 使用用户在主语言下拉中选择的语言（默认值已在初始化时设置为源语言）
        selected = self.screen_language_selection.get(screen_id, {})
        primary = selected.get("primary") or self._get_source_language_code()
        secondary = selected.get("secondary")
        try:
            if hasattr(window, 'set_languages'):
                window.set_languages(primary, secondary)
            # 应用隐藏角色名设置
            if hasattr(window, 'set_hide_character_name'):
                hide_charname = self.screen_hide_charname.get(screen_id, False)
                window.set_hide_character_name(hide_charname)
        except Exception as e:
            logging.warning(f"应用语言到窗口失败: {e}")
    
    def show_error(self, message: str):
        """显示错误信息"""
        self.update_status(f"❌ 错误: {message}")
        QMessageBox.critical(self, "错误", message)
        logging.error(f"PlayControl Error: {message}")
        
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 清理字幕窗口管理器
        if self.subtitle_window_manager:
            self.subtitle_window_manager.destroy_all_windows()
        
        # 清理对齐管理器
        if self.alignment_manager:
            self.alignment_manager.cleanup_components()
            
        event.accept()
        logging.info("PlayControl窗口已关闭")
    
    # 屏幕激活相关方法
    @Slot(bool)
    def on_screen_2_toggled(self, checked: bool):
        """屏幕2激活状态改变"""
        self.update_screen_2_state(checked)
        
        # 更新播放器状态
        if self.player:
            self.player.set_window_active(2, checked)
        
        self.update_status(f"屏幕2 {'激活' if checked else '禁用'}")
    
    @Slot(bool)
    def on_screen_3_toggled(self, checked: bool):
        """屏幕3激活状态改变"""
        self.update_screen_3_state(checked)
        
        # 更新播放器状态
        if self.player:
            self.player.set_window_active(3, checked)
        
        self.update_status(f"屏幕3 {'激活' if checked else '禁用'}")
    
    @Slot(bool)
    def on_2nd_lang_1_toggled(self, checked: bool):
        """屏幕1第二语言激活状态改变"""
        self.update_2nd_lang_tab_state(1, checked)
        # 更新播放器状态
        if self.player:
            self.player.set_second_language_active(1, checked)
        # 应用语言设置到窗口并刷新
        self._apply_language_selection_to_window(1)
        self.update_subtitle_display_for_screen(1)
        self.update_status(f"屏幕1第二语言 {'激活' if checked else '禁用'}")
    
    @Slot(bool)
    def on_2nd_lang_2_toggled(self, checked: bool):
        """屏幕2第二语言激活状态改变"""
        self.update_2nd_lang_tab_state(2, checked)
        # 更新播放器状态
        if self.player:
            self.player.set_second_language_active(2, checked)
        # 应用语言设置到窗口并刷新
        self._apply_language_selection_to_window(2)
        self.update_subtitle_display_for_screen(2)
        self.update_status(f"屏幕2第二语言 {'激活' if checked else '禁用'}")
    
    @Slot(bool)
    def on_2nd_lang_3_toggled(self, checked: bool):
        """屏幕3第二语言激活状态改变"""
        self.update_2nd_lang_tab_state(3, checked)
        # 更新播放器状态
        if self.player:
            self.player.set_second_language_active(3, checked)
        # 应用语言设置到窗口并刷新
        self._apply_language_selection_to_window(3)
        self.update_subtitle_display_for_screen(3)
        self.update_status(f"屏幕3第二语言 {'激活' if checked else '禁用'}")
    
    @Slot(bool)
    def on_hide_charname_1_toggled(self, checked: bool):
        """屏幕1隐藏角色名状态改变"""
        self.screen_hide_charname[1] = checked
        # 应用设置到窗口并刷新
        self._apply_language_selection_to_window(1)
        self.update_subtitle_display_for_screen(1)
        self.update_status(f"屏幕1角色名 {'隐藏' if checked else '显示'}")
    
    @Slot(bool)
    def on_hide_charname_2_toggled(self, checked: bool):
        """屏幕2隐藏角色名状态改变"""
        self.screen_hide_charname[2] = checked
        # 应用设置到窗口并刷新
        self._apply_language_selection_to_window(2)
        self.update_subtitle_display_for_screen(2)
        self.update_status(f"屏幕2角色名 {'隐藏' if checked else '显示'}")
    
    @Slot(bool)
    def on_hide_charname_3_toggled(self, checked: bool):
        """屏幕3隐藏角色名状态改变"""
        self.screen_hide_charname[3] = checked
        # 应用设置到窗口并刷新
        self._apply_language_selection_to_window(3)
        self.update_subtitle_display_for_screen(3)
        self.update_status(f"屏幕3角色名 {'隐藏' if checked else '显示'}")
    
    def update_screen_2_state(self, enabled: bool):
        """更新屏幕2的UI状态"""
        # 屏幕2的所有UI元素（除了activate_screen_2）
        widgets_to_toggle = [
            'activate_2nd_lang_2', 'hideCharname_2', 'screen_AsignTo_2', 'comboBox_screen_assign_2', 
            'pushButton_showscreen_2', 'lang_subtabs_2'
        ]
        
        for widget_name in widgets_to_toggle:
            if hasattr(self.ui, widget_name):
                widget = getattr(self.ui, widget_name)
                widget.setEnabled(enabled)
    
    def update_screen_3_state(self, enabled: bool):
        """更新屏幕3的UI状态"""
        # 屏幕3的所有UI元素（除了activate_screen_3）
        widgets_to_toggle = [
            'activate_2nd_lang_3', 'hideCharname_3', 'label_tab3_assign', 'comboBox_screen_assign_3', 
            'pushButton_showscreen_3', 'lang_subtabs_3'
        ]
        
        for widget_name in widgets_to_toggle:
            if hasattr(self.ui, widget_name):
                widget = getattr(self.ui, widget_name)
                widget.setEnabled(enabled)
    
    def update_2nd_lang_tab_state(self, screen_num: int, enabled: bool):
        """更新第二语言标签页的状态"""
        if screen_num == 1:
            tab_widget = getattr(self.ui, 'lang_subtabs_1', None)
            tab_name = 'sub_lang_1_2'
        elif screen_num == 2:
            tab_widget = getattr(self.ui, 'lang_subtabs_2', None)
            tab_name = 'sub_lang_2_2'
        elif screen_num == 3:
            tab_widget = getattr(self.ui, 'lang_subtabs_3', None)
            tab_name = 'sub_lang_3_2'
        else:
            return
        
        if tab_widget and hasattr(self.ui, tab_name):
            # 查找并禁用/启用第二语言标签页
            for i in range(tab_widget.count()):
                widget = tab_widget.widget(i)
                if widget and widget.objectName() == tab_name:
                    tab_widget.setTabEnabled(i, enabled)
                    break
    
    # ==================== 角色分配功能 ====================
    
    def load_character_list(self):
        """从剧本数据中加载角色列表"""
        if not self.script_data or not self.script_data.cues:
            return
        
        # 提取所有非空的角色名
        characters = set()
        for cue in self.script_data.cues:
            if cue.character and cue.character.strip():
                characters.add(cue.character.strip())
        
        # 转换为排序的列表
        self.character_list = sorted(list(characters))
        print(f"[PlayControl] 加载了 {len(self.character_list)} 个角色: {self.character_list}")
    
    def setup_character_combo_boxes(self):
        """设置角色分配下拉框"""
        if not self.character_list:
            return
        
        # 为每个ComboBox设置选项
        combo_boxes = [
            self.ui.comboBox_screen_assign_1,
            self.ui.comboBox_screen_assign_2,
            self.ui.comboBox_screen_assign_3
        ]
        
        for i, combo_box in enumerate(combo_boxes, 1):
            if combo_box:
                # 清空现有选项
                combo_box.clear()
                
                # 添加"All"选项
                combo_box.addItem("All")
                
                # 添加角色选项
                for character in self.character_list:
                    combo_box.addItem(character)
                
                # 设置默认选择为"All"
                combo_box.setCurrentText("All")
                
                # 连接信号
                combo_box.currentTextChanged.connect(
                    lambda text, screen_id=i: self.on_character_assignment_changed(screen_id, text)
                )
                
                print(f"[PlayControl] 已设置屏幕 {i} 的角色选择框")
    
    def on_character_assignment_changed(self, screen_id: int, character: str):
        """角色分配变化处理"""
        # 更新分配记录
        if character == "All" or character == "":
            self.screen_character_assignments[screen_id] = None
        else:
            self.screen_character_assignments[screen_id] = character
        
        print(f"[PlayControl] 屏幕 {screen_id} 分配给角色: {character}")
        
        # 如果窗口已创建且可见，更新其显示
        if self.subtitle_window_manager:
            window = self.subtitle_window_manager.get_window(screen_id)
            if window and self.subtitle_window_manager.is_window_visible(screen_id):
                # 强制更新当前字幕显示
                self.update_subtitle_display_for_screen(screen_id)
    
    def update_subtitle_display_for_screen(self, screen_id: int):
        """更新指定屏幕的字幕显示"""
        if not self.subtitle_window_manager:
            return
        
        window = self.subtitle_window_manager.get_window(screen_id)
        if not window:
            return
        
        # 获取当前播放的Cue
        current_cue = None
        if self.player and self.player.current_cue:
            current_cue = self.player.current_cue
        elif self.script_data and self.script_data.cues and self.current_cue_index >= 0:
            if self.current_cue_index < len(self.script_data.cues):
                current_cue = self.script_data.cues[self.current_cue_index]
        
        if not current_cue:
            return
        
        # 检查角色分配
        assigned_character = self.screen_character_assignments.get(screen_id)
        
        if assigned_character is None:
            # 显示All模式 - 显示当前Cue
            window.display_cue(current_cue)
        else:
            # 角色过滤模式
            if current_cue.character and current_cue.character.strip() == assigned_character:
                # 当前Cue属于该角色，显示
                window.display_cue(current_cue)
            else:
                # 当前Cue不属于该角色，查找该角色的最近台词或清空显示
                self.display_character_nearest_cue(screen_id, assigned_character)
    
    def display_character_nearest_cue(self, screen_id: int, character: str):
        """为指定屏幕显示角色的最近台词"""
        if not self.subtitle_window_manager or not self.script_data:
            return
        
        window = self.subtitle_window_manager.get_window(screen_id)
        if not window:
            return
        
        # 获取当前播放位置
        current_index = self.current_cue_index
        if self.player:
            current_index = self.player.current_index
        
        # 查找该角色在当前位置之前的最后一条台词
        last_character_cue = None
        for i in range(min(current_index + 1, len(self.script_data.cues))):
            cue = self.script_data.cues[i]
            if cue.character and cue.character.strip() == character:
                last_character_cue = cue
        
        if last_character_cue:
            # 显示该角色的最后一条台词
            window.display_cue(last_character_cue)
        else:
            # 该角色还没有台词，什么都不显示（空白）
            # 创建一个空的Cue来清空显示
            from app.models.models import Cue
            empty_cue = Cue(
                id=-1,
                character="",
                line="",
                pure_line="",
                phonemes=""
            )
            window.display_cue(empty_cue)
    
    def unified_subtitle_switch(self, cue: Cue):
        """统一的字幕切换接口 - 控制所有3个字幕窗口"""
        if not self.subtitle_window_manager:
            return
        
        # 更新当前播放位置
        if cue:
            # 查找Cue的索引
            for i, script_cue in enumerate(self.script_data.cues if self.script_data else []):
                if script_cue.id == cue.id:
                    self.current_cue_index = i
                    break
        
        # 为每个活跃的屏幕更新显示
        for screen_id in [1, 2, 3]:
            if self.subtitle_window_manager.is_window_visible(screen_id):
                self.update_subtitle_display_for_screen(screen_id)
    
    # ========== 字体控件信号处理方法 ==========
    
    @Slot(str)
    def on_font_changed(self, screen: int, subtab: int, font_name: str):
        """字体选择变化处理"""
        self.update_status(f"屏幕{screen}语言{subtab} 字体已更改为: {font_name}")
        self.apply_font_settings_to_window(screen, subtab)
    
    @Slot(str)
    def on_font_size_changed(self, screen: int, subtab: int, size: str):
        """字体大小变化处理"""
        self.update_status(f"屏幕{screen}语言{subtab} 字体大小已更改为: {size}")
        self.apply_font_settings_to_window(screen, subtab)
    
    @Slot(str) 
    def on_font_color_changed(self, screen: int, subtab: int, color: str):
        """字体颜色变化处理"""
        self.update_status(f"屏幕{screen}语言{subtab} 字体颜色已更改为: {color}")
        self.apply_font_settings_to_window(screen, subtab)
    
    @Slot(str)
    def on_bg_color_changed(self, screen: int, subtab: int, color: str):
        """背景颜色变化处理"""
        self.update_status(f"屏幕{screen}语言{subtab} 背景颜色已更改为: {color}")
        self.apply_font_settings_to_window(screen, subtab)
    
    def apply_font_settings_to_window(self, screen: int, subtab: int):
        """将字体设置应用到字幕窗口"""
        if not self.subtitle_window_manager:
            return
        
        window = self.subtitle_window_manager.get_window(screen)
        if not window:
            return
        
        # 获取当前设置
        font_settings = self.get_font_settings(screen, subtab)
        
        # 检查是否是第二语言标签页
        is_second_lang = (subtab == 2)
        
        # 应用设置到窗口
        if hasattr(window, 'apply_font_settings'):
            window.apply_font_settings(font_settings, is_second_lang)
        
        print(f"[PlayControl] 已应用字体设置到屏幕{screen}语言{subtab}: {font_settings}")
    
    def get_font_settings(self, screen: int, subtab: int) -> Dict[str, str]:
        """获取指定屏幕和语言标签的字体设置"""
        settings = {}
        
        # 字体名称
        font_combo = getattr(self.ui, f'comboBox_font_{screen}_{subtab}', None)
        if font_combo:
            settings['font_family'] = font_combo.currentText()
        
        # 字体大小
        size_combo = getattr(self.ui, f'comboBox_size_{screen}_{subtab}', None)
        if size_combo:
            settings['font_size'] = size_combo.currentText()
        
        # 字体颜色
        font_color_combo = getattr(self.ui, f'comboBox_font_color_{screen}_{subtab}', None)
        if font_color_combo:
            settings['font_color'] = font_color_combo.currentText()
        
        # 背景颜色
        bg_color_combo = getattr(self.ui, f'comboBox_bg_color_{screen}_{subtab}', None)
        if not bg_color_combo and screen == 1 and subtab == 1:
            bg_color_combo = getattr(self.ui, 'comboBox_bg_color', None)
        if bg_color_combo:
            settings['bg_color'] = bg_color_combo.currentText()
        
        return settings
    
    def color_name_to_hex(self, color_name: str) -> str:
        """将中文颜色名称转换为十六进制颜色代码"""
        color_map = {
            "白色": "#FFFFFF",
            "黑色": "#000000", 
            "红色": "#FF0000",
            "绿色": "#00FF00",
            "蓝色": "#0000FF",
            "黄色": "#FFFF00",
            "青色": "#00FFFF",
            "洋红色": "#FF00FF",
            "橙色": "#FFA500",
            "紫色": "#800080",
            "灰色": "#808080",
            "深灰色": "#404040",
            "透明": "transparent"
        }
        return color_map.get(color_name, "#FFFFFF")
    
    # ========== 位置调整功能方法 ==========
    
    def adjust_subtitle_position(self, screen: int, subtab: int, direction: str):
        """调整字幕位置 - 支持语言特定调整"""
        if not self.subtitle_window_manager:
            return
        
        window = self.subtitle_window_manager.get_window(screen)
        if not window:
            return
        
        # 确定语言目标 (subtab 1=主语言, subtab 2=第二语言)
        language = 'primary' if subtab == 1 else 'secondary'
        
        # 使用窗口内的位置调整方法，传入语言参数
        if hasattr(window, 'adjust_subtitle_position'):
            window.adjust_subtitle_position(direction, self.position_step, language)
        else:
            # fallback: 移动整个窗口
            current_pos = window.pos()
            x, y = current_pos.x(), current_pos.y()
            
            if direction == 'up':
                y -= self.position_step
            elif direction == 'down':
                y += self.position_step
            elif direction == 'left':
                x -= self.position_step
            elif direction == 'right':
                x += self.position_step
            
            window.move(x, y)
        
        # 状态反馈
        lang_desc = "主语言" if subtab == 1 else "第二语言"
        direction_desc = {"up": "上", "down": "下", "left": "左", "right": "右"}[direction]
        
        self.update_status(f"屏幕{screen}({lang_desc}) 位置调整: 向{direction_desc}移动{self.position_step}像素")
        print(f"[PlayControl] 屏幕{screen}({lang_desc}) 位置调整: {direction}")
    
    def reset_subtitle_position(self, screen: int, subtab: int):
        """重置字幕位置到默认位置 - 支持语言特定重置"""
        if not self.subtitle_window_manager:
            return
        
        window = self.subtitle_window_manager.get_window(screen)
        if not window:
            return
        
        # 确定语言目标 (subtab 1=主语言, subtab 2=第二语言)
        language = 'primary' if subtab == 1 else 'secondary'
        
        # 使用窗口内的位置重置方法，传入语言参数
        if hasattr(window, 'reset_subtitle_position'):
            window.reset_subtitle_position(language)
        else:
            # fallback: 重置窗口位置
            if hasattr(self.subtitle_window_manager, 'default_positions'):
                default_pos = self.subtitle_window_manager.default_positions.get(screen, (100, 100))
                window.move(*default_pos)
            else:
                screen_geometry = window.screen().geometry()
                center_x = screen_geometry.width() // 2 - window.width() // 2
                center_y = screen_geometry.height() // 2 - window.height() // 2
                window.move(center_x, center_y)
        
        # 状态反馈
        lang_desc = "主语言" if subtab == 1 else "第二语言"
        
        self.update_status(f"屏幕{screen}({lang_desc}) 位置已重置到默认位置")
        print(f"[PlayControl] 屏幕{screen}({lang_desc}) 位置重置完成")
