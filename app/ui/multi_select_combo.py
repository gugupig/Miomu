#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多选下拉菜单组件
"""

from typing import List, Set
from PySide6.QtWidgets import QComboBox, QListWidget, QListWidgetItem, QVBoxLayout, QWidget, QCheckBox
from PySide6.QtCore import Qt, Signal


class MultiSelectComboBox(QComboBox):
    """多选下拉菜单组件"""
    
    selectionChanged = Signal(list)  # 当选择发生变化时发出信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 创建列表组件用于显示多选项
        self.list_widget = QListWidget()
        self.list_widget.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 改为NoFocus避免焦点问题
        
        # 设置下拉菜单的样式
        self.setEditable(True)
        if self.lineEdit():
            self.lineEdit().setReadOnly(True)
            self.lineEdit().setPlaceholderText("选择语言...")
        
        # 存储选中的项目
        self._selected_items: Set[str] = set()
        self._items_data: List[tuple] = []  # (display_name, value) 对
        
        # 连接信号
        self.list_widget.itemChanged.connect(self._on_item_changed)
        
        # 安装事件过滤器到列表组件和应用程序
        self.list_widget.installEventFilter(self)
        
        # 为列表组件添加鼠标追踪
        self.list_widget.setMouseTracking(True)
        
        # 防止下拉菜单被点击时的默认行为
        self.setMaxVisibleItems(0)
        
        # 添加超时定时器，防止UI冻结
        from PySide6.QtCore import QTimer
        self._timeout_timer = QTimer()
        self._timeout_timer.setSingleShot(True)
        self._timeout_timer.timeout.connect(self.hidePopup)
        self._timeout_timer.setInterval(3000)  # 3秒超时，而不是10秒
        
        # 添加鼠标离开延迟定时器
        self._hide_timer = QTimer()
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hidePopup)
        self._hide_timer.setInterval(300)  # 300ms延迟隐藏
        
    def mousePressEvent(self, event):
        """重写鼠标点击事件 - 主要用于切换显示/隐藏"""
        try:
            from PySide6.QtCore import Qt
            if event.button() == Qt.MouseButton.LeftButton:
                # 点击时切换显示状态
                if self.list_widget.isVisible():
                    self.hidePopup()
                else:
                    self.showPopup()
                event.accept()
                return
        except Exception as e:
            print(f"鼠标点击事件处理出错: {e}")
        
        super().mousePressEvent(event)
        
    def enterEvent(self, event):
        """鼠标进入事件 - 显示下拉列表"""
        try:
            # 取消隐藏定时器
            self._hide_timer.stop()
            
            # 如果列表未显示，则显示它
            if not self.list_widget.isVisible():
                self.showPopup()
                
        except Exception as e:
            print(f"鼠标进入事件处理出错: {e}")
            
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开事件 - 延迟隐藏下拉列表"""
        try:
            # 启动延迟隐藏定时器
            self._hide_timer.start()
            
        except Exception as e:
            print(f"鼠标离开事件处理出错: {e}")
            
        super().leaveEvent(event)
        
    def add_item(self, text: str, userData=None):
        """添加一个可选项"""
        self._items_data.append((text, userData or text))
        self._update_list_widget()
        
    def add_items(self, texts: List[str]):
        """添加多个可选项"""
        for text in texts:
            self._items_data.append((text, text))
        self._update_list_widget()
        
    def clear(self):
        """清空所有选项"""
        self._items_data.clear()
        self._selected_items.clear()
        self.list_widget.clear()
        self._update_display_text()
        
    def _update_list_widget(self):
        """更新列表组件中的项目"""
        try:
            # 暂时断开信号连接，避免在更新时触发事件
            self.list_widget.itemChanged.disconnect()
            
            self.list_widget.clear()
            
            for display_name, value in self._items_data:
                try:
                    item = QListWidgetItem(display_name)
                    item.setData(Qt.ItemDataRole.UserRole, value)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    
                    # 设置选中状态
                    if value in self._selected_items:
                        item.setCheckState(Qt.CheckState.Checked)
                    else:
                        item.setCheckState(Qt.CheckState.Unchecked)
                        
                    self.list_widget.addItem(item)
                    
                except Exception as e:
                    print(f"添加列表项时出错: {e}")
                    continue
            
            # 重新连接信号
            self.list_widget.itemChanged.connect(self._on_item_changed)
            
        except Exception as e:
            print(f"更新列表组件时出错: {e}")
            # 确保信号重新连接
            try:
                self.list_widget.itemChanged.connect(self._on_item_changed)
            except:
                pass
            
    def _on_item_changed(self, item: QListWidgetItem):
        """处理项目选中状态变化"""
        value = item.data(Qt.ItemDataRole.UserRole)
        
        if item.checkState() == Qt.CheckState.Checked:
            self._selected_items.add(value)
        else:
            self._selected_items.discard(value)
            
        self._update_display_text()
        self.selectionChanged.emit(list(self._selected_items))
        
    def _update_display_text(self):
        """更新显示文本"""
        line_edit = self.lineEdit()
        if not line_edit:
            return
            
        if not self._selected_items:
            line_edit.setText("选择语言...")
            line_edit.setPlaceholderText("选择语言...")
        else:
            # 显示选中的语言名称
            selected_names = []
            for display_name, value in self._items_data:
                if value in self._selected_items:
                    selected_names.append(display_name)
            
            display_text = ", ".join(selected_names)
            if len(display_text) > 30:  # 如果文本太长，显示省略号
                display_text = display_text[:27] + "..."
            line_edit.setText(display_text)
            
    def showPopup(self):
        """显示下拉列表"""
        try:
            # 停止所有定时器
            self._timeout_timer.stop()
            self._hide_timer.stop()
            
            # 更新列表内容
            self._update_list_widget()
            
            # 如果没有项目，不显示弹出窗口
            if self.list_widget.count() == 0:
                return
            
            # 计算弹出位置
            pos = self.mapToGlobal(self.rect().bottomLeft())
            
            # 计算合适的尺寸，避免调用可能出错的sizeHintForRow
            item_height = 25  # 固定的项目高度
            list_height = min(200, item_height * min(8, self.list_widget.count()) + 10)
            list_width = max(self.width(), 200)
            
            # 设置几何属性并显示
            self.list_widget.setGeometry(pos.x(), pos.y(), list_width, list_height)
            self.list_widget.show()
            self.list_widget.raise_()
            
        except Exception as e:
            print(f"显示下拉列表时出错: {e}")
            # 确保在出错时隐藏列表
            self.list_widget.hide()
        
    def hidePopup(self):
        """隐藏下拉列表"""
        try:
            # 停止所有定时器
            self._timeout_timer.stop()
            self._hide_timer.stop()
            
            if self.list_widget.isVisible():
                self.list_widget.hide()
        except Exception as e:
            print(f"隐藏下拉列表时出错: {e}")
        
    def eventFilter(self, obj, event):
        """事件过滤器，处理列表组件的鼠标事件"""
        try:
            from PySide6.QtCore import QEvent
            
            if obj == self.list_widget:
                # 处理列表组件的鼠标进入事件
                if event.type() == QEvent.Type.Enter:
                    # 取消隐藏定时器
                    self._hide_timer.stop()
                    return True
                    
                # 处理列表组件的鼠标离开事件
                elif event.type() == QEvent.Type.Leave:
                    # 启动延迟隐藏定时器
                    self._hide_timer.start()
                    return True
                    
                # 处理窗口失去激活状态（保留原有逻辑）
                elif event.type() == QEvent.Type.WindowDeactivate:
                    self.hidePopup()
                    return True
                    
            return super().eventFilter(obj, event)
            
        except Exception as e:
            print(f"事件过滤器出错: {e}")
            return False
        
    def setSelectedValues(self, values: List[str]):
        """设置选中的值"""
        self._selected_items = set(values)
        self._update_list_widget()
        self._update_display_text()
        
    def getSelectedValues(self) -> List[str]:
        """获取选中的值"""
        return list(self._selected_items)
        
    def setPlaceholderText(self, text: str):
        """设置占位符文本"""
        line_edit = self.lineEdit()
        if line_edit:
            line_edit.setPlaceholderText(text)
            if not self._selected_items:
                line_edit.setText(text)
