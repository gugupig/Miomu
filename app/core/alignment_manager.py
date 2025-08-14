"""
对齐管理器 - 管理对齐系统的初始化、状态和音频流控制
"""
import logging
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, QTimer

from app.data.script_data import ScriptData
from app.core.audio.audio_hub import AudioHub
from app.core.stt.vosk_engine import VoskEngine
from app.core.stt.whisper_engine import WhisperEngine
from app.core.aligner.Aligner import Aligner
from app.core.director.director import Director
from app.core.g2p.g2p_manager import G2PManager


class ComponentState:
    """组件状态枚举"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    STANDBY = "standby"
    RUNNING = "running"
    ERROR = "error"


class AudioGate(QObject):
    """音频闸口 - 控制AudioHub到STTEngine的音频流"""
    
    def __init__(self, audio_hub: AudioHub, stt_engine, parent=None):
        super().__init__(parent)
        self.audio_hub = audio_hub
        self.stt_engine = stt_engine
        self.gate_open = False
        
        # 连接AudioHub的信号到我们的中介方法
        self.audio_hub.blockReady.connect(self._on_audio_block)
    
    def open_gate(self):
        """打开闸口，允许音频流传递"""
        self.gate_open = True
        logging.info("音频闸口已打开")
    
    def close_gate(self):
        """关闭闸口，阻止音频流传递"""
        self.gate_open = False
        logging.info("音频闸口已关闭")
    
    def _on_audio_block(self, channel_id: int, audio_block):
        """音频块中介处理 - 只有闸口打开时才传递给STT引擎"""
        if self.gate_open and self.stt_engine:
            # 传递给STT引擎
            if hasattr(self.stt_engine, 'feed'):
                self.stt_engine.feed(channel_id, audio_block)


class AlignmentManager(QObject):
    """对齐管理器 - 统一管理所有对齐相关组件"""
    
    # 信号定义
    component_standby = Signal(str)  # 组件名
    all_components_ready = Signal()  # 所有组件就绪
    component_error = Signal(str, str)  # 组件名, 错误信息
    status_changed = Signal(str)  # 状态消息
    alignment_started = Signal()  # 对齐开始
    alignment_stopped = Signal()  # 对齐停止
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 组件实例
        self.audio_hub: Optional[AudioHub] = None
        self.stt_engine: Optional[Any] = None  # VoskEngine 或 WhisperEngine
        self.aligner: Optional[Aligner] = None
        self.director: Optional[Director] = None
        self.g2p_manager: Optional[G2PManager] = None
        self.audio_gate: Optional[AudioGate] = None
        
        # 状态管理
        self.component_states: Dict[str, str] = {
            'AudioHub': ComponentState.IDLE,
            'STTEngine': ComponentState.IDLE,
            'Aligner': ComponentState.IDLE,
            'Director': ComponentState.IDLE
        }
        
        # 数据
        self.script_data: Optional[ScriptData] = None
        
        # 状态标志
        self.is_initialized = False
        self.is_running = False
        
        # 初始化超时定时器
        self.init_timeout_timer = QTimer()
        self.init_timeout_timer.setSingleShot(True)
        self.init_timeout_timer.timeout.connect(self._on_init_timeout)
    
    def initialize_components(self, script_data: ScriptData, stt_engine_type: str = "vosk"):
        """初始化所有组件"""
        if self.is_initialized:
            self.status_changed.emit("组件已经初始化，正在重新初始化...")
            self.cleanup_components()
        
        self.script_data = script_data
        self.status_changed.emit("开始初始化组件...")
        
        # 重置状态
        for component in self.component_states:
            self.component_states[component] = ComponentState.INITIALIZING
        
        # 启动初始化超时检查（30秒）
        self.init_timeout_timer.start(30000)
        
        try:
            self._initialize_g2p_manager()
            self._initialize_audio_hub()
            self._initialize_stt_engine(stt_engine_type)
            self._initialize_aligner()
            self._initialize_director()
            self._setup_audio_gate()
            
        except Exception as e:
            self.status_changed.emit(f"初始化失败: {str(e)}")
            self.component_error.emit("初始化", str(e))
            return False
        
        return True
    
    def _initialize_g2p_manager(self):
        """初始化G2P管理器"""
        try:
            self.g2p_manager = G2PManager()
            # 获取最佳可用引擎
            g2p_engine = self.g2p_manager.get_best_available_engine()
            if g2p_engine:
                self.status_changed.emit(f"G2P管理器初始化成功")
            else:
                raise Exception("无法获取可用的G2P引擎")
        except Exception as e:
            raise Exception(f"G2P管理器初始化失败: {str(e)}")
    
    def _initialize_audio_hub(self):
        """初始化AudioHub"""
        try:
            self.audio_hub = AudioHub(
                channels=1,
                samplerate=16000,
                frames_per_block=3200,
                silence_thresh=0.00,
                enable_denoise=True,
                denoise_method='noisereduce'
            )
            self.status_changed.emit("AudioHub初始化成功")
            self._mark_component_ready('AudioHub')
        except Exception as e:
            self.component_states['AudioHub'] = ComponentState.ERROR
            raise Exception(f"AudioHub初始化失败: {str(e)}")
    
    def _initialize_stt_engine(self, engine_type: str):
        """初始化STT引擎"""
        try:
            if engine_type.lower() == "vosk":
                # 使用Vosk引擎 - 法语模型
                self.stt_engine = VoskEngine(
                    model_dir="F:\\Miomu\\Miomu\\app\\models\\stt\\vosk\\vosk-model-fr-0.22",
                    lang="fr",
                    channel_id=0
                )
                self.status_changed.emit("VoskEngine (法语) 创建成功，正在启动...")
                
                # 连接模型就绪信号
                self.stt_engine.modelReady.connect(self._on_vosk_model_ready)
                
                # 启动STT引擎，模型将在后台线程中加载
                self.stt_engine.start()
                self.status_changed.emit("VoskEngine (法语) 启动成功，模型正在加载...")
                
            elif engine_type.lower() == "whisper":
                # 使用Whisper引擎
                self.stt_engine = WhisperEngine(
                    model_size="small",
                    device="cpu",
                    language="fr"
                )
                self.status_changed.emit("WhisperEngine (法语) 创建成功")
                
                # 启动Whisper引擎
                if hasattr(self.stt_engine, 'start'):
                    self.stt_engine.start()
                    self.status_changed.emit("WhisperEngine (法语) 启动成功")
                
                # Whisper引擎没有异步模型加载，直接标记为就绪
                self._mark_component_ready('STTEngine')
            else:
                raise Exception(f"不支持的STT引擎类型: {engine_type}")
            
        except Exception as e:
            self.component_states['STTEngine'] = ComponentState.ERROR
            raise Exception(f"STT引擎初始化失败: {str(e)}")
    
    def _on_vosk_model_ready(self):
        """VoskEngine模型加载完成的回调"""
        self.status_changed.emit("VoskEngine 模型加载完成，组件就绪")
        self._mark_component_ready('STTEngine')
    
    def _initialize_aligner(self):
        """初始化Aligner"""
        try:
            if not self.g2p_manager or not self.script_data:
                raise Exception("G2P管理器或脚本数据缺失")
            
            g2p_converter = self.g2p_manager.get_current_engine()
            self.aligner = Aligner(
                cues=self.script_data.cues,
                g2p_converter=g2p_converter
            )
            self.status_changed.emit("Aligner初始化成功")
            self._mark_component_ready('Aligner')
        except Exception as e:
            self.component_states['Aligner'] = ComponentState.ERROR
            raise Exception(f"Aligner初始化失败: {str(e)}")
    
    def _initialize_director(self):
        """初始化Director"""
        try:
            if not self.script_data or not self.script_data.cues:
                raise Exception("脚本数据缺失")
            
            # 从第一个cue开始
            initial_cue = self.script_data.cues[0] if self.script_data.cues else None
            self.director = Director(current_cue=initial_cue)
            self.director.set_cues_list(self.script_data.cues)
            
            # 连接Aligner和Director
            if self.aligner:
                self.director.set_aligner(self.aligner)
            
            self.status_changed.emit("Director初始化成功")
            self._mark_component_ready('Director')
        except Exception as e:
            self.component_states['Director'] = ComponentState.ERROR
            raise Exception(f"Director初始化失败: {str(e)}")
    
    def _setup_audio_gate(self):
        """设置音频闸口"""
        try:
            if not self.audio_hub or not self.stt_engine:
                raise Exception("AudioHub或STT引擎未初始化")
            
            self.audio_gate = AudioGate(self.audio_hub, self.stt_engine)
            # 默认关闭闸口
            self.audio_gate.close_gate()
            self.status_changed.emit("音频闸口设置完成")
        except Exception as e:
            raise Exception(f"音频闸口设置失败: {str(e)}")
    
    def _mark_component_ready(self, component_name: str):
        """标记组件为就绪状态"""
        if component_name in self.component_states:
            self.component_states[component_name] = ComponentState.STANDBY
            self.component_standby.emit(component_name)
            self.status_changed.emit(f"{component_name} 就绪")
            
            # 检查是否所有组件都就绪
            if all(state == ComponentState.STANDBY for state in self.component_states.values()):
                self._on_all_components_ready()
    
    def _on_all_components_ready(self):
        """所有组件就绪时的处理"""
        self.init_timeout_timer.stop()
        self.is_initialized = True
        self.status_changed.emit("所有组件已就绪，可以开始对齐")
        self.all_components_ready.emit()
    
    def _on_init_timeout(self):
        """初始化超时处理"""
        not_ready = [name for name, state in self.component_states.items() 
                    if state != ComponentState.STANDBY]
        error_msg = f"初始化超时，以下组件未就绪: {', '.join(not_ready)}"
        self.status_changed.emit(error_msg)
        self.component_error.emit("初始化", error_msg)
    
    def start_alignment(self):
        """开始对齐 - 打开音频闸口并启动组件"""
        if not self.is_initialized:
            self.status_changed.emit("错误: 组件未初始化")
            return False
        
        if self.is_running:
            self.status_changed.emit("对齐已在运行中")
            return True
        
        try:
            # STT引擎已经在初始化时启动，这里不需要再启动
            
            # 启动AudioHub
            if self.audio_hub:
                self.audio_hub.start()
            
            # 打开音频闸口
            if self.audio_gate:
                self.audio_gate.open_gate()
            
            # 设置组件连接
            self._setup_component_connections()
            
            self.is_running = True
            self.status_changed.emit("对齐系统运行中...")
            self.alignment_started.emit()
            
            # 更新组件状态
            for component in self.component_states:
                self.component_states[component] = ComponentState.RUNNING
            
            return True
            
        except Exception as e:
            self.status_changed.emit(f"启动对齐失败: {str(e)}")
            self.component_error.emit("启动", str(e))
            return False
    
    def stop_alignment(self):
        """停止对齐"""
        if not self.is_running:
            self.status_changed.emit("对齐未在运行")
            return True
        
        try:
            # 关闭音频闸口
            if self.audio_gate:
                self.audio_gate.close_gate()
            
            # 停止AudioHub
            if self.audio_hub:
                self.audio_hub.stop()
            
            # 不停止STT引擎，让它保持运行状态等待下次使用
            
            self.is_running = False
            self.status_changed.emit("对齐已停止")
            self.alignment_stopped.emit()
            
            # 更新组件状态回到STANDBY
            for component in self.component_states:
                self.component_states[component] = ComponentState.STANDBY
            
            return True
            
        except Exception as e:
            self.status_changed.emit(f"停止对齐失败: {str(e)}")
            self.component_error.emit("停止", str(e))
            return False
    
    def _setup_component_connections(self):
        """设置组件间的信号连接"""
        try:
            # STT引擎到Aligner的连接
            if hasattr(self.stt_engine, 'segmentReady') and self.aligner:
                # 这里需要根据实际的接口来连接
                # 临时使用简单的连接方式
                pass
            
            # Director的信号连接
            if self.director:
                # 连接Director的决策信号等
                pass
                
        except Exception as e:
            logging.warning(f"设置组件连接时出现警告: {e}")
    
    def cleanup_components(self):
        """清理组件"""
        if self.is_running:
            self.stop_alignment()
        
        # 清理各个组件
        if self.audio_hub:
            self.audio_hub.stop()
            self.audio_hub = None
        
        if self.stt_engine and hasattr(self.stt_engine, 'stop'):
            self.stt_engine.stop()
        self.stt_engine = None
        
        self.aligner = None
        self.director = None
        self.audio_gate = None
        
        # 重置状态
        for component in self.component_states:
            self.component_states[component] = ComponentState.IDLE
        
        self.is_initialized = False
        self.is_running = False
        
        self.status_changed.emit("组件已清理")
    
    def get_component_states(self) -> Dict[str, str]:
        """获取组件状态"""
        return self.component_states.copy()
    
    def is_component_ready(self, component_name: str) -> bool:
        """检查指定组件是否就绪"""
        return self.component_states.get(component_name) == ComponentState.STANDBY
    
    def are_all_components_ready(self) -> bool:
        """检查所有组件是否都就绪"""
        return all(state == ComponentState.STANDBY for state in self.component_states.values())
