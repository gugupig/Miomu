"""
引擎工作线程模块
"""
import logging
from typing import Optional
from PySide6.QtCore import QThread, Signal

from app.data.script_data import ScriptData
from app.core.player import SubtitlePlayer
from app.core.audio.audio_hub import AudioHub
from app.core.stt.whisper_engine import WhisperEngine
from app.core.stt.vosk_engine import VoskEngine
from app.core.aligner.Aligner import Aligner


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
                cues=script_data.cues,
                g2p_converter=g2p_converter,
                debug=True
            )
            
            # 注意：信号连接将在播放控制窗口中处理
            self.status_changed.emit("引擎设置完成")
            
        except Exception as e:
            error_msg = f"引擎设置失败: {str(e)}"
            logging.error(error_msg)
            self.error_occurred.emit(error_msg)
            raise
    
    def start_engines(self):
        """启动引擎"""
        try:
            if not self.aligner or not self.stt_engine or not self.audio_hub:
                raise Exception("引擎未正确设置")
            
            # 启动音频采集
            self.audio_hub.start()
            
            # 注意：具体的信号连接需要根据实际的STT和音频引擎接口来调整
            # 这里先保留基本的启动逻辑
            
            self.running = True
            self.status_changed.emit("引擎已启动")
            
        except Exception as e:
            error_msg = f"启动引擎失败: {str(e)}"
            logging.error(error_msg)
            self.error_occurred.emit(error_msg)
            raise
    
    def stop_engines(self):
        """停止引擎"""
        try:
            if self.audio_hub:
                self.audio_hub.stop()
            
            self.running = False
            self.status_changed.emit("引擎已停止")
            
        except Exception as e:
            error_msg = f"停止引擎失败: {str(e)}"
            logging.error(error_msg)
            self.error_occurred.emit(error_msg)
    
    def run(self):
        """线程主循环"""
        # 这个方法在QThread中会被自动调用
        # 对于我们的用例，我们不需要在这里做什么
        # 因为引擎的工作是事件驱动的
        self.exec()
