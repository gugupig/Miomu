#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
G2P引擎选择界面测试程序
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QLabel, QComboBox, QPushButton, QTextEdit
from PySide6.QtCore import Qt

from app.core.g2p.g2p_manager import G2PManager, G2PEngineType


class G2PTestWindow(QMainWindow):
    """G2P测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.g2p_manager = G2PManager()
        self.init_ui()
        self.setup_g2p_ui()
        
    def init_ui(self):
        """初始化界面"""
        self.setWindowTitle("G2P引擎选择测试")
        self.setGeometry(200, 200, 600, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # G2P选择区域
        g2p_layout = QHBoxLayout()
        
        g2p_layout.addWidget(QLabel("G2P引擎:"))
        self.engine_combo = QComboBox()
        self.engine_combo.setMinimumWidth(150)
        self.engine_combo.currentTextChanged.connect(self.on_engine_changed)
        g2p_layout.addWidget(self.engine_combo)
        
        g2p_layout.addWidget(QLabel("语言:"))
        self.language_combo = QComboBox()
        self.language_combo.setMinimumWidth(100)
        self.language_combo.currentTextChanged.connect(self.on_language_changed)
        g2p_layout.addWidget(self.language_combo)
        
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        g2p_layout.addWidget(self.status_label)
        
        g2p_layout.addStretch()
        
        layout.addLayout(g2p_layout)
        
        # 测试区域
        test_layout = QHBoxLayout()
        
        self.test_input = QTextEdit()
        self.test_input.setMaximumHeight(100)
        self.test_input.setPlainText("Bonjour, comment allez-vous ?")
        
        self.convert_btn = QPushButton("转换")
        self.convert_btn.clicked.connect(self.convert_text)
        
        test_layout.addWidget(self.test_input, 2)
        test_layout.addWidget(self.convert_btn)
        
        layout.addLayout(test_layout)
        
        # 结果显示区域
        layout.addWidget(QLabel("转换结果:"))
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)
        
    def setup_g2p_ui(self):
        """设置G2P引擎选择UI"""
        try:
            # 获取可用引擎
            available_engines = self.g2p_manager.get_available_engines()
            
            # 填充引擎下拉框
            self.engine_combo.clear()
            for engine_type, config in available_engines:
                self.engine_combo.addItem(config["name"], engine_type)
            
            # 设置默认选择（Epitran优先）
            for i in range(self.engine_combo.count()):
                engine_type = self.engine_combo.itemData(i)
                if engine_type == G2PEngineType.EPITRAN:
                    self.engine_combo.setCurrentIndex(i)
                    break
            
            # 更新语言选择
            self.update_language_combo()
            
            # 更新状态
            self.update_status()
            
        except Exception as e:
            print(f"设置G2P UI失败: {e}")
            self.status_label.setText("错误")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            
    def update_language_combo(self):
        """更新语言选择下拉框"""
        try:
            current_engine_type = self.engine_combo.currentData()
            if current_engine_type is None:
                return
                
            # 获取当前引擎支持的语言
            languages = self.g2p_manager.get_engine_languages(current_engine_type)
            
            # 填充语言下拉框
            self.language_combo.clear()
            for lang_name, lang_code in languages.items():
                self.language_combo.addItem(lang_name, lang_code)
            
            # 设置默认语言（法语优先）
            for i in range(self.language_combo.count()):
                if "法语" in self.language_combo.itemText(i):
                    self.language_combo.setCurrentIndex(i)
                    break
                    
        except Exception as e:
            print(f"更新语言选择失败: {e}")
            
    def update_status(self):
        """更新状态显示"""
        try:
            engine_info = self.g2p_manager.get_current_engine_info()
            status_text = f"当前: {engine_info['name']} ({engine_info['language']})"
            self.status_label.setText(status_text)
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        except Exception as e:
            print(f"更新状态失败: {e}")
            self.status_label.setText("错误")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            
    def on_engine_changed(self, engine_name: str):
        """引擎选择变化"""
        try:
            engine_type = self.engine_combo.currentData()
            if engine_type is None:
                return
                
            print(f"切换到引擎: {engine_name}")
            
            # 更新语言选择
            self.update_language_combo()
            
            # 获取默认语言
            config = self.g2p_manager.engine_configs[engine_type]
            default_language = config["default_language"]
            
            # 切换引擎
            self.g2p_manager.switch_engine(engine_type, default_language)
            
            # 更新状态
            self.update_status()
            
        except Exception as e:
            print(f"切换引擎失败: {e}")
            self.status_label.setText("切换失败")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            
    def on_language_changed(self, language_name: str):
        """语言选择变化"""
        try:
            language_code = self.language_combo.currentData()
            engine_type = self.engine_combo.currentData()
            
            if language_code is None or engine_type is None:
                return
                
            print(f"切换到语言: {language_name} ({language_code})")
            
            # 切换语言
            self.g2p_manager.switch_engine(engine_type, language_code)
            
            # 更新状态
            self.update_status()
            
        except Exception as e:
            print(f"切换语言失败: {e}")
            self.status_label.setText("语言切换失败")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            
    def convert_text(self):
        """转换文本"""
        try:
            input_text = self.test_input.toPlainText().strip()
            if not input_text:
                return
                
            # 使用当前引擎转换
            engine = self.g2p_manager.get_current_engine()
            result = engine.convert(input_text)
            
            # 显示结果
            engine_info = self.g2p_manager.get_current_engine_info()
            output_text = f"引擎: {engine_info['name']} (语言: {engine_info['language']})\n"
            output_text += f"输入: {input_text}\n"
            output_text += f"输出: [{result}]\n"
            output_text += "-" * 50 + "\n"
            
            self.result_display.append(output_text)
            
        except Exception as e:
            error_text = f"转换失败: {e}\n" + "-" * 50 + "\n"
            self.result_display.append(error_text)


def main():
    app = QApplication(sys.argv)
    
    window = G2PTestWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
