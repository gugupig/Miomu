import sys
from typing import Optional
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QFileDialog, QMessageBox
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QKeyEvent
from app.core.player import SubtitlePlayer
from app.models.models import Cue
from app.data.script_data import ScriptData


class SubtitleWindow(QMainWindow):
    def __init__(self, player: Optional[SubtitlePlayer] = None):
        super().__init__()
        self.player = player
        self.script_data: Optional[ScriptData] = None

        # 纯显示配置
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        self.showFullScreen()
        self.setCursor(Qt.CursorShape.BlankCursor)

        self.label = QLabel("", self, alignment=Qt.AlignmentFlag.AlignCenter, wordWrap=True)
        self.label.setFont(QFont("Arial", 64, QFont.Weight.Bold))
        self.label.setStyleSheet("color:#fff;background:#000;padding:40px;")
        self.setCentralWidget(self.label)

        # 如果没有传入播放器，显示提示信息
        if self.player is None:
            self.label.setText("字幕窗口\n\n按 O 键加载剧本\n按 ESC 键退出")
        else:
            # 连接信号——视图只关心"Cue 改变"这一件事
            self.setup_player_connections()
            self.player.go(0)  # 显示首句

    def setup_player_connections(self):
        """设置播放器连接"""
        if self.player:
            self.player.cueChanged.connect(self.display_cue)

    @Slot()
    def load_script(self):
        """加载剧本文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "选择剧本文件",
            "",
            "JSON 文件 (*.json);;所有文件 (*)"
        )
        
        if not file_path:
            return
            
        try:
            # 创建ScriptData实例并加载
            from app.core.g2p.g2p_manager import G2PManager
            
            g2p_manager = G2PManager()
            g2p_converter = g2p_manager.get_best_available_engine()
            
            self.script_data = ScriptData()
            success = self.script_data.load_from_file(file_path, g2p_converter)
            
            if success and self.script_data.cues:
                # 创建新的播放器
                self.player = SubtitlePlayer(self.script_data.cues)
                self.setup_player_connections()
                
                # 显示第一句
                self.player.go(0)
                
                # 更新窗口标题（虽然是无边框，但用于调试）
                self.setWindowTitle(f"字幕窗口 - {file_path}")
                
            else:
                self.show_error("剧本加载失败或文件为空")
                
        except Exception as e:
            self.show_error(f"加载剧本时出错: {str(e)}")

    def show_error(self, message: str):
        """显示错误消息"""
        QMessageBox.critical(self, "错误", message)

    # ---------- Slots ----------
    @Slot()
    def display_cue(self, cue: Cue):
        if cue.character:
            self.label.setText(f"{cue.character}:\n{cue.line}")
        else:
            self.label.setText(cue.line)

    # ---------- Key events (视图层只把交互转给 Player) ----------
    def keyPressEvent(self, ev: QKeyEvent):
        key = ev.key()
        
        # 如果没有播放器，只处理加载和退出
        if not self.player:
            if key == Qt.Key.Key_O:
                self.load_script()
            elif key == Qt.Key.Key_Escape:
                self.close()
            return
            
        # 有播放器时的完整控制
        if key in (Qt.Key.Key_Down, Qt.Key.Key_Space, Qt.Key.Key_PageDown):
            self.player.next()
        elif key in (Qt.Key.Key_Up, Qt.Key.Key_PageUp):
            self.player.prev()
        elif key == Qt.Key.Key_Home:
            self.player.go(0)
        elif key == Qt.Key.Key_End:
            self.player.go(len(self.player.cues) - 1)
        elif key == Qt.Key.Key_O:
            self.load_script()  # 重新加载剧本
        elif key == Qt.Key.Key_Escape:
            self.close()
