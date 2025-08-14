"""
增强版字幕显示窗口

功能特性：
1. 无边框黑屏，默认800x600
2. 双击全屏切换
3. 支持双语显示（上下两个文本框）
4. 白线分隔符
5. 根据第二语言激活状态动态调整布局
"""

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, 
                              QFrame, QHBoxLayout, QMenu, QApplication, QMessageBox)
from PySide6.QtCore import Qt, Signal, Slot, QPoint
from PySide6.QtGui import QFont, QKeyEvent, QMouseEvent, QAction, QContextMenuEvent
from app.core.player import SubtitlePlayer
from app.models.models import Cue


class EnhancedSubtitleWindow(QMainWindow):
    """增强版字幕显示窗口"""
    
    # 信号
    windowClosed = Signal(int)  # 窗口关闭信号，发射窗口ID
    
    def __init__(self, window_id: int, player: SubtitlePlayer, parent=None):
        super().__init__(parent)

        self.window_id = window_id
        self.player = player
        self.is_fullscreen = False
        self.normal_size = (800, 600)
        # 语言选择（由控制面板设置）：primary为源语言，secondary为选中的翻译语言
        self.primary_lang_code = None
        self.secondary_lang_code = None
        # 隐藏角色名设置
        self.hide_character_name = False
        
        # 位置微调偏移量 (像素) - 分别为主语言和第二语言
        self.primary_position_offset_x = 0
        self.primary_position_offset_y = 0
        self.secondary_position_offset_x = 0
        self.secondary_position_offset_y = 0

        # 鼠标拖拽相关
        self.dragging = False
        self.drag_position = QPoint()

        # 初始化UI
        self.setup_ui()
        self.setup_connections()
        # 按当前播放器的第二语言状态设置可见性
        active = self.player.get_second_language_active(self.window_id)
        self.secondary_label.setVisible(active)
        self.separator.setVisible(active)
        self.update_layout()

        # 注册到播放器
        self.player.register_subtitle_window(self.window_id, self)

        print(f"[SubtitleWindow-{self.window_id}] Initialized")
    
    def setup_ui(self):
        """设置用户界面"""
        # 窗口基本设置
        self.setWindowTitle(f"字幕窗口 {self.window_id}")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.resize(*self.normal_size)
        
        # 设置黑色背景
        self.setStyleSheet("background-color: black;")
        
        # 创建中心组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(40, 40, 40, 40)
        self.main_layout.setSpacing(0)
        
        # 添加弹性空间（用于垂直居中）
        self.main_layout.addStretch()
        
        # 第一个文本框（主语言）
        self.primary_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        self.primary_label.setWordWrap(True)
        self.setup_label_style(self.primary_label, is_primary=True)
        self.main_layout.addWidget(self.primary_label)
        
        # 分隔线
        self.separator = QFrame()
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setStyleSheet("QFrame { color: white; background-color: white; max-height: 2px; }")
        self.separator.setVisible(False)  # 默认隐藏
        self.main_layout.addWidget(self.separator)
        
        # 第二个文本框（第二语言）
        self.secondary_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        self.secondary_label.setWordWrap(True)
        self.setup_label_style(self.secondary_label, is_primary=False)
        self.secondary_label.setVisible(False)  # 默认隐藏
        self.main_layout.addWidget(self.secondary_label)
        
        # 添加弹性空间（用于垂直居中）
        self.main_layout.addStretch()
        
        # 更新布局
        self.update_layout()
        
        # 设置右键菜单策略
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
    
    def setup_label_style(self, label: QLabel, is_primary: bool = True):
        """设置标签样式"""
        font_size = 48 if is_primary else 36
        font = QFont("Arial", font_size, QFont.Weight.Bold)
        label.setFont(font)
        
        color = "white" if is_primary else "#cccccc"
        label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                background-color: transparent;
                padding: 20px;
                border: none;
            }}
        """)
    
    def apply_font_settings(self, font_settings: dict, is_second_lang: bool = False):
        """应用字体设置到相应的标签"""
        # 选择要修改的标签
        target_label = self.secondary_label if is_second_lang else self.primary_label
        
        # 获取设置值，如果没有则使用默认值
        font_family = font_settings.get('font_family', 'Arial')
        font_size = int(font_settings.get('font_size', '48' if not is_second_lang else '36'))
        font_color = self.color_name_to_hex(font_settings.get('font_color', 'white' if not is_second_lang else '#cccccc'))
        bg_color = self.color_name_to_hex(font_settings.get('bg_color', 'transparent'))
        
        # 创建字体对象
        font = QFont(font_family, font_size, QFont.Weight.Bold)
        target_label.setFont(font)
        
        # 应用样式
        background_style = f"background-color: {bg_color};" if bg_color != "transparent" else "background-color: transparent;"
        
        target_label.setStyleSheet(f"""
            QLabel {{
                color: {font_color};
                {background_style}
                padding: 20px;
                border: none;
            }}
        """)
        
        print(f"[SubtitleWindow-{self.window_id}] Applied font settings to {'secondary' if is_second_lang else 'primary'} label: {font_settings}")
    
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
        return color_map.get(color_name, color_name)  # 如果不在映射中，直接返回原值
    
    def adjust_subtitle_position(self, direction: str, step: int = 10, language: str = 'both'):
        """
        调整字幕位置偏移
        direction: 'up', 'down', 'left', 'right', 'center'
        language: 'primary', 'secondary', 'both'
        """
        if direction == 'center':
            if language == 'primary' or language == 'both':
                self.primary_position_offset_x = 0
                self.primary_position_offset_y = 0
            if language == 'secondary' or language == 'both':
                self.secondary_position_offset_x = 0
                self.secondary_position_offset_y = 0
        else:
            if language == 'primary' or language == 'both':
                if direction == 'up':
                    self.primary_position_offset_y -= step
                elif direction == 'down':
                    self.primary_position_offset_y += step
                elif direction == 'left':
                    self.primary_position_offset_x -= step
                elif direction == 'right':
                    self.primary_position_offset_x += step
            
            if language == 'secondary' or language == 'both':
                if direction == 'up':
                    self.secondary_position_offset_y -= step
                elif direction == 'down':
                    self.secondary_position_offset_y += step
                elif direction == 'left':
                    self.secondary_position_offset_x -= step
                elif direction == 'right':
                    self.secondary_position_offset_x += step
        
        # 应用位置偏移
        self.apply_position_offset()
        
        # 更新状态信息
        if language == 'primary':
            print(f"[SubtitleWindow-{self.window_id}] 主语言位置调整: {direction} by {step}px, 偏移量: ({self.primary_position_offset_x}, {self.primary_position_offset_y})")
        elif language == 'secondary':
            print(f"[SubtitleWindow-{self.window_id}] 第二语言位置调整: {direction} by {step}px, 偏移量: ({self.secondary_position_offset_x}, {self.secondary_position_offset_y})")
        else:
            print(f"[SubtitleWindow-{self.window_id}] 位置调整: {direction} by {step}px, 主语言: ({self.primary_position_offset_x}, {self.primary_position_offset_y}), 第二语言: ({self.secondary_position_offset_x}, {self.secondary_position_offset_y})")
    
    def reset_subtitle_position(self, language: str = 'both'):
        """重置字幕位置偏移"""
        if language == 'primary' or language == 'both':
            self.primary_position_offset_x = 0
            self.primary_position_offset_y = 0
        if language == 'secondary' or language == 'both':
            self.secondary_position_offset_x = 0
            self.secondary_position_offset_y = 0
            
        self.apply_position_offset()
        
        if language == 'primary':
            print(f"[SubtitleWindow-{self.window_id}] 主语言位置重置")
        elif language == 'secondary':
            print(f"[SubtitleWindow-{self.window_id}] 第二语言位置重置")
        else:
            print(f"[SubtitleWindow-{self.window_id}] 所有语言位置重置")
    
    def apply_position_offset(self):
        """应用分别的位置偏移到各语言标签"""
        # 基础边距
        base_margin = 40
        
        # 应用主语言位置偏移
        primary_left = base_margin + self.primary_position_offset_x
        primary_top = base_margin + self.primary_position_offset_y
        primary_right = base_margin - self.primary_position_offset_x
        primary_bottom = base_margin - self.primary_position_offset_y
        
        # 确保边距不会变成负数
        primary_left = max(10, primary_left)
        primary_top = max(10, primary_top)
        primary_right = max(10, primary_right)
        primary_bottom = max(10, primary_bottom)
        
        self.primary_label.setContentsMargins(primary_left, primary_top, primary_right, primary_bottom)
        
        # 应用第二语言位置偏移
        secondary_left = base_margin + self.secondary_position_offset_x
        secondary_top = base_margin + self.secondary_position_offset_y
        secondary_right = base_margin - self.secondary_position_offset_x
        secondary_bottom = base_margin - self.secondary_position_offset_y
        
        # 确保边距不会变成负数
        secondary_left = max(10, secondary_left)
        secondary_top = max(10, secondary_top)
        secondary_right = max(10, secondary_right)
        secondary_bottom = max(10, secondary_bottom)
        
        self.secondary_label.setContentsMargins(secondary_left, secondary_top, secondary_right, secondary_bottom)
    
    def setup_connections(self):
        """设置信号连接"""
        # 连接播放器信号
        self.player.cueChanged.connect(self.display_cue)
        self.player.secondLanguageStateChanged.connect(self.on_second_language_state_changed)

    def set_languages(self, primary: str | None, secondary: str | None):
        """由控制面板设置窗口的语言选择"""
        self.primary_lang_code = (primary or '').strip() or None
        self.secondary_lang_code = (secondary or '').strip() or None
        # 刷新当前显示
        if self.player.current_cue:
            self.display_cue(self.player.current_cue)
    
    def set_hide_character_name(self, hide: bool):
        """设置是否隐藏角色名"""
        self.hide_character_name = hide
        # 刷新当前显示
        if self.player.current_cue:
            self.display_cue(self.player.current_cue)
        
    @Slot(Cue)
    def display_cue(self, cue: Cue):
        """显示字幕"""
        if not self.player.get_window_active(self.window_id):
            return

        # 计算主语言文本：优先取所选主语言的翻译，若无则回退到源文本 cue.line
        primary_text_line = ""
        if cue:
            if self.primary_lang_code:
                try:
                    if hasattr(cue, 'get_translation'):
                        primary_text_line = cue.get_translation(self.primary_lang_code) or ""
                    else:
                        primary_text_line = (cue.translation or {}).get(self.primary_lang_code, "")
                except Exception:
                    primary_text_line = (getattr(cue, 'translation', {}) or {}).get(self.primary_lang_code, "")
            # 回退到源文本
            if not primary_text_line:
                primary_text_line = cue.line or ""

        # 根据隐藏角色名设置构建显示文本
        if self.hide_character_name:
            primary_text = primary_text_line
        else:
            primary_text = f"{cue.character}:\n{primary_text_line}" if (cue and primary_text_line) else ""
        self.primary_label.setText(primary_text)

        # 显示第二语言（如果激活）
        if self.player.get_second_language_active(self.window_id):
            sec_text_line = ""
            lang_code = self.secondary_lang_code
            if lang_code:
                # 与主语言相同则直接使用主语言内容，避免不必要查询
                if self.primary_lang_code and lang_code.split('-')[0].lower() == self.primary_lang_code.split('-')[0].lower():
                    sec_text_line = primary_text_line
                else:
                    try:
                        if hasattr(cue, 'get_translation'):
                            sec_text_line = cue.get_translation(lang_code) or ""
                        else:
                            sec_text_line = (cue.translation or {}).get(lang_code, "")
                    except Exception:
                        sec_text_line = (getattr(cue, 'translation', {}) or {}).get(lang_code, "")
                    # 若仍无内容且所选第二语言可能是源语言，则回退到源文本
                    if not sec_text_line and self.primary_lang_code and lang_code.split('-')[0].lower() == (self.primary_lang_code.split('-')[0].lower()):
                        sec_text_line = primary_text_line

            # 根据隐藏角色名设置构建第二语言显示文本
            if self.hide_character_name:
                secondary_text = sec_text_line
            else:
                secondary_text = f"{cue.character}:\n{sec_text_line}" if (cue and sec_text_line) else ""
            self.secondary_label.setText(secondary_text)
        else:
            # 单语时清空第二语言显示
            self.secondary_label.setText("")
        
        print(f"[SubtitleWindow-{self.window_id}] Displayed cue: {cue.id}")
    
    @Slot(int, bool)
    def on_second_language_state_changed(self, window_id: int, active: bool):
        """响应第二语言状态变化"""
        if window_id != self.window_id:
            return
            
        self.secondary_label.setVisible(active)
        self.separator.setVisible(active)
        self.update_layout()
        # 状态改变后刷新当前cue的显示
        if self.player.current_cue:
            self.display_cue(self.player.current_cue)
        
        print(f"[SubtitleWindow-{self.window_id}] Second language {'activated' if active else 'deactivated'}")
    
    def update_layout(self):
        """更新布局"""
        # 根据第二语言状态调整间距
        if self.player.get_second_language_active(self.window_id):
            # 双语模式：调整间距
            self.main_layout.setSpacing(15)
        else:
            # 单语模式：无间距
            self.main_layout.setSpacing(0)
    
    def mouseDoubleClickEvent(self, event: QMouseEvent):
        """双击切换全屏"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle_fullscreen()
    
    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件 - 开始拖拽"""
        if event.button() == Qt.MouseButton.LeftButton and not self.is_fullscreen:
            self.dragging = True
            # 使用全局坐标计算偏移
            global_pos = event.globalPosition().toPoint()
            window_pos = self.pos()
            self.drag_position = global_pos - window_pos
            print(f"[SubtitleWindow-{self.window_id}] Started dragging from {self.drag_position}")
            event.accept()
        else:
            super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """鼠标移动事件 - 执行拖拽"""
        if self.dragging and not self.is_fullscreen and event.buttons() & Qt.MouseButton.LeftButton:
            # 计算新位置
            global_pos = event.globalPosition().toPoint()
            new_pos = global_pos - self.drag_position
            
            # 限制窗口不要移动到屏幕外
            screen = QApplication.primaryScreen().geometry()
            window_size = self.size()
            
            # 确保窗口至少有一部分在屏幕内
            min_x = -window_size.width() + 100  # 允许大部分窗口在屏幕外，但保留100px
            min_y = 0  # 不允许标题栏移动到屏幕上方
            max_x = screen.width() - 100
            max_y = screen.height() - 100
            
            new_pos.setX(max(min_x, min(new_pos.x(), max_x)))
            new_pos.setY(max(min_y, min(new_pos.y(), max_y)))
            
            self.move(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件 - 结束拖拽"""
        if event.button() == Qt.MouseButton.LeftButton:
            if self.dragging:
                self.dragging = False
                print(f"[SubtitleWindow-{self.window_id}] Finished dragging, new position: {self.pos()}")
                event.accept()
        super().mouseReleaseEvent(event)
    
    def show_context_menu(self, position: QPoint):
        """显示右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2c3e50;
                color: white;
                border: 1px solid #34495e;
                border-radius: 3px;
                padding: 4px;
            }
            QMenu::item {
                padding: 8px 16px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #3498db;
            }
            QMenu::item:disabled {
                color: #7f8c8d;
            }
            QMenu::separator {
                height: 1px;
                background-color: #34495e;
                margin: 4px 8px;
            }
        """)
        
        # 关闭窗口 - 添加图标和改进功能
        close_action = QAction("🗙 关闭窗口", self)
        close_action.triggered.connect(self.close_window_with_confirmation)
        close_action.setToolTip("关闭当前字幕窗口")
        menu.addAction(close_action)
        
        # 隐藏窗口（不关闭，只是隐藏）
        hide_action = QAction("👁 隐藏窗口", self)
        hide_action.triggered.connect(self.hide_window)
        hide_action.setToolTip("隐藏窗口但保持在后台")
        menu.addAction(hide_action)
        
        menu.addSeparator()
        
        # 全屏切换
        if self.is_fullscreen:
            fullscreen_action = QAction("🗗 退出全屏", self)
            fullscreen_action.setToolTip("退出全屏模式")
        else:
            fullscreen_action = QAction("🗖 进入全屏", self)
            fullscreen_action.setToolTip("进入全屏模式")
        fullscreen_action.triggered.connect(self.toggle_fullscreen)
        menu.addAction(fullscreen_action)
        
        # 重置位置
        reset_pos_action = QAction("📍 重置位置", self)
        reset_pos_action.triggered.connect(self.reset_window_position)
        reset_pos_action.setToolTip("重置窗口到默认位置")
        menu.addAction(reset_pos_action)
        
        menu.addSeparator()
        
        # 第二语言切换
        if self.player.get_second_language_active(self.window_id):
            lang_action = QAction("🌐 关闭第二语言", self)
            lang_action.triggered.connect(lambda: self.player.set_second_language_active(self.window_id, False))
        else:
            lang_action = QAction("🌐 开启第二语言", self)
            lang_action.triggered.connect(lambda: self.player.set_second_language_active(self.window_id, True))
        menu.addAction(lang_action)
        
        menu.addSeparator()
        
        # 窗口信息
        info_action = QAction(f"ℹ️ 窗口 {self.window_id} 信息", self)
        info_action.setEnabled(False)  # 只显示信息，不可点击
        menu.addAction(info_action)
        
        # 当前状态
        if self.player.get_second_language_active(self.window_id):
            lang_status = "双语模式"
        else:
            lang_status = "单语模式"
        
        status_action = QAction(f"📊 状态: {lang_status}", self)
        status_action.setEnabled(False)
        menu.addAction(status_action)
        
        # 位置信息
        pos_info = f"📐 位置: ({self.x()}, {self.y()})"
        pos_action = QAction(pos_info, self)
        pos_action.setEnabled(False)
        menu.addAction(pos_action)
        
        # 显示菜单
        global_pos = self.mapToGlobal(position)
        menu.exec(global_pos)
        
        print(f"[SubtitleWindow-{self.window_id}] Context menu shown at {position}")
    
    def close_window_with_confirmation(self):
        """带确认对话框的关闭窗口功能"""
        # 创建消息框并设置正常的系统样式
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("确认关闭")
        msg_box.setText(f"确定要关闭窗口 {self.window_id} 吗？")
        msg_box.setInformativeText("窗口关闭后需要重新激活才能显示。")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        # 重置样式为系统默认，避免继承黑色背景
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: palette(window);
                color: palette(text);
            }
            QMessageBox QLabel {
                color: palette(text);
                background-color: transparent;
            }
            QMessageBox QPushButton {
                background-color: palette(button);
                color: palette(button-text);
                border: 1px solid palette(mid);
                padding: 6px 12px;
                border-radius: 4px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover {
                background-color: palette(highlight);
                color: palette(highlighted-text);
            }
            QMessageBox QPushButton:pressed {
                background-color: palette(mid);
            }
        """)
        
        reply = msg_box.exec()
        
        if reply == QMessageBox.StandardButton.Yes:
            print(f"[SubtitleWindow-{self.window_id}] User confirmed window closure")
            self.close()
        else:
            print(f"[SubtitleWindow-{self.window_id}] User cancelled window closure")
    
    def reset_window_position(self):
        """重置窗口位置到默认位置"""
        # 获取默认位置
        default_positions = {
            1: (100, 100),
            2: (950, 100), 
            3: (525, 550)
        }
        
        if self.window_id in default_positions:
            default_pos = default_positions[self.window_id]
            self.move(*default_pos)
            print(f"[SubtitleWindow-{self.window_id}] Reset position to {default_pos}")
        
        # 如果是全屏状态，先退出全屏
        if self.is_fullscreen:
            self.toggle_fullscreen()
    
    def toggle_fullscreen(self):
        """切换全屏状态"""
        if self.is_fullscreen:
            # 退出全屏
            self.showNormal()
            self.resize(*self.normal_size)
            self.is_fullscreen = False
            print(f"[SubtitleWindow-{self.window_id}] Exited fullscreen - dragging enabled")
        else:
            # 进入全屏
            self.showFullScreen()
            self.is_fullscreen = True
            # 全屏时停止任何正在进行的拖拽
            self.dragging = False
            print(f"[SubtitleWindow-{self.window_id}] Entered fullscreen - dragging disabled")
    
    def keyPressEvent(self, event: QKeyEvent):
        """键盘事件处理"""
        key = event.key()
        
        if key == Qt.Key.Key_Escape:
            if self.is_fullscreen:
                self.toggle_fullscreen()
            else:
                self.close()
        elif key == Qt.Key.Key_F11:
            self.toggle_fullscreen()
        # 移除字幕切换功能 - 统一由 main_console 控制
        # elif key in (Qt.Key.Key_Down, Qt.Key.Key_Space, Qt.Key.Key_PageDown):
        #     self.player.next()
        # elif key in (Qt.Key.Key_Up, Qt.Key.Key_PageUp):
        #     self.player.prev()
        # elif key == Qt.Key.Key_Home:
        #     self.player.go(0)
        # elif key == Qt.Key.Key_End:
        #     self.player.go(len(self.player.cues) - 1)
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 注销窗口
        self.player.unregister_subtitle_window(self.window_id)
        
        # 发射关闭信号
        self.windowClosed.emit(self.window_id)
        
        print(f"[SubtitleWindow-{self.window_id}] Closed")
        super().closeEvent(event)
    
    def show_window(self):
        """显示窗口"""
        self.show()
        self.raise_()
        self.activateWindow()
        print(f"[SubtitleWindow-{self.window_id}] Shown")
    
    def hide_window(self):
        """隐藏窗口"""
        self.hide()
        print(f"[SubtitleWindow-{self.window_id}] Hidden")
    
    def set_window_position(self, x: int, y: int):
        """设置窗口位置"""
        self.move(x, y)
        print(f"[SubtitleWindow-{self.window_id}] Moved to ({x}, {y})")
    
    def get_window_info(self) -> dict:
        """获取窗口信息"""
        return {
            "window_id": self.window_id,
            "is_visible": self.isVisible(),
            "is_fullscreen": self.is_fullscreen,
            "is_dragging": self.dragging,
            "position": (self.x(), self.y()),
            "size": (self.width(), self.height()),
            "second_language_active": self.player.get_second_language_active(self.window_id)
        }
